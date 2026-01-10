# Day 1 & Day 2: Foundation & Provider Abstraction

This guide explains exactly what was built in Days 1-2, with all code snippets included.

---

## Day 1: Project Setup & Basic Structure

### Goal
Set up a FastAPI project structure and create basic configuration management.

### What We Built

#### 1. Project Structure

We created this directory structure:

```
app/
├── main.py                    # FastAPI app entry point
├── core/
│   └── config.py             # Configuration management
├── routes/
│   └── ask_router.py         # API endpoints
└── services/
    └── llm_router.py         # LLM client factory
```

#### 2. Configuration File (`app/core/config.py`)

**Purpose:** Centralized configuration management using environment variables.

**Complete Code:**

```python
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
```

**What it does:**
- Loads environment variables from `.env` file
- Provides defaults for all configuration values
- Centralizes all config in one place

#### 3. Basic FastAPI App (`app/main.py`)

**Purpose:** Create the FastAPI application instance.

**Complete Code:**

```python
"""
FastAPI application entry point.
"""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import APP_NAME, APP_VERSION, DEBUG, LOG_LEVEL, LOG_JSON
from app.core.logging_config import setup_logging, get_logger
from app.core.exceptions import RAGServiceError
from app.routes import ask_router

# Setup logging first
setup_logging(log_level=LOG_LEVEL, json_output=LOG_JSON)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    yield
    # Shutdown
    logger.info(f"Shutting down {APP_NAME}")


# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(RAGServiceError)
async def rag_service_error_handler(request: Request, exc: RAGServiceError):
    """Handle custom RAG service errors."""
    logger.error(
        f"RAG service error: {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "status_code": exc.status_code,
            "details": exc.details,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": getattr(request.state, "request_id", None),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "Internal server error",
                "details": {"error_type": type(exc).__name__} if DEBUG else {},
            },
            "request_id": request_id,
        }
    )


# Include routers
app.include_router(ask_router.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
    }
```

**What it does:**
- Creates FastAPI app instance
- Sets up CORS middleware
- Adds request ID middleware for tracing
- Registers exception handlers
- Includes routers
- Provides health check endpoint

---

## Day 2: Provider Abstraction Pattern

### Goal
Create a clean abstraction layer that allows switching between LLM providers (OpenAI, Anthropic) without changing application code.

### Key Design Pattern: Strategy Pattern + Abstract Base Class

We use Python's `ABC` (Abstract Base Class) to define a contract that all providers must follow.

---

### Step 1: Base LLM Interface (`app/services/llm/base.py`)

**Purpose:** Define the contract that all LLM providers must implement.

**Complete Code:**

```python
"""
Base LLM client interface for provider abstraction.
This ensures all providers implement the same contract.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Standardized message format across providers."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Unified response schema for all LLM providers."""
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None  # tokens, cost, etc.
    finish_reason: Optional[str] = None


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__.replace("Client", "").lower()
    
    @abstractmethod
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Synchronous completion request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with standardized format
        """
        pass
    
    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """
        Streaming completion request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of text as they're generated
        """
        pass
    
    @abstractmethod
    async def ask_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Async version of ask()."""
        pass
    
    @abstractmethod
    async def stream_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Async version of stream()."""
        pass
```

**Key Points:**
- `@abstractmethod` decorator ensures all subclasses must implement these methods
- `LLMResponse` provides a unified response format regardless of provider
- All providers must support sync/async and streaming

---

### Step 2: OpenAI Implementation (`app/services/llm/openai_client.py`)

**Purpose:** Implement OpenAI's API using our base interface.

**Complete Code:**

