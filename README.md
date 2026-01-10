# AI RAG Service

A production-ready AI RAG (Retrieval-Augmented Generation) backend built with FastAPI, supporting multiple LLM providers (OpenAI + Anthropic) with proper logging, error handling, streaming, and evaluation.

## Features

- ✅ **Multi-Provider LLM Support**: OpenAI and Anthropic with unified interface
- ✅ **Streaming Responses**: Server-Sent Events (SSE) for real-time generation
- ✅ **Structured Logging**: JSON logs for production, readable logs for development
- ✅ **Error Handling**: Comprehensive error handling with proper HTTP status codes
- ✅ **Request Tracing**: Request IDs for debugging and monitoring
- ✅ **Evaluation Framework**: Extensible evaluation system for testing RAG quality
- ✅ **Type Safety**: Full Pydantic validation and type hints
- ✅ **Async Support**: Full async/await support for scalability

## Quick Start

### 1. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or: venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file:

```bash
# LLM Configuration
LLM_PROVIDER=anthropic  # or "openai"
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key  # Optional, only needed if using OpenAI

# Logging
LOG_LEVEL=INFO
LOG_JSON=false

# Application
APP_NAME=ai-rag-service
APP_VERSION=0.1.0
DEBUG=false
```

### 4. Run the Server

**Important:** Make sure your virtual environment is activated:
```bash
source venv/bin/activate  # macOS/Linux
```

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the API

Visit http://localhost:8000/docs for interactive API documentation.

Or test with curl:

```bash
# Non-streaming
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?"}'

# Streaming
curl -X POST "http://localhost:8000/ask/stream" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a short story", "stream": true}'
```

## Project Structure

```
app/
├── main.py                    # FastAPI app entry point
├── core/
│   ├── config.py             # Configuration & env vars
│   ├── exceptions.py          # Custom exceptions
│   ├── logging_config.py      # Logging setup
│   └── responses.py           # Unified response schemas
├── routes/
│   ├── __init__.py
│   └── ask_router.py          # LLM completion endpoints
├── services/
│   ├── llm/
│   │   ├── base.py            # Base LLM interface
│   │   ├── openai_client.py   # OpenAI implementation
│   │   └── anthropic_client.py # Anthropic implementation
│   ├── llm_router.py          # LLM client factory
│   └── evaluation/
│       ├── base.py            # Evaluation base classes
│       ├── metrics.py         # Concrete metrics
│       └── evaluator.py       # Evaluation orchestrator
```

## API Endpoints

### POST `/ask`
Non-streaming LLM completion.

**Request:**
```json
{
  "prompt": "What is Python?",
  "system_prompt": "You are a helpful assistant.",
  "temperature": 0.7,
  "max_tokens": 1000,
  "provider": "anthropic"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content": "Python is a programming language...",
    "model": "claude-3-5-sonnet-20241022",
    "provider": "anthropic",
    "usage": {
      "prompt_tokens": 10,
      "completion_tokens": 50,
      "total_tokens": 60
    },
    "latency_ms": 1234.5
  },
  "request_id": "uuid-here"
}
```

### POST `/ask/stream`
Streaming LLM completion (Server-Sent Events).

**Request:** Same as `/ask`

**Response:** SSE stream of chunks:
```
data: {"content": "Python", "done": false, "model": "claude-3-5-sonnet-20241022", "provider": "anthropic"}

data: {"content": " is", "done": false, "model": "claude-3-5-sonnet-20241022", "provider": "anthropic"}

data: {"content": "", "done": true, "model": "claude-3-5-sonnet-20241022", "provider": "anthropic"}
```

### GET `/health`
Health check endpoint.

## Evaluation Framework

The evaluation framework allows you to test RAG system quality:

```python
from app.services.evaluation.evaluator import Evaluator
from app.services.evaluation.metrics import ExactMatchEvaluator, F1ScoreEvaluator

# Initialize evaluator
evaluator = Evaluator([
    ExactMatchEvaluator(),
    F1ScoreEvaluator(),
])

# Evaluate batch
test_set = [
    {
        "question": "What is Python?",
        "expected_answer": "Python is a programming language",
        "actual_answer": "Python is a high-level programming language",
    },
]

report = evaluator.evaluate_batch(test_set, test_set_name="python_qa")
evaluator.save_report(report, "evaluation_results.json")
```

## Development Roadmap

See [DAY3_PLUS_GUIDE.md](./DAY3_PLUS_GUIDE.md) for detailed implementation guide and next steps.

**Current Status:** Days 1-5 Complete
- ✅ Day 1-2: Basic setup and provider abstraction
- ✅ Day 3: Logging, error handling, unified responses
- ✅ Day 4: Streaming support
- ✅ Day 5: Evaluation framework

**Next Steps:**
- Day 6-7: Embedding service
- Day 8-10: Vector database integration
- Day 11-12: Document processing
- Day 13-15: RAG pipeline core

## License

MIT
