from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel

from app.models.document import DocumentProcessingStatus, DocumentType
from app.models.GeneratedMaterial import MaterialType
from app.models.QuestionTopicMatch import MatchMethod
from app.models.StudyPlanItem import PlanItemPriority, StudyItemStatus
from app.models.Topic import TopicPriority
from app.models.user import User

# Services
from app.services.DocumentService import DocumentService
from app.services.ExamService import ExamService
from app.services.GeneratedMaterialService import GeneratedMaterialService
from app.services.QuestionService import QuestionService
from app.services.StudyPlanService import StudyPlanService
from app.services.SyllabusService import SyllabusService
from app.services.TaskService import TaskService
from app.services.TopicMatchService import TopicMatchService
from app.services.TopicPriorityService import TopicPriorityService


# 1. Context dependency holding authenticated user & active services
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


# 2. Local LLM Runner
ollama_model = OpenAIChatModel(
    model_name="llama3.1:8b",
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

exam_agent = Agent(
    model=ollama_model,
    deps_type=AgentDeps,
    system_prompt=(
        "You are an expert exam preparation assistant. Use the provided tools to manage exams, "
        "inspect syllabus hierarchies, track documents, evaluate PYQ coverage, and update study plans. "
        "Never invent details or statistics; always call the corresponding tool."
    ),
)


# =====================================================================
# EXAM TOOLS
# =====================================================================


@exam_agent.tool
async def calculate_hours(
    ctx: RunContext[AgentDeps], examname: str, daily_study_hours: int
) -> dict[str, Any]:
    """Recalculate remaining usable study hours and update exam mode (SURVIVAL or NORMAL) based on daily study hours."""
    exam = await ctx.deps.exam_service.recalculate_hours(
        ctx.deps.user, examname, daily_study_hours
    )
    return {
        "status": "success",
        "exam_name": exam.name,
        "availableStudyHours": exam.availableStudyHours,
        "mode": exam.mode,
    }


@exam_agent.tool
async def create_exam(
    ctx: RunContext[AgentDeps],
    examname: str,
    daily_study_hours: int,
    exam_datetime: datetime,
) -> dict[str, Any]:
    """Create a new exam schedule given target exam datetime and daily study hours."""
    exam = await ctx.deps.exam_service.create_exam(
        user=ctx.deps.user,
        name=examname,
        examdate=exam_datetime,
        dailystudyhours=daily_study_hours,
    )
    return {
        "status": "success",
        "exam_id": str(exam.id),
        "exam_name": exam.name,
        "mode": exam.mode,
        "availableStudyHours": exam.availableStudyHours,
    }


@exam_agent.tool
async def get_exam_name(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """Retrieve details and study status of a specific exam by its name."""
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


# =====================================================================
# SYLLABUS & TOPIC TOOLS
# =====================================================================


@exam_agent.tool
async def create_syllabus(
    ctx: RunContext[AgentDeps], examname: str, documenttitle: str, filename: str
) -> dict[str, Any]:
    """Create a syllabus root structure for an exam using an uploaded syllabus document."""
    syllabus = await ctx.deps.syllabus_service.create_syllabus_structure(
        ctx.deps.user, examname, documenttitle, filename
    )
    return {
        "status": "success",
        "syllabus_id": str(syllabus.id),
        "title": getattr(syllabus, "title", documenttitle),
    }


@exam_agent.tool
async def create_syllabus_units(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabustitle: str,
    unitname: str,
    description: str,
    unitNumber: int,
) -> dict[str, Any]:
    """Add a unit/module to an existing syllabus with its unit number and description."""
    unit = await ctx.deps.syllabus_service.create_syllabus_unit(
        ctx.deps.user, syllabustitle, unitname, unitNumber, description
    )
    return {
        "status": "success",
        "unit_id": str(unit.id),
        "unit_name": unitname,
        "unit_number": unitNumber,
    }


@exam_agent.tool
async def get_by_topic_name(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabusname: str,
    topictitle: str,
) -> dict[str, Any]:
    """Fetch details and current base priority of a specific topic within a syllabus."""
    topic = await ctx.deps.syllabus_service.getTopicByName(
        ctx.deps.user, examname, syllabusname, topictitle
    )
    return {
        "status": "success",
        "topic_id": str(topic.id),
        "name": getattr(topic, "name", topictitle),
        "priority": str(getattr(topic, "priority", "")),
    }


@exam_agent.tool
async def update_priority_of_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topicName: str,
    pr: TopicPriority,
) -> dict[str, Any]:
    """Update the base priority level (e.g. HIGH, MEDIUM, LOW) of a syllabus topic."""
    topic = await ctx.deps.syllabus_service.updateTopicBasePriority(
        ctx.deps.user, examname, syllabus_title, topicName, pr
    )
    return {
        "status": "success",
        "topic_id": str(topic.id),
        "updated_priority": str(pr),
    }


# =====================================================================
# DOCUMENT TOOLS
# =====================================================================


@exam_agent.tool
async def register_document(
    ctx: RunContext[AgentDeps],
    examname: str,
    filename: str,
    storagePath: str,
    st: DocumentProcessingStatus,
    type: DocumentType,
) -> dict[str, Any]:
    """Register a new uploaded syllabus or PYQ document in the system."""
    document = await ctx.deps.document_service.registerDocument(
        ctx.deps.user, filename, examname, storagePath, st, type
    )
    return {
        "status": "success",
        "document_id": str(document.id),
        "filename": document.filename,
        "processing_status": str(document.status),
    }


@exam_agent.tool
async def update_status(
    ctx: RunContext[AgentDeps],
    document_id: UUID,
    status: DocumentProcessingStatus,
) -> dict[str, Any]:
    """Update processing lifecycle status of a document (e.g. PENDING, PROCESSED, FAILED)."""
    document = await ctx.deps.document_service.transition_document_status(
        document_id, status
    )
    return {
        "status": "success",
        "document_id": str(document.id),
        "new_status": str(document.status),
    }


@exam_agent.tool
async def get_document_by_name(
    ctx: RunContext[AgentDeps], exam_name: str, filename: str
) -> dict[str, Any]:
    """Find a specific document linked to an exam by its filename."""
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


@exam_agent.tool
async def get_related_exam_type_documents(
    ctx: RunContext[AgentDeps], exam_name: str, type: DocumentType
) -> dict[str, Any]:
    """List documents filtered by type (e.g. SYLLABUS, PYQ) for an exam."""
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


@exam_agent.tool
async def get_exam_related_documents(
    ctx: RunContext[AgentDeps], exam_name: str
) -> dict[str, Any]:
    """List all documents registered under an exam."""
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
# GENERATED MATERIAL TOOLS
# =====================================================================


@exam_agent.tool
async def create_generated_material_without_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    material_tile: str,
    content: str,
    type: MaterialType,
) -> dict[str, Any]:
    """Save generated revision notes or summaries attached to the exam in general."""
    material = await ctx.deps.generated_material_service.create_material(
        ctx.deps.user, examname, material_tile, content, type
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "type": str(type),
    }