```python
"""
OpenAI LLM client implementation.
"""
import time
from typing import Optional, Iterator, AsyncIterator
from openai import OpenAI, AsyncOpenAI
from openai import APIError as OpenAIAPIError

from app.services.llm.base import BaseLLMClient, LLMResponse
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
    
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Synchronous completion."""
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
            )
        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error: {e}", extra={"provider": "openai", "error": str(e)})
            raise LLMProviderError(
                f"OpenAI API error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI client: {e}", exc_info=True)
            raise LLMProviderError(
                f"Unexpected error: {str(e)}",
                provider="openai",
                details={"error_type": type(e).__name__}
            )
    
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Streaming completion."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIAPIError as e:
            logger.error(f"OpenAI streaming error: {e}", extra={"provider": "openai"})
            raise LLMProviderError(
                f"OpenAI streaming error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
    
    async def ask_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Async completion."""
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
            )
        except OpenAIAPIError as e:
            logger.error(f"OpenAI async API error: {e}", extra={"provider": "openai"})
            raise LLMProviderError(
                f"OpenAI API error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
    
    async def stream_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Async streaming completion."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIAPIError as e:
            logger.error(f"OpenAI async streaming error: {e}", extra={"provider": "openai"})
            raise LLMProviderError(
                f"OpenAI streaming error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
```

**Key Points:**
- Inherits from `BaseLLMClient` (must implement all abstract methods)
- Converts OpenAI's response format to our `LLMResponse` format
- Handles errors and converts them to our `LLMProviderError`
- Supports both sync and async operations

---

### Step 3: Anthropic Implementation (`app/services/llm/anthropic_client.py`)

**Purpose:** Implement Anthropic's API using the same base interface.

**Complete Code:**

```python
"""
Anthropic LLM client implementation.
"""
import time
from typing import Optional, Iterator, AsyncIterator
from anthropic import Anthropic, AsyncAnthropic
from anthropic import APIError as AnthropicAPIError

from app.services.llm.base import BaseLLMClient, LLMResponse
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic LLM client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
    
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Synchronous completion."""
        start_time = time.time()
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None,
                finish_reason=response.stop_reason,
            )
        except AnthropicAPIError as e:
            logger.error(f"Anthropic API error: {e}", extra={"provider": "anthropic", "error": str(e)})
            raise LLMProviderError(
                f"Anthropic API error: {str(e)}",
                provider="anthropic",
                status_code=getattr(e, "status_code", 500),
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic client: {e}", exc_info=True)
            raise LLMProviderError(
                f"Unexpected error: {str(e)}",
                provider="anthropic",
                details={"error_type": type(e).__name__}
            )
    
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Streaming completion."""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            with self.client.messages.stream(**kwargs) as stream:
                for text_event in stream.text_stream:
                    yield text_event
        except AnthropicAPIError as e:
            logger.error(f"Anthropic streaming error: {e}", extra={"provider": "anthropic"})
            raise LLMProviderError(
                f"Anthropic streaming error: {str(e)}",
                provider="anthropic",
                status_code=getattr(e, "status_code", 500),
            )
    
    async def ask_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Async completion."""
        start_time = time.time()
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self.async_client.messages.create(**kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None,
                finish_reason=response.stop_reason,
            )
        except AnthropicAPIError as e:
            logger.error(f"Anthropic async API error: {e}", extra={"provider": "anthropic"})
            raise LLMProviderError(
                f"Anthropic API error: {str(e)}",
                provider="anthropic",
                status_code=getattr(e, "status_code", 500),
            )
    
    async def stream_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Async streaming completion."""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            async with self.async_client.messages.stream(**kwargs) as stream:
                async for text_event in stream.text_stream:
                    yield text_event
        except AnthropicAPIError as e:
            logger.error(f"Anthropic async streaming error: {e}", extra={"provider": "anthropic"})
            raise LLMProviderError(
                f"Anthropic streaming error: {str(e)}",
                provider="anthropic",
                status_code=getattr(e, "status_code", 500),
            )
```

