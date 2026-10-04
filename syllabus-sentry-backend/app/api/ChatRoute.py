from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import validateUser
from app.services.AutoContainer import AutoContainer
from app.core.database import get_db
from app.models.user import User

from app.repositories.ChatMessageRepository import ChatMessageRepository
from app.repositories.ChatSessionRepository import ChatSessionRepository
from app.repositories.UserRepository import UserRepository

from app.schemas.Chat import ChatRequest, ChatSessionRequest

from app.services.ChatService import ChatService
from app.services.ExamService import ExamService
from app.services.DocumentService import DocumentService
from app.services.GeneratedMaterialService import GeneratedMaterialService
from app.services.QuestionService import QuestionService
from app.services.StudyPlanService import StudyPlanService
from app.services.SyllabusService import SyllabusService
from app.services.ToolsCreation import AgentDeps
from app.services.TopicMatchService import TopicMatchService
from app.services.TopicPriorityService import TopicPriorityService


chatrouter = APIRouter(
    prefix="/chat",
    tags=["Exam Chat Orchestrator"],
)


def get_chat_service(
    db: AsyncSession = Depends(get_db),
) -> ChatService:

    return ChatService(
        session=db,
        message_repo=ChatMessageRepository(db),
        chat_session_repo=ChatSessionRepository(db),
        user_repo=UserRepository(db),
    )


def get_agent_deps(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(validateUser),
) -> AgentDeps:

    container = AutoContainer(db)

    return AgentDeps(
        user=user,

        exam_service=container.get(ExamService),

        document_service=container.get(DocumentService),

        syllabus_service=container.get(SyllabusService),

        question_service=container.get(QuestionService),

        study_plan_service=container.get(StudyPlanService),

        generated_material_service=container.get(
            GeneratedMaterialService
        ),

        topic_match_service=container.get(
            TopicMatchService
        ),

        topic_priority_service=container.get(
            TopicPriorityService
        ),
        chat_message_repo=ChatMessageRepository(db),
        chat_session_repo=ChatSessionRepository(db),
    )


@chatrouter.post(
    "/session",
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    payload: ChatSessionRequest,
    user: User = Depends(validateUser),
    chat_service: ChatService = Depends(get_chat_service),
):
    session = await chat_service.create_session(
        user=user,
        exam_id=payload.exam_id,
        title=payload.title,
    )

    return {
        "status": "success",
        "message": "Session Created Successfully",
        "session_id": session.id,
        "title": session.title,
    }


@chatrouter.post(
    "/message",
    status_code=status.HTTP_200_OK,
)
async def send_message(
    payload: ChatRequest,
    user: User = Depends(validateUser),
    chat_service: ChatService = Depends(get_chat_service),
    agent_deps: AgentDeps = Depends(get_agent_deps),
):
    reply = await chat_service.chat_process(
        user=user,
        sessionTitle=payload.session_title,
        agentDeps=agent_deps,
        prompt=payload.message,
    )

    return {
        "response": reply
    }