@exam_agent.tool
async def create_material_with_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    material_tile: str,
    content: str,
    type: MaterialType,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """Save generated revision notes or summaries linked to a specific syllabus topic."""
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


@exam_agent.tool
async def get_material_without_topic(
    ctx: RunContext[AgentDeps], examname: str, material_tile: str
) -> dict[str, Any]:
    """Retrieve saved general study material by title for an exam."""
    material = await ctx.deps.generated_material_service.get_material(
        ctx.deps.user, examname, material_tile
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "content": str(material.content),
    }


@exam_agent.tool
async def get_material_with_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    material_tile: str,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """Retrieve saved topic-specific study material by title and topic name."""
    material = await ctx.deps.generated_material_service.get_material_topic(
        ctx.deps.user, examname, material_tile, syllabus_title, topic_title
    )
    return {
        "status": "success",
        "material_id": str(material.id),
        "content": str(material.content),
    }


# =====================================================================
# QUESTION TOOLS
# =====================================================================


@exam_agent.tool
async def save_new_extracted_questions(
    ctx: RunContext[AgentDeps],
    examname: str,
    document_id: UUID,
    questions_data: list[dict],
) -> dict[str, Any]:
    """Persist structured questions extracted from a PYQ document into the database."""
    saved_questions = (
        await ctx.deps.question_service.save_extracted_questions(
            ctx.deps.user, examname, document_id, questions_data
        )
    )
    return {
        "status": "success",
        "saved_count": len(saved_questions),
        "question_ids": [str(q.id) for q in saved_questions],
    }