**Key Differences from OpenAI:**
- Anthropic uses `messages.create()` instead of `chat.completions.create()`
- System prompt is passed as a separate `system` parameter, not in messages
- Response structure is different (`response.content[0].text` vs `response.choices[0].message.content`)
- Usage tokens are `input_tokens` and `output_tokens` instead of `prompt_tokens` and `completion_tokens`

**But:** Both return the same `LLMResponse` format, so the rest of the application doesn't need to know which provider is being used!

---

### Step 4: LLM Router Factory (`app/services/llm_router.py`)

**Purpose:** Factory pattern to create and manage LLM client instances (singleton pattern).

**Complete Code:**

```python
"""
LLM Router - Factory for creating and managing LLM clients.
"""
from typing import Optional
from app.core.config import LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY
from app.services.llm.openai_client import OpenAIClient
from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm.base import BaseLLMClient
from app.core.exceptions import ConfigurationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton client instance
_llm_client: Optional[BaseLLMClient] = None


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """
    Get or create LLM client instance (singleton pattern).
    
    Args:
        provider: Override default provider from config
        
    Returns:
        BaseLLMClient instance
        
    Raises:
        ConfigurationError: If provider or API key is missing
    """
    global _llm_client
    
    provider = provider or LLM_PROVIDER
    
    # Return existing client if provider matches
    if _llm_client and _llm_client.provider_name == provider:
        return _llm_client
    
    # Create new client
    if provider == "openai":
        if not OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY not found in environment variables",
                details={"provider": "openai"}
            )
        _llm_client = OpenAIClient(api_key=OPENAI_API_KEY)
        logger.info("Initialized OpenAI client", extra={"provider": "openai", "model": _llm_client.model})
        
    elif provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY not found in environment variables",
                details={"provider": "anthropic"}
            )
        _llm_client = AnthropicClient(api_key=ANTHROPIC_API_KEY)
        logger.info("Initialized Anthropic client", extra={"provider": "anthropic", "model": _llm_client.model})
        
    else:
        raise ConfigurationError(
            f"Unsupported LLM provider: {provider}",
            details={"supported_providers": ["openai", "anthropic"]}
        )
    
    return _llm_client


def reset_client() -> None:
    """Reset the singleton client (useful for testing)."""
    global _llm_client
    _llm_client = None
```

**Key Points:**
- **Singleton Pattern:** Only creates one client instance, reuses it
- **Factory Pattern:** Creates the right client based on provider name
- **Validation:** Checks API keys exist before creating clients
- **Flexible:** Can override default provider per request

---

### Step 5: API Route (`app/routes/ask_router.py`)

**Purpose:** HTTP endpoint that uses the LLM client without knowing which provider.

**Complete Code:**

