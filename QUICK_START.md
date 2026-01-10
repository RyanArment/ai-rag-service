# Quick Start Guide

## What's Been Implemented (Days 1-5)

✅ **Day 1-2**: Basic setup, provider abstraction
✅ **Day 3**: Logging, error handling, unified responses
✅ **Day 4**: Streaming support (SSE)
✅ **Day 5**: Evaluation framework

## Setup

1. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or: venv\Scripts\activate  # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here  # Optional, only if using OpenAI
   LOG_LEVEL=INFO
   LOG_JSON=false
   ```

3. **Run the server:**
   ```bash
   # Make sure venv is activated first
   uvicorn app.main:app --reload
   ```
   
   **Note:** Always activate your virtual environment before running:
   ```bash
   source venv/bin/activate  # macOS/Linux
   ```

4. **Test the API:**
   - Visit http://localhost:8000/docs for interactive docs
   - Or use curl:
     ```bash
     curl -X POST "http://localhost:8000/ask" \
       -H "Content-Type: application/json" \
       -d '{"prompt": "What is Python?"}'
     ```

## Key Files

- `app/main.py` - FastAPI app with middleware and error handling
- `app/routes/ask_router.py` - LLM completion endpoints
- `app/services/llm/base.py` - Base LLM interface
- `app/services/llm/openai_client.py` - OpenAI implementation
- `app/services/llm/anthropic_client.py` - Anthropic implementation
- `app/core/logging_config.py` - Structured logging
- `app/core/exceptions.py` - Custom exceptions
- `app/services/evaluation/` - Evaluation framework

## Next Steps

See `DAY3_PLUS_GUIDE.md` for detailed roadmap (Days 6-30).