@exam_agent.tool
async def get_questions_by_exam(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """Retrieve all past exam questions stored for an exam."""
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


@exam_agent.tool
async def get_unmatched_questions(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """Retrieve questions that have not yet been mapped to any topic in the syllabus."""
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


@exam_agent.tool
async def get_question_by_number(
    ctx: RunContext[AgentDeps], examname: str, question_number: int
) -> dict[str, Any]:
    """Retrieve a single question by its question number under a specific exam."""
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
# STUDY PLAN TOOLS
# =====================================================================


@exam_agent.tool
async def get_active_plan(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """Fetch the currently active study plan and its metadata for an exam."""
    plan = await ctx.deps.study_plan_service.get_active_plan(
        ctx.deps.user, examname
    )
    return {
        "status": "success",
        "plan_id": str(plan.id),
        "version": getattr(plan, "version", "1.0"),
    }


@exam_agent.tool
async def create_baseline_plan(
    ctx: RunContext[AgentDeps], examname: str, version: str
) -> dict[str, Any]:
    """Generate a baseline study plan version for an exam."""
    plan = await ctx.deps.study_plan_service.generate_baseline_plan(
        ctx.deps.user, examname, version
    )
    return {
        "status": "success",
        "plan_id": str(plan.id),
        "version": version,
    }


@exam_agent.tool
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
    """Add a topic item to the study plan with allocated study hours and priority."""
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


@exam_agent.tool
async def update_plan_item_status(
    ctx: RunContext[AgentDeps], examname: str, status: StudyItemStatus
) -> dict[str, Any]:
    """Update progress status (e.g. NOT_STARTED, IN_PROGRESS, COMPLETED) for a study plan item."""
    item = await ctx.deps.study_plan_service.update_plan_item_status(
        ctx.deps.user, examname, status
    )
    return {
        "status": "success",
        "item_id": str(item.id),
        "status": str(status),
    }


@exam_agent.tool
async def update_plan_hours(
    ctx: RunContext[AgentDeps],
    examname: str,
    adjusted_daily_hours: float | None = None,
) -> dict[str, Any]:
    """Recalculate and update the study plan when daily study hours are modified."""
    plan = await ctx.deps.study_plan_service.update_plan(
        ctx.deps.user, examname, adjusted_daily_hours
    )
    return {
        "status": "success",
        "plan_id": str(plan.id),
    }


# =====================================================================
# TOPIC MATCH & PRIORITY TOOLS
# =====================================================================


@exam_agent.tool
async def record_match(
    ctx: RunContext[AgentDeps],
    examname: str,
    questionnumber: int,
    syllabus_title: str,
    topic_title: str,
    score: float,
    method: MatchMethod,
) -> dict[str, Any]:
    """Record an association match between an exam question and a syllabus topic with a confidence score."""
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


@exam_agent.tool
async def get_matches_for_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """Retrieve all past exam questions mapped to a particular syllabus topic."""
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


@exam_agent.tool
async def delete_weak_matches(
    ctx: RunContext[AgentDeps],
    examname: str,
    questionnumber: int,
    min_score: float,
) -> dict[str, Any]:
    """Delete question-topic associations that fall below a confidence threshold."""
    count = await ctx.deps.topic_match_service.delete_weak_matches(
        ctx.deps.user, examname, questionnumber, min_score
    )
    return {
        "status": "success",
        "deleted_count": count,
    }


@exam_agent.tool
async def calculate_and_save_priority(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_name: str,
    topic_name: str,
    occurance_count: int,
    years_appeared: int,
    exam_mode: str = "NORMAL",
) -> dict[str, Any]:
    """Calculate and save weighted topic priority based on PYQ frequency and exam mode."""
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
        "calculated_priority": str(
            getattr(priority, "priority", priority)
        ),
    }