```python
"""
LLM completion endpoints.
"""
import time
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.llm_router import get_llm_client
from app.core.responses import APIResponse, LLMCompletionResponse, StreamingChunk
from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    """Request model for LLM completion."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="User prompt")
    system_prompt: Optional[str] = Field(None, max_length=5000, description="Optional system prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, le=100000, description="Maximum tokens to generate")
    provider: Optional[str] = Field(None, description="Override default LLM provider")
    stream: bool = Field(False, description="Enable streaming response")


@router.post("", response_model=APIResponse)
async def ask(request: AskRequest, http_request: Request):
    """
    LLM completion endpoint (non-streaming).
    
    Returns standardized API response with LLM completion.
    """
    request_id = getattr(http_request.state, "request_id", None)
    start_time = time.time()
    
    logger.info(
        "LLM completion request",
        extra={
            "request_id": request_id,
            "provider": request.provider,
            "stream": request.stream,
            "prompt_length": len(request.prompt),
        }
    )
    
    try:
        # Get LLM client (doesn't matter if OpenAI or Anthropic!)
        llm_client = get_llm_client(provider=request.provider)
        
        # Make request - same code works for both providers!
        response = llm_client.ask(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "LLM completion successful",
            extra={
                "request_id": request_id,
                "provider": response.provider,
                "model": response.model,
                "latency_ms": latency_ms,
                "usage": response.usage,
            }
        )
        
        return APIResponse(
            success=True,
            data=LLMCompletionResponse(
                content=response.content,
                model=response.model,
                provider=response.provider,
                usage=response.usage,
                finish_reason=response.finish_reason,
                latency_ms=latency_ms,
            ).dict(),
            request_id=request_id,
        )
        
    except Exception as e:
        logger.error(
            f"LLM completion failed: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise


@router.post("/stream")
async def ask_stream(request: AskRequest, http_request: Request):
    """
    LLM completion endpoint with streaming.
    
    Returns Server-Sent Events (SSE) stream of text chunks.
    """
    request_id = getattr(http_request.state, "request_id", None)
    
    logger.info(
        "LLM streaming request",
        extra={
            "request_id": request_id,
            "provider": request.provider,
            "prompt_length": len(request.prompt),
        }
    )
    
    try:
        # Get LLM client
        llm_client = get_llm_client(provider=request.provider)
        
        # Streaming generator
        async def generate():
            try:
                model_name = None
                provider_name = None
                
                async for chunk in llm_client.stream_async(
                    prompt=request.prompt,
                    system_prompt=request.system_prompt,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                ):
                    if model_name is None:
                        model_name = llm_client.model
                        provider_name = llm_client.provider_name
                    
                    chunk_data = StreamingChunk(
                        content=chunk,
                        done=False,
                        model=model_name,
                        provider=provider_name,
                    )
                    yield f"data: {chunk_data.json()}\n\n"
                
                # Final chunk
                final_chunk = StreamingChunk(
                    content="",
                    done=True,
                    model=model_name,
                    provider=provider_name,
                )
                yield f"data: {final_chunk.json()}\n\n"
                
            except Exception as e:
                logger.error(
                    f"Streaming error: {str(e)}",
                    extra={"request_id": request_id},
                    exc_info=True
                )
                error_chunk = StreamingChunk(
                    content=f"Error: {str(e)}",
                    done=True,
                )
                yield f"data: {error_chunk.json()}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id or "",
            }
        )
        
    except Exception as e:
        logger.error(
            f"Streaming request failed: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise
```

**Key Points:**
- The route code doesn't know or care which provider is being used
- Calls `get_llm_client()` which returns the right client
- Uses `llm_client.ask()` - same method for both providers
- Returns standardized response format

---

## Summary: What We Achieved

### Day 1 Achievements:
1. ✅ Project structure with clear separation of concerns
2. ✅ Configuration management with environment variables
3. ✅ Basic FastAPI app with middleware and error handling

### Day 2 Achievements:
1. ✅ **Provider Abstraction:** Base class defines contract
2. ✅ **OpenAI Implementation:** Converts OpenAI API to our format
3. ✅ **Anthropic Implementation:** Converts Anthropic API to our format
4. ✅ **Factory Pattern:** Router creates the right client
5. ✅ **Unified Interface:** Application code doesn't know which provider is used

### Key Design Patterns Used:

1. **Strategy Pattern:** Different providers (strategies) can be swapped
2. **Abstract Base Class:** Ensures all providers implement the same interface
3. **Factory Pattern:** Router creates appropriate client instances
4. **Singleton Pattern:** Only one client instance per provider

### Benefits:

- ✅ **Easy to add new providers:** Just implement `BaseLLMClient`
- ✅ **No code changes needed:** Switch providers via config
- ✅ **Consistent responses:** Same format regardless of provider
- ✅ **Testable:** Can mock `BaseLLMClient` for testing
- ✅ **Type-safe:** Type hints ensure correctness

---

## How to Use

### Switch Providers:

**Option 1: Environment Variable**
```bash
# In .env file
LLM_PROVIDER=anthropic  # or "openai"
```

**Option 2: Per Request**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello",
    "provider": "anthropic"
  }'
```

The application code doesn't change - the abstraction handles everything!
