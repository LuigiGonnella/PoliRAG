# PoliRAG

PoliRAG is a RAG agent microservice and web UI for querying university notes, slides, PDFs, notebooks, reports, and other study material stored in Qdrant.

The current API serves a Vite-built React frontend, manages anonymous chat sessions, stores visible chat history in SQLite, retrieves local context from Qdrant, reranks results, and routes the conversation through a LangGraph agent.

## Architecture

```text
User message
  -> cache judge
  -> rewrite judge
  -> optional query rewrite
  -> local FastEmbed dense/sparse query embedding
  -> Qdrant hybrid retrieval with optional degree/year/course filters
  -> local cross-encoder reranking
  -> optional web fallback when retrieval confidence is low
  -> LLM answer with citations
  -> long-term conversation summary compaction
```

The frontend calls the FastAPI service only. It never talks directly to Qdrant or any LLM provider.

## Course Metadata

Ingestion stores these Qdrant payload fields:

- `degree_level`
- `year`
- `course`
- `source`
- `index`
- `text`

Course filters must use the exact Qdrant metadata values. The frontend displays clean labels generated from those values. For example:

- Display: `Machine Learning For Vision And Multimedia`
- Qdrant value: `MachineLearning_for_Vision_and_Multimedia`

`GET /v1/courses` returns a committed static catalog generated from the original university folder tree, with semester wrapper folders skipped. This keeps deployments independent from the local OneDrive filesystem. Calling `GET /v1/courses?refresh=true` asks Qdrant for live metadata and falls back to the static catalog if Qdrant is unavailable.

## API

- `GET /health`: service, Qdrant, and collection health.
- `GET /v1/courses`: degree/year/course catalog.
- `POST /v1/sessions`: create a general or course-scoped chat session.
- `GET /v1/sessions`: list sessions.
- `GET /v1/sessions/{thread_id}`: session metadata and message history.
- `DELETE /v1/sessions/{thread_id}`: delete one session and its stored messages.
- `POST /v1/agent/chat`: send a message to the agent.
- `POST /v1/agent/chat/stream`: stream assistant text as newline-delimited JSON events.

Source chip details are documented in [`docs/sources.md`](docs/sources.md).

Example chat payload:

```json
{
  "thread_id": "existing-session-id",
  "message": "Explain backpropagation from my notes",
  "degree_filter": "Magistrale",
  "year_filter": "Primo Anno",
  "course_filter": "MachineLearning_for_Vision_and_Multimedia"
}
```

## Environment

Copy `.env.example` to `.env` and fill the keys you use.

Required for agent answers:

- `QDRANT_URL`
- `QDRANT_COLLECTION`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`

Retrieval uses local FastEmbed query embeddings by default:

- `HF_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`
- `HF_API_TOKEN` is optional but recommended; Docker maps it to `HF_TOKEN` so Hugging Face Hub model downloads use authenticated rate limits.

Optional:

- `GEMINI_API_KEY` for lightweight route judges.
- `TAVILY_API_KEY` for web fallback.
- `ENABLE_PYTHON_TOOL=false` by default. Keep it disabled unless the service is isolated for trusted use.
- `MAX_HISTORY_MESSAGES=16` controls how much SQLite chat history is replayed into the agent each turn.
- `AUTO_CREATE_PAYLOAD_INDEXES=true` creates Qdrant keyword indexes for `course`, `year`, and `degree_level` so filtered search works.

## Run Locally

Create or repair a Python environment, then install the API dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-api.txt
```

Start the backend:

```powershell
.\.venv\Scripts\python -m uvicorn src.app.app:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal, start the React frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite app during development:

```text
http://localhost:5173
```

The backend serves the compiled frontend from `frontend/dist` at `http://localhost:8000` after `npm run build`, or automatically when running Docker.

Build the frontend locally:

```powershell
cd frontend
npm run build
```

Production/Docker URL:

```text
http://localhost:8000
```

## Run With Docker

Using the root compose file:

```powershell
docker compose up --build
```

The app is available at:

```text
http://localhost:8000
```

If your documents already live in Qdrant Cloud, set `QDRANT_URL` and `QDRANT_API_KEY` in `.env`. If you want local Qdrant, leave `QDRANT_URL=http://qdrant:6333` for Docker or `http://localhost:6333` for local development.

## Ingestion

The ingestion pipeline is separate from the API runtime and uses the larger `requirements.txt` stack.

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m src.rag.ingestion.pipelines.ingestion_pipeline
```

After ingestion, the metadata repair script can normalize existing Qdrant payloads:

```powershell
.\.venv\Scripts\python scripts\fix_store_metadata.py
```

To add new documents, place them under the expected university folder hierarchy and run ingestion. If you add a new course, also update `src/app/static_courses.py` so deployed frontends can show it without access to your local filesystem. You can compare with live Qdrant metadata by calling:

```text
GET /v1/courses?refresh=true
```

## Testing

Install dev dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Run unit/API tests:

```powershell
.\.venv\Scripts\python -m pytest tests -q
```

Run live Qdrant/RAG tests only when credentials and network access are configured:

```powershell
$env:RUN_QDRANT_TESTS="1"
.\.venv\Scripts\python -m pytest tests\integration -q
```

## Notes

- Chat sessions are anonymous. There is no login or account table; a session is identified only by its generated `thread_id`.
- Visible chat sessions and messages are stored in SQLite at `SESSION_DB_PATH`, so the UI can recover them after container restarts if the `data` volume is preserved.
- The agent replays the latest SQLite message window into each turn. This gives restart-tolerant user-facing context without pretending `MemorySaver` is durable storage.
- LangGraph internal checkpoint memory is still in-process. For true multi-replica production checkpointing, replace `MemorySaver` with a shared checkpoint backend such as Postgres or Redis.
- Local embedding/reranking models can be slow on first use. Configure cloud health-check initial delay/start period to at least 60-90 seconds.
- Web fallback and dynamic tools are optional. Local Qdrant context remains the primary source.
