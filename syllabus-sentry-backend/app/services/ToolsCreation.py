from __future__ import annotations
from pydantic_ai.models.openai import OpenAIChatModel
from app.core.config import settings
from pydantic_ai import Agent
from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any
from fastapi import UploadFile
from uuid import UUID
from typing import Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIChatModel
from app.models.document import DocumentProcessingStatus, DocumentType
from app.models.GeneratedMaterial import MaterialType
from app.models.QuestionTopicMatch import MatchMethod
from app.models.StudyPlanItem import PlanItemPriority, StudyItemStatus
from app.models.Topic import TopicPriority
from app.models.DocumentEmbedding import DocumentEmbedding
from app.models.user import User
from app.repositories.ChatMessageRepository import ChatMessageRepository
from app.repositories.ChatSessionRepository import ChatSessionRepository

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
from app.services.DocuemntIngestionService import DocumentIngestionService

os.environ["OPENAI_BASE_URL"] = settings.OPENAI_BASE_URL
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
# ====================================================================
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
    document_ingestion_service:DocumentIngestionService
    uploaded_file: Optional[UploadFile] = None



ollama_client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # dummy key required by the client
)
model = OpenAIChatModel("gpt-4o-mini")
exam_agent = Agent(
    model=model,
    deps_type=AgentDeps,
    system_prompt = (
   "You are an academic exam assistant.\n"
        "IMPORTANT RULES:\n"
        "- When the user asks to ingest, upload, or process notes, you MUST call the `record_matches` tool.\n"
        "- NEVER output raw JSON, code blocks, or function-call text in your message response.\n"
        "- NEVER output `{\"type\": \"function\" ...}` or markdown containing tool schemas.\n"
        "- Call the tool silently and reply only in plain text confirming the operation when done." \
        "Always invoke tools when requested."
)
)



# =====================================================================
# EXAM TOOLS
# =====================================================================


