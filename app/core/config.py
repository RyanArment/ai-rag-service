"""
Application configuration and environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_JSON = os.getenv("LOG_JSON", "false").lower() == "true"

# Application Configuration
APP_NAME = os.getenv("APP_NAME", "ai-rag-service")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./rag_service.db" if os.getenv("DEBUG", "false").lower() == "true" 
    else "postgresql://user:password@localhost:5432/ragdb"
)

# Vector Store Configuration
VECTOR_STORE_PROVIDER = os.getenv("VECTOR_STORE_PROVIDER", "pgvector")  # pgvector or chroma
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# SEC EDGAR Configuration
SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "ai-rag-service (contact: dev@example.com)"
)
SEC_RATE_LIMIT_PER_SEC = float(os.getenv("SEC_RATE_LIMIT_PER_SEC", "8"))
SEC_CACHE_DIR = os.getenv("SEC_CACHE_DIR", "./sec_cache")
SEC_WORKER_POLL_SECONDS = float(os.getenv("SEC_WORKER_POLL_SECONDS", "3"))
