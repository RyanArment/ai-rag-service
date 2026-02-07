# AI RAG Service

Backend service for RAG, document ingestion, and SEC EDGAR workflows. Built on FastAPI with LLM/embedding providers, PostgreSQL + pgvector (or Chroma), and API-key protection.

## What this service does

- RAG queries with source retrieval and query logging
- Document upload → chunking → embeddings → vector storage
- SEC EDGAR search, ingestion, and queued background processing
- LLM completions with optional streaming responses
- Optional evaluation framework for RAG quality checks

## Quick start

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file:

```bash
# Core
APP_NAME=ai-rag-service
APP_VERSION=0.1.0
DEBUG=true

# Database (required when DEBUG=false)
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/ai_rag

# API access
API_KEY=change-me
API_KEY_HASH_PEPPER=optional-pepper

# LLMs
LLM_PROVIDER=anthropic  # or "openai"
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Vector store
VECTOR_STORE_PROVIDER=pgvector  # or "chroma"
CHROMA_PERSIST_DIR=./chroma_db

# SEC EDGAR
SEC_USER_AGENT=ai-rag-service (contact: you@example.com)
SEC_RATE_LIMIT_PER_SEC=8
SEC_CACHE_DIR=./sec_cache
SEC_WORKER_POLL_SECONDS=3
```

### 4. Initialize the database

```bash
python scripts/init_db.py
```

### 5. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. (Optional) Run the SEC ingestion worker

```bash
python scripts/sec_worker.py
```

Visit `http://localhost:8000/docs` for interactive API docs.

## API highlights

All endpoints (except `/` and `/health`) require `X-API-Key` unless `DEBUG=true` and `API_KEY` is unset.

- `POST /ask` - LLM completion
- `POST /ask/stream` - streaming completion (SSE)
- `POST /documents/upload` - upload and index a document
- `GET /documents/count` - document/chunk counts
- `GET /documents/list` - list documents
- `DELETE /documents/{document_id}` - delete a document and its chunks
- `POST /rag/query` - RAG query with optional SEC filters
- `POST /sec/search` - search EDGAR filings
- `POST /sec/ingest` - ingest a filing immediately
- `POST /sec/ingest/queue` - enqueue a filing for background ingest
- `POST /sec/ingest/queue/process-next` - process one queued job
- `GET /sec/ingest/jobs` - list ingest jobs
- `GET /sec/ingest/jobs/{job_id}` - get a job
- `GET /sec/filings` - list indexed filings
- `POST /sec/research` - research question against filings
- `POST /sec/compare` - compare two filings

Example request:

```bash
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Summarize the risk factors for Apple",
    "form_type": "10-K",
    "top_k": 5
  }'
```

## Vector store setup

The default vector store is `pgvector`. Ensure the Postgres extension is installed:

```bash
./install_pgvector.sh
```

To use Chroma instead, set `VECTOR_STORE_PROVIDER=chroma` and `CHROMA_PERSIST_DIR`.

## Useful scripts

- `scripts/init_db.py` - create all database tables
- `scripts/reset_db.py` - drop and recreate tables
- `scripts/sec_worker.py` - background worker for SEC ingestion queue
