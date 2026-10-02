from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import validateUser
from app.core.database import get_db
from app.models.user import User
from app.schemas.Chat import ChatRequest, ChatSessionRequest

# Repositories & Services
from app.repositories.ChatMessageRepository import ChatMessageRepository
from app.repositories.ChatSessionRepository import ChatSessionRepository
from app.services.ChatService import ChatService
from app.services.ToolsCreation import AgentDeps

# Domain services injected for tools
from app.services.DocumentService import DocumentService
from app.services.ExamService import ExamService
from app.services.GeneratedMaterialService import GeneratedMaterialService
from app.services.QuestionService import QuestionService
from app.services.StudyPlanService import StudyPlanService
from app.services.SyllabusService import SyllabusService
from app.services.TopicMatchService import TopicMatchService
from app.services.TopicPriorityService import TopicPriorityService

router = APIRouter(prefix="/chat", tags=["Exam Chat Orchestrator"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(
        session=db,
        message_repo=ChatMessageRepository(db),
        chat_session_repo=ChatSessionRepository(db),
    )


@router.post("/session", status_code=status.HTTP_201_CREATED)
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


@router.post("/message", status_code=status.HTTP_200_OK)
async def send_message(
    payload: ChatRequest,
    user: User = Depends(validateUser),
    chat_service: ChatService = Depends(get_chat_service),
    exam_service: ExamService = Depends(),
    doc_service: DocumentService = Depends(),
    syl_service: SyllabusService = Depends(),
    q_service: QuestionService = Depends(),
    plan_service: StudyPlanService = Depends(),
    gen_service: GeneratedMaterialService = Depends(),
    match_service: TopicMatchService = Depends(),
    priority_service: TopicPriorityService = Depends(),
):
    deps = AgentDeps(
        user=user,
        exam_service=exam_service,
        document_service=doc_service,
        syllabus_service=syl_service,
        question_service=q_service,
        study_plan_service=plan_service,
        generated_material_service=gen_service,
        topic_match_service=match_service,
        topic_priority_service=priority_service,
    )

    reply = await chat_service.chat_process(
        user=user,
        session_title=payload.session_title,
        agent_deps=deps,
        prompt=payload.message,
    )

    return {"response": reply}