# Syllabus Sentry (Backend Engine)

An asynchronous AI agent backend for academic exam preparation. It processes course syllabi and previous-year question papers (PYQs), stores text embeddings in PostgreSQL using `pgvector`, and uses a tool-routed LLM agent with PydanticAI to generate study plans, topic priorities, and study materials.

---

## Architecture & Design Decisions

### 1. Dynamic Tool Routing (Agent Factory)

The backend registers 33 domain tools for exam profiles, syllabus management, document search, question banks, and study plans.

- **Problem:** Providing too many tool schemas to smaller or local LLMs can cause schema parsing errors, incorrect parameters, and unreliable tool selection.
- **Solution:** `get_exam_agent_for_message` analyzes the user message and available attachments to create an agent with a smaller set of relevant tools for each request.

### 2. Defensive Serialization

- Database entities fetched using async SQLAlchemy are converted into dictionaries before being returned by agent tools.
- UUIDs are converted to strings, datetimes to ISO 8601 strings, and ORM attributes are extracted before serialization.
- Tool inputs handle both native JSON structures and JSON strings where required.

### 3. Asynchronous Persistence & Transactions

- Built using **FastAPI**, **SQLAlchemy (asyncio)**, and **Uvicorn**.
- Uses an `AutoContainer` pattern to manage sessions, repositories, and domain services.
- Commit and rollback operations are managed at the request and service layers to avoid session lifecycle conflicts.

### 4. Document Ingestion & Semantic Retrieval (RAG)

- Accepts PDF uploads for course syllabi and previous-year question papers.
- Uses PyMuPDF (`fitz`) to extract text from uploaded PDF files.
- Splits extracted text into chunks, generates embeddings, and stores them in PostgreSQL using `pgvector`.
- Uses semantic search to retrieve relevant PYQs and match them with syllabus topics.
- Uses the retrieved information to support topic prioritization and study-plan generation.

---

## Tech Stack

- **Language:** Python 3.12+
- **Web Framework:** FastAPI, Uvicorn
- **Agent Framework:** PydanticAI
- **Database:** PostgreSQL, SQLAlchemy (async)
- **Vector Search:** `pgvector`
- **Document Processing:** PyMuPDF (`fitz`)
- **LLM / Embeddings:** OpenAI API / Local Ollama instances

---

## Core Tool Modules

The backend contains 33 registered tools across the following modules:

- **Exam Tools:** Exam profile initialization, target dates, daily available hours, and study modes (`NORMAL` and `SURVIVAL`).
- **Syllabus & Topic Tools:** Syllabus containers, units, topics, and base priority assignment.
- **Document Ingestion:** PDF parsing, chunk embedding generation, vector storage, and document processing status.
- **Question Bank:** PYQ storage and retrieval, exam-based filtering, and unmatched question identification.
- **Study Plans:** Baseline plan generation, topic scheduling, and study-hour allocation.
- **Topic Matching & Materials:** Semantic similarity between PYQs and syllabus topics, topic priority calculations, flashcards, and summary notes.

---

## Primary API Endpoints

### 1. Authentication

- `POST /api/register` — Register a user account.
- `POST /api/login` — Authenticate a user and return authentication tokens.

### 2. Conversational Agent

**`POST /chat/message`**

Accepts multipart form data.

| Parameter | Description |
|---|---|
| `session_title` | Chat session title |
| `message` | User message or instruction |
| `file` | Optional syllabus or PYQ PDF |

The endpoint processes the message and optional uploaded document, selects relevant agent tools, executes the required operations, and returns a response.

The agent supports tasks such as generating baseline study plans and prioritizing Operating Systems topics based on available PYQ data.

---

## Local Setup

### 1. Prerequisites

- Python 3.12 or newer
- PostgreSQL
- PostgreSQL `pgvector` extension
- Access to a configured LLM and embedding provider

Enable the vector extension in your database:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Configure Environment Variables

Create a `.env` file with the database connection, LLM provider credentials, and other configuration required by the application.

Use the variable names expected by your project settings. Do not commit API keys or database credentials to GitHub.

### 3. Install Dependencies

Activate your virtual environment and install the project's dependencies using its dependency file.

### 4. Run the Backend

Start the FastAPI application using the correct application module path for your project.

Once the server is running, use the API endpoints to test authentication, chat requests, and document uploads.

---

## Current Status

- Authentication endpoints implemented.
- Conversational agent endpoint tested successfully.
- Baseline Operating Systems study-plan generation tested.
- Dynamic tool routing and document retrieval are part of the backend design.

