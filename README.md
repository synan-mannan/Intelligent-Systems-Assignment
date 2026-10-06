# People Operations Assistant

A small handbook question-answering and Performance Review booking app. The React client talks to a FastAPI API; a LangGraph workflow routes each turn to handbook RAG or the booking flow and keeps the conversation in memory by `thread_id`.

## Architecture

- `backend/app/api`: asynchronous FastAPI endpoints and request/response schemas.
- `backend/app/graph`: typed conversation state, routing, workflow nodes, and the in-memory checkpointer.
- `backend/app/rag`: handbook download, PDF parsing, chunking, Chroma storage, and similarity retrieval.
- `backend/app/tools/booking.py`: available slots, contact parsing, and booking reference generation.
- `frontend`: React + Vite chat client; Vite proxies `/api` to FastAPI during development.

## LangGraph State Flow

Each request adds a user message to the graph state using the supplied `thread_id`. The router extracts a name/email if present and sends handbook questions to the FAQ node before considering the pending booking. The booking node requests missing contact details, offers slots, requests confirmation, then returns a reference ID. `MemorySaver` checkpoints all fields and messages for that thread while the backend process is running.

## RAG Flow

On backend startup, the app downloads the employee handbook if absent, loads pages with `PyPDFLoader`, and splits them into 1,000-character chunks with 150-character overlap. Chroma stores the chunks and uses its default local embedding function for vectorization and similarity search. The FAQ node supplies the top four matches to Groq (`qwen/qwen3.8-27b`) and appends handbook page citations.

## API

- `GET /api/slots` returns three upcoming weekday appointment slots.
- `POST /api/chat` accepts `{"thread_id":"...","message":"..."}` and returns the response, booking state, and thread ID.

FastAPI also serves its interactive schema at `/docs` while running.

## Backend Setup

From the repository root, in PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set GROQ_API_KEY in .env
uvicorn app.main:app --reload
```

The first backend start downloads the PDF and creates the local Chroma index. The initial embedding model download may take a little while.

## Frontend Setup

In a second terminal from the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). The client retains the thread ID and visible messages in browser local storage.

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and set:

- `GROQ_API_KEY`: required for handbook answers; never commit the populated `.env` file.

Booking and `/api/slots` work without a Groq key. FAQ requests return a clear configuration error until it is set.

## Context Interleaving Example

1. User: `I want to book a Performance Review.`
2. Assistant asks for a name and email.
3. User: `Alex Chen, alex.chen@example.com. Before that, how often are performance reviews conducted?`
4. Assistant answers from the handbook with page citation and asks Alex to choose a slot. The router stores the contact details before routing to RAG; the FAQ node does not change the pending booking state.
5. User selects a listed slot, then confirms. The assistant returns a booking reference.

## Verification

With the backend environment active, run these checks:

```powershell
python -c "from app.rag.retriever import retrieve_handbook_context; docs=retrieve_handbook_context('How often are performance reviews conducted?'); print([(d.metadata.get('page', 0) + 1, d.page_content[:120]) for d in docs])"
Invoke-RestMethod http://localhost:8000/api/slots
Invoke-RestMethod -Method Post http://localhost:8000/api/chat -ContentType 'application/json' -Body '{"thread_id":"demo-1","message":"I want to book a Performance Review"}'
```

Continue the chat requests with the same `thread_id`, providing a name/email, a slot ID (`slot-1` etc.), and `yes`. To verify interleaving, send the contact details together with a handbook question between the booking prompt and slot choice. A RAG answer should include a source such as `Employee Handbook, p. 12`; the response should still report the saved name/email and pending booking state. A different `thread_id` starts a separate conversation. The frontend uses these same endpoints through the Vite proxy.

## AI Engineering Log

- AI tool used: GitHub Copilot in VS Code for implementation and validation.
- Issue observed: the first slot-label implementation used `strftime`'s Unix-only `%-d`/`%-I` directives. Running the slot generator on Windows raised `ValueError: Invalid format string`; replacing those directives with portable `%d`/`%I` formatting made the same check pass.
- Issue observed: an actual FAQ request returned Groq `model_not_found` for `llama-3.3-70b-versatile`. The account's model list showed `qwen/qwen3.8-27b` as available; the implementation now uses that advertised model.
- Issue observed: the first live RAG answer cited page 4 in its text but the source footer also listed an unrelated retrieved page 8. The footer now filters retrieved citations to pages named by the answer.
