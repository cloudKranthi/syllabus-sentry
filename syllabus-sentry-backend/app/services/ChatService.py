from dataclasses import dataclass
from uuid import UUID
from fastapi import HTTPException, status
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ChatMessage import ChatMessage, Role
from app.models.ChatSession import ChatSession
from app.models.user import User
from app.repositories.UserRepository import UserRepository
from app.repositories.ChatMessageRepository import ChatMessageRepository
from app.repositories.ChatSessionRepository import ChatSessionRepository
from app.services.ToolsCreation import AgentDeps, exam_agent


@dataclass
class ChatService:
    session: AsyncSession
    message_repo: ChatMessageRepository
    chat_session_repo: ChatSessionRepository
    user_repo:UserRepository

    SYSTEM_INSTRUCTION: str = (
        "You are an expert academic exam prep assistant. You help students plan their study hours, "
        "analyze previous year question trends, prioritize syllabus topics, and manage study materials. "
        "Always rely on the tools provided to access exam details and database records. "
        "Never guess or hallucinate stats."
    )
    async def find_session(self,user:User,session_title:str)->ChatSession|None:
        s=await self.chat_session_repo.get_by_userid_title(user.id,session_title)
        return s
    async def update_session(self,user:User,session_title:str,eid:UUID)->ChatSession:
        s=await self.chat_session_repo.update_exam(user.id,session_title,eid)
        return s
    async def create_session(
        self, user: User, exam_id: UUID | None, title: str
    ) -> ChatSession:
        # 1. Instantiate ChatSession and persist via repository
        new_session = ChatSession(
            user_id=user.id,
            exam_id=exam_id,
            title=title,
        )
        saved_session = await self.chat_session_repo.create(new_session)
        await self.session.commit()

        # 2. Persist the initial system prompt (ChatMessage has no user_id column)
        system_msg = ChatMessage(
            session_id=saved_session.id,
            role=Role.SYSTEM,
            content=self.SYSTEM_INSTRUCTION,
            tool_calls=None,
            tool_call_id=None,
        )
        await self.message_repo.create(system_msg)
        await self.message_repo.session.commit()

        return saved_session

    async def chat_process(
        self, user: User, sessionTitle: str, agentDeps: AgentDeps, prompt: str
    ) -> str:
        # 1. Find session by user and title
        session = await self.chat_session_repo.get_by_userid_title(
            user.id, sessionTitle
        )
        if not session:
            s=ChatSession(title=sessionTitle,user_id=user.id)
            session=await self.chat_session_repo.create(s)
            await self.session.commit()

        # 2. Pull system messages and historical conversation turns
        system_msgs = await self.message_repo.getSystemMessages(session.id)
        messages = await self.message_repo.extractMessages(session.id)

        # 3. Build PydanticAI message history (System prompt first)
        message_history: list[ModelMessage] = []
        for m in system_msgs:
            if m.content:
                message_history.append(
                    ModelRequest(parts=[SystemPromptPart(content=m.content)])
                )

        for msg in messages:
            if not msg.content:
                continue
            if msg.role == Role.USER:
                message_history.append(
                    ModelRequest(parts=[UserPromptPart(content=msg.content)])
                )
            elif msg.role == Role.ASSISTANT:
                message_history.append(
                    ModelResponse(parts=[TextPart(content=msg.content)])
                )

        # 4. Save incoming user prompt to DB
        user_message = ChatMessage(
            session_id=session.id,
            role=Role.USER,
            content=prompt,
            tool_calls=None,
            tool_call_id=None,
        )
        await self.message_repo.create(user_message)
        await self.message_repo.session.commit()

        # 5. Run agent turn (executes tools automatically via agentDeps)
        result = await exam_agent.run(
            prompt,
            message_history=message_history,
            deps=agentDeps,
        )
        reply_text = str(result.output)

        # 6. Save assistant response to DB
        assistant_message = ChatMessage(
            session_id=session.id,
            role=Role.ASSISTANT,
            content=reply_text,
            tool_calls=None,
            tool_call_id=None,
        )
        await self.message_repo.create(assistant_message)
        await self.message_repo.session.commit()

        return reply_text
            