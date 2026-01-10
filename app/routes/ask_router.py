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
        # Get LLM client
        llm_client = get_llm_client(provider=request.provider)
        
        # Make request
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
