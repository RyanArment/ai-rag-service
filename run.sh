#!/bin/bash
# Quick start script for the AI RAG Service

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
