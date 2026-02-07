"""
RAG query endpoints.
"""
import time
from typing import Optional, Dict, Any
from datetime import date
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.rag.pipeline import RAGPipeline
from app.core.config import LLM_PROVIDER
from app.database.database import get_db
from app.database.repositories import QueryRepository
from app.core.responses import APIResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])

# Initialize RAG pipeline
rag_pipeline = RAGPipeline(top_k=5, context_window=4000)


class RAGQueryRequest(BaseModel):
    """Request model for RAG query."""
    question: str = Field(..., min_length=1, max_length=5000, description="User question")
    system_prompt: Optional[str] = Field(None, max_length=2000, description="Optional system prompt")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, le=100000, description="Maximum tokens to generate")
    top_k: Optional[int] = Field(5, gt=0, le=20, description="Number of documents to retrieve")
    form_type: Optional[str] = Field(None, max_length=20, description="SEC form type filter")
    cik: Optional[str] = Field(None, max_length=10, description="CIK filter")
    accession_number: Optional[str] = Field(None, max_length=25, description="Accession number filter")
    filed_date_from: Optional[date] = Field(None, description="Filed date start (YYYY-MM-DD)")
    filed_date_to: Optional[date] = Field(None, description="Filed date end (YYYY-MM-DD)")


@router.post("/query", response_model=APIResponse)
async def rag_query(
    request: RAGQueryRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    RAG query endpoint.
    
    Retrieves relevant context from vector store and generates answer using LLM.
    Logs query to PostgreSQL for analytics.
    """
    request_id = getattr(http_request.state, "request_id", None)
    start_time = time.time()
    
    logger.info(
        "RAG query request",
        extra={
            "request_id": request_id,
            "question_length": len(request.question),
            "top_k": request.top_k,
        }
    )
    
    query_record = None
    try:
        # Override top_k if provided
        if request.top_k:
            rag_pipeline.top_k = request.top_k
        
        # Execute RAG pipeline
        filter: Dict[str, Any] = {}
        if request.form_type:
            filter["form_type"] = request.form_type
        if request.cik:
            filter["cik"] = request.cik
        if request.accession_number:
            filter["accession_number"] = request.accession_number
        if request.filed_date_from:
            filter["filed_date_from"] = request.filed_date_from
        if request.filed_date_to:
            filter["filed_date_to"] = request.filed_date_to
        if filter:
            filter["source_type"] = "sec_filing"

        requested_provider = http_request.headers.get("X-LLM-Provider")
        llm_provider = requested_provider if requested_provider in {"openai", "anthropic"} else LLM_PROVIDER
        openai_key = http_request.headers.get("X-OpenAI-Key")
        anthropic_key = http_request.headers.get("X-Anthropic-Key")
        llm_api_key = openai_key if llm_provider == "openai" else anthropic_key

        result = await rag_pipeline.query_async(
            question=request.question,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            filter=filter if filter else None,
            llm_provider=llm_provider,
            llm_api_key=llm_api_key,
            embedding_api_key=openai_key,
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract token usage
        tokens_used = None
        if result.get("usage"):
            if isinstance(result["usage"], dict):
                tokens_used = result["usage"].get("total_tokens") or result["usage"].get("output_tokens")
        
        # Log query to PostgreSQL
        query_record = QueryRepository.create_query(
            db=db,
            question=request.question,
            answer=result.get("answer"),
            sources_count=len(result.get("sources", [])),
            latency_ms=latency_ms,
            model=result.get("model"),
            provider=result.get("provider"),
            tokens_used=tokens_used,
        )
        
        logger.info(
            "RAG query successful",
            extra={
                "request_id": request_id,
                "query_id": str(query_record.id),
                "sources_retrieved": len(result["sources"]),
                "latency_ms": latency_ms,
            }
        )
        
        return APIResponse(
            success=True,
            data={
                **result,
                "latency_ms": latency_ms,
                "query_id": str(query_record.id),  # Include query ID in response
            },
            request_id=request_id,
        )
        
    except Exception as e:
        # Log failed query
        try:
            QueryRepository.create_query(
                db=db,
                question=request.question,
                answer=None,
                sources_count=0,
                latency_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )
        except:
            pass
        
        logger.error(
            f"RAG query failed: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise
