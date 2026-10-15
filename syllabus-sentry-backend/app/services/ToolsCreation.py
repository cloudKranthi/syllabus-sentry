from __future__ import annotations

import os
import json
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from typing import Any, Optional
from uuid import UUID
import uuid
from fastapi import UploadFile
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel

from app.core.config import settings
from app.models.document import DocumentProcessingStatus, DocumentType
from app.models.DocumentEmbedding import DocumentEmbedding
from app.models.GeneratedMaterial import MaterialType
from app.models.QuestionTopicMatch import MatchMethod
from app.models.StudyPlanItem import PlanItemPriority, StudyItemStatus
from app.models.Topic import TopicPriority
from app.models.user import User
from app.repositories.ChatMessageRepository import ChatMessageRepository
from app.repositories.ChatSessionRepository import ChatSessionRepository
# Services
from app.services.DocuemntIngestionService import DocumentIngestionService
from app.services.DocumentService import DocumentService
from app.services.ExamService import ExamService
from app.services.GeneratedMaterialService import GeneratedMaterialService
from app.services.QuestionService import QuestionService
from app.services.StudyPlanService import StudyPlanService
from app.services.SyllabusService import SyllabusService
from app.services.TaskService import TaskService
from app.services.TopicMatchService import TopicMatchService
from app.services.TopicPriorityService import TopicPriorityService

# Ensure client discovery variables are populated
os.environ["OPENAI_BASE_URL"] = getattr(
    settings, "OPENAI_BASE_URL", "http://localhost:11434/v1"
)
os.environ["OPENAI_API_KEY"] = getattr(settings, "OPENAI_API_KEY", "ollama")

# =====================================================================
# AGENT DEPENDENCIES & INITIALIZATION
# =====================================================================


@dataclass
class AgentDeps:
    user: User
    exam_service: ExamService
    document_service: DocumentService
    syllabus_service: SyllabusService
    question_service: QuestionService
    study_plan_service: StudyPlanService
    generated_material_service: GeneratedMaterialService
    topic_match_service: TopicMatchService
    topic_priority_service: TopicPriorityService
    chat_message_repo: ChatMessageRepository
    chat_session_repo: ChatSessionRepository
    document_ingestion_service: DocumentIngestionService
    uploaded_file: Optional[UploadFile] = None


ollama_client = AsyncOpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)

model = OpenAIChatModel("gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are an academic exam preparation assistant.\n"
    "IMPORTANT EXECUTION RULES:\n"
    "- When the user asks to perform an action, you MUST call the corresponding tool directly.\n"
    "- NEVER output markdown code blocks (e.g. ```python ... ```).\n"
    "- NEVER output raw JSON schemas or function definition text.\n"
    "- Call the required tool silently and confirm the result in concise plain text."
)

# =====================================================================
# 1. EXAM TOOLS
# =====================================================================


async def get_exam_name(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve current status, total available usable study hours, exam date, and preparation mode (NORMAL or SURVIVAL) for an existing exam.
    USE THIS TOOL WHEN: The user asks what mode they are in, how many hours they have left, or requests current exam details.
    """
    exam = await ctx.deps.exam_service.get_exam_by_name(ctx.deps.user, examname)
    return {
        "status": "success",
        "exam_id": str(exam.id),
        "exam_name": exam.name,
        "availableStudyHours": exam.availableStudyHours,
        "mode": exam.mode,
        "examDateTime": (
            exam.examDateTime.isoformat() if exam.examDateTime else None
        ),
    }


async def get_active_plan(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve metadata and version ID of the currently active study plan for an exam.
    USE THIS TOOL WHEN: Checking if a study plan already exists before creating a new baseline.
    """
    try:
        plan = await ctx.deps.study_plan_service.get_active_plan(
            ctx.deps.user, examname
        )
        if not plan:
            return {
                "status": "not_found",
                "message": f"No active study plan found for exam '{examname}'.",
            }
        return {
            "status": "success",
            "plan_id": str(plan.id),
            "version": getattr(plan, "version", "1.0"),
        }
    except Exception as e:
        return {
            "status": "not_found",
            "message": f"No study plan found for {examname}. Error: {str(e)}",
        }


async def calculate_hours(
    ctx: RunContext[AgentDeps], examname: str, daily_study_hours: int
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Recalculate and update remaining usable study hours and exam mode (NORMAL vs SURVIVAL) for an existing exam in the database.
    USE THIS TOOL ONLY WHEN: The user explicitly provides a new or modified daily study commitment.
    """
    exam = await ctx.deps.exam_service.recalculate_hours(
        ctx.deps.user, examname, daily_study_hours
    )
    return {
        "status": "success",
        "exam_name": exam.name,
        "availableStudyHours": exam.availableStudyHours,
        "mode": exam.mode,
    }


async def create_exam(
    ctx: RunContext[AgentDeps],
    examname: str,
    session_title: str,
    daily_study_hours: int,
    exam_datetime: datetime,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Create a new exam profile in the database and link it to the current chat session.
    USE THIS TOOL WHEN: The student specifies an exam name, exam date/time, and daily study hours to schedule a new exam.
    """
    existing = await ctx.deps.exam_repo.get_by_name(ctx.deps.user.id, examname)
    if existing:
        return existing
    if exam_datetime is None:
       exam_datetime = datetime.now(timezone.utc) + timedelta(days=30)
    elif exam_datetime.tzinfo is None:
        exam_datetime = exam_datetime.replace(tzinfo=timezone.utc)
    exam = await ctx.deps.exam_service.create_exam(
        user=ctx.deps.user,
        name=examname,
        examdate=exam_datetime,
        dailystudyhours=daily_study_hours,
    )
    session = await ctx.deps.chat_session_repo.get_by_userid_title(
        ctx.deps.user.id, session_title
    )
    if session:
        await ctx.deps.chat_session_repo.update_exam(
            ctx.deps.user.id, session_title, exam.id
        )
    return {
        "status": "success",
        "exam_id": str(exam.id),
        "exam_name": exam.name,
        "mode": exam.mode,
        "availableStudyHours": exam.availableStudyHours,
    }


# =====================================================================
# 2. SYLLABUS & TOPIC TOOLS
# =====================================================================


async def create_syllabus(
    ctx: RunContext[AgentDeps], examname: str, documenttitle: str, filename: str
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Initialize the root syllabus record for an exam based on an uploaded document file.
    """
    syllabus = await ctx.deps.syllabus_service.create_syllabus_structure(
        ctx.deps.user, examname, documenttitle, filename
    )
    return {
        "status": "success",
        "syllabus_id": str(syllabus.id),
        "title": getattr(syllabus, "title", documenttitle),
    }


async def create_syllabus_units(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabustitle: str,
    unitname: str,
    description: str,
    unitNumber: int,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Add a module or unit section to an existing syllabus.
    """
    unit = await ctx.deps.syllabus_service.create_syllabus_unit(
        examname,
        ctx.deps.user,
        syllabustitle,
        unitname,
        unitNumber,
        description,
    )
    return {
        "status": "success",
        "unit_id": str(unit.id),
        "unit_name": unitname,
        "unit_number": unitNumber,
    }


async def create_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabusTitle: str,
    Topicname: str,
    description: str,
    priority: TopicPriority,
    unitNumber: int,
    estimatedHours: int,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Creates and persists a new academic topic under a specific syllabus unit.
    """
    t = await ctx.deps.syllabus_service.createTopic(
        ctx.deps.user,
        examname,
        syllabusTitle,
        Topicname,
        description,
        priority,
        unitNumber,
        estimatedHours,
    )
    return {"status": "success", "topic_id": str(t.id),"topic_name": t.name,
        "priority": str(t.priority),
        "estimated_hours": t.estimatedHours,}


async def get_syllabus_by_name(
    ctx: RunContext[AgentDeps], examname: str, syllabusTitle: str
) -> dict[str, Any]:
    """[QUERY / READ]
    Fetches the syllabus container details and structure for an exam.
    """
    ns = await ctx.deps.syllabus_service.get_syllabus_by_name(
        ctx.deps.user, examname, syllabusTitle
    )
    units_data=[]
    if hasattr(ns, "units") and ns.units:
        for u in ns.units:
            units_data.append(
                {
                    "unit_id": str(u.id),
                    "unit_number": getattr(u, "unitNumber", None),
                    "name": getattr(u, "name", ""),
                    "description": getattr(u, "description", ""),
                }
            )
    return {
        "status": "success",
        "syllabus_id": str(ns.id),
        "title": getattr(ns, "title", syllabusTitle),
        "units": units_data,
    }


async def get_by_topic_name(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabusname: str,
    topictitle: str,
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Fetch detailed topic information, current priority level, and metadata for a specific topic within a syllabus.
    """
    topic = await ctx.deps.syllabus_service.getTopicByName(
        ctx.deps.user, examname, syllabusname, topictitle
    )
    return {
        "status": "success",
        "topic_id": str(topic.id),
        "name": getattr(topic, "name", topictitle),
        "priority": str(getattr(topic, "priority", "")),
    }


async def update_priority_of_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topicName: str,
    pr: TopicPriority,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Manually override the baseline priority level (HIGH, MEDIUM, or LOW) of a syllabus topic.
    """
    topic = await ctx.deps.syllabus_service.updateTopicBasePriority(
        ctx.deps.user, examname, syllabus_title, topicName, pr
    )
    return {
        "status": "success",
        "topic_id": str(topic.id),
        "updated_priority": str(pr),
    }


# =====================================================================
# 3. DOCUMENT & EMBEDDING TOOLS
# =====================================================================


async def record_matches(
    ctx: RunContext[AgentDeps],
    examname: str,
    sourceType: DocumentType,
    unitNumber: Optional[int] | None = None,
) -> dict[str, Any]:
    """Ingest and vectorize the attached PDF file into the database for a given exam.[PRIMARY FILE INGESTION TOOL]
    USE THIS TOOL FIRST: Whenever the user has uploaded/attached a PDF (whether Syllabus or PYQ)."""
    file = ctx.deps.uploaded_file
    if not file:
        return {
            "status": "failed",
            "message": "No file was attached to this request to process.",
        }
    await file.seek(0)
    file_bytes = await file.read()
    await ctx.deps.document_ingestion_service.record(
        ctx.deps.user, examname, sourceType, file_bytes, unitNumber
    )
    return {"status": "success","message": f"Successfully ingested and vectorized {sourceType.value} for {examname}.",}


async def search_with_embeddings(
    ctx: RunContext[AgentDeps],
    examname: str,
    question: str,
    unitNumber: int = None,
    limit: int = 5,
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Semantically search uploaded syllabus documents and course materials for relevant context.
    """
    embeddings = await ctx.deps.document_ingestion_service.search(
        ctx.deps.user, examname, question, limit, unitNumber
    )
    if not embeddings:
        return {
            "status": "empty",
            "message": "No relevant document excerpts found in uploaded materials.",
            "chunks": [],
        }
    return {
        "status": "success",
        "chunks": [
            {
                "content": item.content,
                "unit_number": item.unit_number,
                "chunk_index": item.chunk_index,
                "source_type": str(item.source_type),
            }
            for item in embeddings
        ],
    }


async def register_document(
    ctx: RunContext[AgentDeps],
    examname: str,
    filename: str,
    storagePath: str,
    st: DocumentProcessingStatus,
    type: DocumentType,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Record an uploaded file into document tracking with initial status.
    """
    document = await ctx.deps.document_service.registerDocument(
        ctx.deps.user, filename, examname, storagePath, st, type
    )
    return {
        "status": "success",
        "document_id": str(document.id),
        "filename": document.filename,
        "processing_status": str(document.status),
    }


async def update_status(
    ctx: RunContext[AgentDeps],
    document_id: UUID,
    status: DocumentProcessingStatus,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Transition document processing status through lifecycle.
    """
    document = await ctx.deps.document_service.transition_document_status(
        document_id, status
    )
    return {
        "status": "success",
        "document_id": str(document.id),
        "new_status": str(document.status),
    }


async def get_document_by_name(
    ctx: RunContext[AgentDeps], exam_name: str, filename: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Locate a single document associated with an exam using its exact filename.
    """
    doc = await ctx.deps.document_service.get_document_by_name(
        ctx.deps.user, exam_name, filename
    )
    return {
        "status": "success",
        "document_id": str(doc.id),
        "filename": doc.filename,
        "type": str(doc.type),
        "status": str(doc.status),
    }


async def get_related_exam_type_documents(
    ctx: RunContext[AgentDeps], exam_name: str, type: DocumentType
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    List all documents attached to an exam filtered by type (e.g. SYLLABUS or PYQ).
    """
    documents = await ctx.deps.document_service.get_exam_type_documents(
        ctx.deps.user, exam_name, type
    )
    return {
        "status": "success",
        "documents": [
            {"id": str(d.id), "filename": d.filename, "type": str(d.type)}
            for d in documents
        ],
    }


async def get_exam_related_documents(
    ctx: RunContext[AgentDeps], exam_name: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    List all uploaded files registered under an exam.
    """
    documents = await ctx.deps.document_service.get_exam_all_documents(
        ctx.deps.user, exam_name
    )
    return {
        "status": "success",
        "documents": [
            {"id": str(d.id), "filename": d.filename, "type": str(d.type)}
            for d in documents
        ],
    }


# =====================================================================
# 4. QUESTION TOOLS
# =====================================================================
async def save_new_extracted_questions(
    ctx: RunContext[AgentDeps],
    examname: str,
    questions_data: Any,
    document_id: Optional[str|UUID]=None) -> dict[str, Any]:
    """[DATABASE STORAGE ONLY]
    Persist a batch of structured PYQ questions into the database.
    DO NOT CALL THIS TOOL FOR ATTACHED PDF FILES.
    """
    if isinstance(questions_data,str):
        try:
            questions_data2=json.loads(questions_data)
        except Exception:
            return {
                "status": "failed",
                "message": "Invalid JSON string format for questions_data.",
            }
    doc_id:UUID
    if isinstance(document_id,UUID):
        doc_id=document_id
    elif isinstance(document_id,str):
        try:
           doc_id=UUID(document_id)
        except Exception:
            doc_id=uuid.uuid4()
    else:
        doc_id=uuid.uuid4()
    saved_questions = await ctx.deps.question_service.save_extracted_questions(
        ctx.deps.user, examname, doc_id, questions_data2
    )
    return {
        "status": "success",
        "saved_count": len(saved_questions),
        "question_ids": [str(q.id) for q in saved_questions],
    }


async def get_questions_by_exam(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve all historical previous-year exam questions logged in the system for an exam.
    """
    questions = await ctx.deps.question_service.get_questions_by_exam(
        ctx.deps.user, examname
    )
    return {
        "status": "success",
        "questions": [
            {
                "id": str(q.id),
                "number": q.questionNumber,
                "text": q.questionText,
                "marks": q.marks,
                "year": q.year,
            }
            for q in questions
        ],
    }


async def get_unmatched_questions(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Fetch all PYQs for an exam that have not yet been categorized or mapped to a syllabus topic.
    """
    questions = await ctx.deps.question_service.get_unmatched_questions(
        ctx.deps.user, examname
    )
    return {
        "status": "success",
        "unmatched_questions": [
            {"id": str(q.id), "number": q.questionNumber, "text": q.questionText}
            for q in questions
        ],
    }


async def get_question_by_number(
    ctx: RunContext[AgentDeps], examname: str, question_number: int
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve the text, mark allotment, and year for a single specific question number.
    """
    question = await ctx.deps.question_service.get_question(
        ctx.deps.user, examname, question_number
    )
    return {
        "status": "success",
        "id": str(question.id),
        "number": question.questionNumber,
        "text": question.questionText,
        "marks": question.marks,
        "year": question.year,
    }


# =====================================================================
# 5. STUDY PLAN TOOLS
# =====================================================================


async def create_baseline_plan(
    ctx: RunContext[AgentDeps], examname: str, version: str
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Initialize a new baseline study plan schedule container for an exam.
    """
    plan = await ctx.deps.study_plan_service.generate_baseline_plan(
        ctx.deps.user, examname, version
    )
    return {
        "status": "success",
        "plan_id": str(plan.id),
        "version": version,
    }


async def generate_study_plan_item(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topic_title: str,
    plannedHours: float,
    sequence_order: int,
    priority: PlanItemPriority,
    status: StudyItemStatus,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Add a scheduled topic item into the active study plan with allotted hours and priority.
    """
    item = await ctx.deps.study_plan_service.generate_plan_item(
        ctx.deps.user,
        examname,
        syllabus_title,
        topic_title,
        plannedHours,
        sequence_order,
        priority,
        status,
    )
    return {
        "status": "success",
        "item_id": str(item.id),
        "topic": topic_title,
        "planned_hours": plannedHours,
    }


async def update_plan_item_status(
    ctx: RunContext[AgentDeps], examname: str, status: StudyItemStatus
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Update execution state (NOT_STARTED, IN_PROGRESS, COMPLETED) of a study plan entry.
    """
    item = await ctx.deps.study_plan_service.update_plan_item_status(
        ctx.deps.user, examname, status
    )
    return {
        "status": "success",
        "item_id": str(item.id),
        "status": str(status),
    }


async def update_plan_hours(
    ctx: RunContext[AgentDeps],
    examname: str,
    adjusted_daily_hours: float | None = None,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Recalculate study hour distributions across all plan items following a schedule shift.
    """
    plan = await ctx.deps.study_plan_service.update_plan(
        ctx.deps.user, examname, adjusted_daily_hours
    )
    return {"status": "success", "plan_id": str(plan.id)}


# =====================================================================
# 6. TOPIC MATCH, PRIORITY & MATERIAL TOOLS
# =====================================================================


async def record_match(
    ctx: RunContext[AgentDeps],
    examname: str,
    questionnumber: int,
    syllabus_title: str,
    topic_title: str,
    score: float,
    method: MatchMethod,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Save an association linking an exam question to a syllabus topic with confidence scoring.
    """
    match = await ctx.deps.topic_match_service.record_match(
        ctx.deps.user,
        examname,
        questionnumber,
        syllabus_title,
        topic_title,
        score,
        method,
    )
    return {
        "status": "success",
        "match_id": str(match.id),
        "score": score,
        "method": str(method),
    }


async def get_matches_for_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve all recorded question mappings linked to a specific syllabus topic.
    """
    matches = await ctx.deps.topic_match_service.get_matches_for_topic(
        ctx.deps.user, examname, syllabus_title, topic_title
    )
    return {
        "status": "success",
        "matches": [
            {
                "id": str(m.id),
                "score": getattr(m, "score", None),
                "method": str(getattr(m, "method", "")),
            }
            for m in matches
        ],
    }


async def delete_weak_matches(
    ctx: RunContext[AgentDeps],
    examname: str,
    questionnumber: int,
    min_score: float,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Remove question-topic associations that fall below a given confidence threshold.
    """
    count = await ctx.deps.topic_match_service.delete_weak_matches(
        ctx.deps.user, examname, questionnumber, min_score
    )
    return {"status": "success", "deleted_count": count}


async def calculate_and_save_priority(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_name: str,
    topic_name: str,
    occurance_count: int,
    years_appeared: int,
    exam_mode: str = "NORMAL",
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Compute and persist weighted topic importance based on past frequency, years appeared, and exam mode.
    """
    priority = (
        await ctx.deps.topic_priority_service.calculate_and_save_priority(
            ctx.deps.user,
            examname,
            syllabus_name,
            topic_name,
            occurance_count,
            years_appeared,
            exam_mode,
        )
    )
    return {
        "status": "success",
        "priority_id": str(getattr(priority, "id", "")),
        "calculated_priority": str(getattr(priority, "priority", priority)),
    }


async def create_generated_material_without_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    material_tile: str,
    content: str,
    type: MaterialType,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Store general exam-wide reference text, cheat sheets, or summary materials not mapped to any specific topic.
    """
    material = await ctx.deps.generated_material_service.create_material(
        ctx.deps.user, examname, material_tile, content, type
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "type": str(type),
    }


async def create_material_with_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    material_tile: str,
    content: str,
    type: MaterialType,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Store targeted revision notes, flashcards, or concept summaries explicitly tied to a syllabus topic.
    """
    material = await ctx.deps.generated_material_service.create_material_topic(
        ctx.deps.user,
        examname,
        material_tile,
        content,
        type,
        syllabus_title,
        topic_title,
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "topic": topic_title,
    }


async def get_material_without_topic(
    ctx: RunContext[AgentDeps], examname: str, material_tile: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve previously saved general study material or formula sheets by title.
    """
    material = await ctx.deps.generated_material_service.get_material(
        ctx.deps.user, examname, material_tile
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "content": str(material.content),
    }


async def get_material_with_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    material_tile: str,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve stored notes, summaries, or flashcards belonging to a specific topic in the syllabus.
    """
    material = await ctx.deps.generated_material_service.get_material_topic(
        ctx.deps.user, examname, material_tile, syllabus_title, topic_title
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "content": str(material.content),
    }


# =====================================================================
# TOOL CATEGORY REGISTRIES
# =====================================================================

EXAM_TOOLS = [
    create_exam,
    get_exam_name,
    calculate_hours,
    get_active_plan,
]

SYLLABUS_TOOLS = [
    create_syllabus,
    create_syllabus_units,
    create_topic,
    get_syllabus_by_name,
    get_by_topic_name,
    update_priority_of_topic,
]

DOCUMENT_INGESTION_TOOLS = [
    record_matches,
    search_with_embeddings,
    register_document,
    update_status,
    get_document_by_name,
    get_related_exam_type_documents,
    get_exam_related_documents,
]

QUESTION_TOOLS = [
    save_new_extracted_questions,
    get_questions_by_exam,
    get_unmatched_questions,
    get_question_by_number,
]

STUDY_PLAN_TOOLS = [
    create_baseline_plan,
    generate_study_plan_item,
    update_plan_item_status,
    update_plan_hours,
]

TOPIC_MATCH_TOOLS = [
    record_match,
    get_matches_for_topic,
    delete_weak_matches,
    calculate_and_save_priority,
    create_generated_material_without_topic,
    create_material_with_topic,
    get_material_without_topic,
    get_material_with_topic,
]

ALL_REGISTERED_TOOLS = (
    EXAM_TOOLS
    + SYLLABUS_TOOLS
    + DOCUMENT_INGESTION_TOOLS
    + QUESTION_TOOLS
    + STUDY_PLAN_TOOLS
    + TOPIC_MATCH_TOOLS
)

# =====================================================================
# DYNAMIC AGENT FACTORY (Context-Adaptive Tool Scaffolding)
# =====================================================================


def get_exam_agent_for_message(
    message: str, has_file: bool = False
) -> Agent[AgentDeps, str]:
    """Dynamically builds an agent registered only with tools pertinent to the incoming prompt.
    Keeps schema count low (3-8 tools) so local 8B models reliably call tools without hallucinating.
    """
    msg = message.lower()
    selected_tools = []

    # 1. File Upload / Document ingestion takes priority when a file is attached
    if (
        has_file
        or "upload" in msg
        or "ingest" in msg
        or "pdf" in msg
        or "document" in msg
    ):
        selected_tools.extend(DOCUMENT_INGESTION_TOOLS)

    # 2. Exam creation, metadata, and hours
    if any(k in msg for k in ["exam", "hour", "mode", "schedule"]):
        selected_tools.extend(EXAM_TOOLS)

    # 3. Syllabus, units, modules, and topics
    if any(k in msg for k in ["syllabus", "unit", "module", "topic"]):
        selected_tools.extend(SYLLABUS_TOOLS)

    # 4. Study plans, scheduling, and task items
    if any(k in msg for k in ["plan", "study plan", "baseline", "progress"]):
        selected_tools.extend(STUDY_PLAN_TOOLS)

    # 5. Question bank, PYQs, and exam queries
    if any(k in msg for k in ["question", "pyq", "previous year", "paper"]):
        selected_tools.extend(QUESTION_TOOLS)

    # 6. Matching, notes, summaries, or materials
    if any(
        k in msg for k in ["match", "material", "notes", "summary", "priority"]
    ):
        selected_tools.extend(TOPIC_MATCH_TOOLS)

    # Fallback: If no distinct keywords matched, provision core exam & syllabus management
    if not selected_tools:
        selected_tools = EXAM_TOOLS + SYLLABUS_TOOLS

    # Deduplicate while preserving order
    seen = set()
    unique_tools = []
    for tool_fn in selected_tools:
        if tool_fn not in seen:
            seen.add(tool_fn)
            unique_tools.append(tool_fn)

    # Create dynamic agent with tight context
    dynamic_agent = Agent(
        model=model,
        deps_type=AgentDeps,
        system_prompt=SYSTEM_PROMPT,
    )
    for tool_fn in unique_tools:
        dynamic_agent.tool(tool_fn)

    return dynamic_agent


# =====================================================================
# DEFAULT FALLBACK AGENT (Backward-compatibility for existing imports)
# ====================================================================
exam_agent = Agent(
    model=model,
    deps_type=AgentDeps,
    system_prompt=SYSTEM_PROMPT,
)

for t in ALL_REGISTERED_TOOLS:
    exam_agent.tool(t)