@exam_agent.tool
async def get_exam_name(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve current status, total available usable study hours, exam date, and preparation mode (NORMAL or SURVIVAL) for an existing exam.
    USE THIS TOOL WHEN: The user asks what mode they are in, how many hours they have left, or requests current exam details.
    DO NOT USE: When the user asks to modify hours or register a new exam.
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
@exam_agent.tool
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
            return {"status": "not_found", "message": f"No active study plan found for exam '{examname}'."}
            
        return {
            "status": "success",
            "plan_id": str(plan.id),
            "version": getattr(plan, "version", "1.0"),
        }
    except Exception as e:
        # Return error message to the agent instead of bubbling up an HTTP 404/500
        return {
            "status": "not_found",
            "message": f"No study plan found for {examname}. Error: {str(e)}"
        }


@exam_agent.tool
async def calculate_hours(
    ctx: RunContext[AgentDeps], examname: str, daily_study_hours: int
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Recalculate and update remaining usable study hours and exam mode (NORMAL vs SURVIVAL) for an existing exam in the database.
    USE THIS TOOL ONLY WHEN: The user explicitly provides a new or modified daily study commitment (e.g., 'I will now study 5 hours daily').
    DO NOT USE: For read-only status inquiries (use `get_exam_name` instead).
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


@exam_agent.tool
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
# SYLLABUS & TOPIC TOOLS
# =====================================================================


@exam_agent.tool
async def create_syllabus(
    ctx: RunContext[AgentDeps], examname: str, documenttitle: str, filename: str
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Initialize the root syllabus record for an exam based on an uploaded document file.
    USE THIS TOOL WHEN: Setting up the primary syllabus container for an exam before adding units.
    """
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
    """[ACTION / MUTATION]
    Add a module or unit section (with index number and description you need to pass from the message about what units are there in it) to an existing syllabus.
    USE THIS TOOL WHEN: Structuring a syllabus into formal numbered units/modules.
    """
    unit = await ctx.deps.syllabus_service.create_syllabus_unit(
       examname, ctx.deps.user, syllabustitle, unitname, unitNumber, description
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
    """[READ-ONLY QUERY]
    Fetch detailed topic information, current priority level, and metadata for a specific topic within a syllabus.
    USE THIS TOOL WHEN: Inspecting a specific topic's existing priority or details.
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


@exam_agent.tool
async def update_priority_of_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topicName: str,
    pr: TopicPriority,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Manually override the baseline priority level (HIGH, MEDIUM, or LOW) of a syllabus topic.
    USE THIS TOOL WHEN: A user explicitly requests to bump or lower the priority of a particular topic.
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
    """[ACTION / MUTATION]
    Record an uploaded file (SYLLABUS or PYQ) into the document tracking repository with its initial processing status.
    USE THIS TOOL WHEN: A file has been saved to disk/storage and needs a registered tracking entry.
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


@exam_agent.tool
async def update_status(
    ctx: RunContext[AgentDeps],
    document_id: UUID,
    status: DocumentProcessingStatus,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Transition document processing status through the lifecycle (PENDING, PROCESSING, PROCESSED, FAILED).
    USE THIS TOOL WHEN: Document extraction finishes, begins processing, or errors out.
    """
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
    """[READ-ONLY QUERY]
    Locate a single document associated with an exam using its exact filename.
    USE THIS TOOL WHEN: Verifying whether a document is already uploaded or checking its status.
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


@exam_agent.tool
async def get_related_exam_type_documents(
    ctx: RunContext[AgentDeps], exam_name: str, type: DocumentType
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    List all documents attached to an exam filtered by type (e.g. SYLLABUS or PYQ).
    USE THIS TOOL WHEN: Listing uploaded question papers only or uploaded syllabus files only.
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


@exam_agent.tool
async def get_exam_related_documents(
    ctx: RunContext[AgentDeps], exam_name: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    List all uploaded files (both PYQs and Syllabi) registered under an exam.
    USE THIS TOOL WHEN: The user asks what documents or files have been uploaded for an exam.
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
    """[ACTION / MUTATION]
    Store general exam-wide reference text, cheat sheets, or summary materials not mapped to any specific topic.
    USE THIS TOOL WHEN: Saving general exam guidelines, formula sheets, or course-wide study notes.
    """
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
    """[ACTION / MUTATION]
    Store targeted revision notes, flashcards, or concept summaries explicitly tied to a syllabus topic.
    USE THIS TOOL WHEN: Saving study materials generated for a single topic or concept.
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


@exam_agent.tool
async def get_material_without_topic(
    ctx: RunContext[AgentDeps], examname: str, material_tile: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve previously saved general study material or formula sheets by title.
    USE THIS TOOL WHEN: Fetching stored general course notes that do not belong to an individual topic.
    """
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
    """[READ-ONLY QUERY]
    Retrieve stored notes, summaries, or flashcards belonging to a specific topic in the syllabus.
    USE THIS TOOL WHEN: The student asks to view saved revision material for a designated topic.
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
# QUESTION TOOLS
# =====================================================================


@exam_agent.tool
async def save_new_extracted_questions(
    ctx: RunContext[AgentDeps],
    examname: str,
    document_id: UUID,
    questions_data: list[dict],
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Persist a batch of structured PYQ questions parsed from an exam paper into the database.
    USE THIS TOOL WHEN: Ingesting newly extracted question sets from an uploaded PYQ document.
    """
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
    """[READ-ONLY QUERY]
    Retrieve all historical previous-year exam questions logged in the system for an exam.
    USE THIS TOOL WHEN: The user requests past questions, PYQ lists, or question counts for the course.
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


@exam_agent.tool
async def get_unmatched_questions(
    ctx: RunContext[AgentDeps], examname: str
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Fetch all PYQs for an exam that have not yet been categorized or mapped to a syllabus topic.
    USE THIS TOOL WHEN: Checking syllabus mapping coverage or auditing unassigned questions.
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


@exam_agent.tool
async def get_question_by_number(
    ctx: RunContext[AgentDeps], examname: str, question_number: int
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve the text, mark allotment, and year for a single specific question number.
    USE THIS TOOL WHEN: A user asks about an exact question (e.g. 'Show me Question 4 from the OS exam').
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
# STUDY PLAN TOOLS
# =====================================================================

 


@exam_agent.tool
async def create_baseline_plan(
    ctx: RunContext[AgentDeps], examname: str, version: str
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Initialize a new baseline study plan schedule container for an exam.
    USE THIS TOOL WHEN: Setting up the master schedule before populating topic items.
    """
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
    """[ACTION / MUTATION]
    Add a scheduled topic item into the active study plan with allotted hours, sequence order, and priority.
    USE THIS TOOL WHEN: Adding an individual study task or topic allocation into the student's study plan.
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


@exam_agent.tool
async def update_plan_item_status(
    ctx: RunContext[AgentDeps], examname: str, status: StudyItemStatus
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Update execution state (NOT_STARTED, IN_PROGRESS, COMPLETED) of a study plan entry.
    USE THIS TOOL WHEN: The user marks a topic as done, started, or skipped in their plan.
    """
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
    """[ACTION / MUTATION]
    Recalculate study hour distributions across all plan items following a schedule shift.
    USE THIS TOOL WHEN: Redistributing topic hours across an existing study plan.
    """
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
    """[ACTION / MUTATION]
    Save an association linking an exam question to a syllabus topic with confidence scoring.
    USE THIS TOOL WHEN: Mapping a PYQ to a specific syllabus topic.
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


@exam_agent.tool
async def get_matches_for_topic(
    ctx: RunContext[AgentDeps],
    examname: str,
    syllabus_title: str,
    topic_title: str,
) -> dict[str, Any]:
    """[READ-ONLY QUERY]
    Retrieve all recorded question mappings linked to a specific syllabus topic.
    USE THIS TOOL WHEN: The user asks what past questions appeared for a particular topic.
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


@exam_agent.tool
async def delete_weak_matches(
    ctx: RunContext[AgentDeps],
    examname: str,
    questionnumber: int,
    min_score: float,
) -> dict[str, Any]:
    """[ACTION / MUTATION]
    Remove question-topic associations that fall below a given confidence threshold.
    USE THIS TOOL WHEN: Cleaning up noisy or low-confidence question associations.
    """
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
    """[ACTION / MUTATION]
    Compute and persist weighted topic importance based on past frequency, years appeared, and exam mode.
    USE THIS TOOL WHEN: Recalculating topic weightings after new PYQ data has been processed.
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
        "calculated_priority": str(
            getattr(priority, "priority", priority)
        ),
    }
@exam_agent.tool
async def create_topic(ctx:RunContext[AgentDeps],examname:str,syllabusTitle:str,Topicname:str,description:str,priority:TopicPriority,unitNumber:int,estimatedHours:int)->dict[str,Any]:
    """[ACTION / MUTATION]
    Creates and persists a new academic topic under a specific syllabus unit.

    WHEN TO USE:
    - Invoke this tool when the user wants to add, register, create, or break down
      a subject topic, concept, module chapter, or syllabus item.
    - MUST be executed BEFORE creating study plan items that reference this topic name.

    DO NOT USE:
    - Do NOT use for general study questions or exam metadata retrieval.

    Args:
        examname: Name of the target exam (e.g., 'Operating Systems').
        syllabusTitle: Title of the parent syllabus document container (e.g., 'OS Core Syllabus 2026').
        Topicname: The unique title of the topic or concept (e.g., 'CPU Scheduling Algorithms').
        description: Granular explanation, key bullet concepts, or covered subtopics.
        priority: Relative urgency or weight ('HIGH', 'MEDIUM', 'LOW').
        unitNumber: The integer index of the parent unit this topic belongs to (e.g., 1).
        estimatedHours: Estimated hours required to study this topic.
    """
    t=await ctx.deps.syllabus_service.createTopic(ctx.deps.user,examname,syllabusTitle,Topicname,description,priority,unitNumber,estimatedHours)
    return {
        "status": "success",
        "topic_id": str(t.id),
        "New Topic": t
    }
@exam_agent.tool
async def get_syllabus_by_name(ctx:RunContext[AgentDeps],examname:str,syllabusTitle:str)->dict[str,Any]:
    """[QUERY / READ]
    Fetches the syllabus container details and structure for an exam.

    WHEN TO USE:
    - Invoke this tool when verifying if a syllabus exists, inspecting syllabus metadata,
      or retrieving the syllabus ID for an exam before performing operations.

    Args:
        examname: Name of the exam (e.g., 'Operating Systems').
        syllabusTitle: Title of the registered syllabus (e.g., 'OS Core Syllabus 2026').
    """

    ns=await ctx.deps.syllabus_service.get_syllabus_by_name(ctx.deps.user,examname,syllabusTitle)
    return {
            "status": "success",
            "syllabus_id": str(ns.id),
            "Syllabus": ns
        }
@exam_agent.tool
async def record_matches(ctx:RunContext[AgentDeps],examname:str,sourceType:DocumentType,unitNumber:Optional[int]|None=None)->dict[str,Any]:
    """Ingest and vectorize the attached PDF file into the database for a given exam.

    Args:
        examname: Name of the exam (e.g. 'Operating Systems').
        sourceType: SYLLABUS, PYQ, ASSIGNMENT, INTERNAL_EXAM, or NOTES.
        unitNumber: Optional unit or module number."""
    file = ctx.deps.uploaded_file
    if not file:
        return {
            "status": "failed",
            "message": "No file was attached to this request to process.",
        }

    file_bytes = await file.read()
    await ctx.deps.document_ingestion_service.record(ctx.deps.user,examname,sourceType,file_bytes,unitNumber)
    return{
        "status":"success"
    }
@exam_agent.tool
async def search_with_embeddings(ctx:RunContext[AgentDeps],examname:str,question:str,unitNumber:int=None,limit:int=5)->dict[str,Any]:
    """
    [READ-ONLY QUERY]
    Semantically search uploaded syllabus documents and course materials for relevant context.

    WHEN TO USE:
    - The student asks a concept, theory, or syllabus-related question for an exam.
    - Check uploaded materials first before answering from general knowledge.
    """
    embeddings=await ctx.deps.document_ingestion_service.search(ctx.deps.user,examname,question,limit,unitNumber)
    if not embeddings:
        return {
            "status": "empty",
            "message": "No relevant document excerpts found in uploaded materials.",
            "chunks": [],
        }
    return{
        "status":"success",
        "chunks": [
            {
                "content": item.content,
                "unit_number": item.unit_number,
                "chunk_index": item.chunk_index,
                "source_type": str(item.source_type),
            }
            for item in embeddings
        ]
    }




