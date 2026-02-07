"""
SEC EDGAR endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.responses import APIResponse
from app.core.logging_config import get_logger
from app.database.database import get_db
from app.database.models import SECFiling
from app.database.repositories import SECIngestionJobRepository
from app.services.sec.queue import SECFilingQueueProcessor
from app.services.sec.edgar_client import EdgarClient
from app.services.sec.ingestion import SECFilingIngestionService
from app.services.sec.comparator import FilingComparator
from app.services.agent.research_agent import ResearchAgent

logger = get_logger(__name__)

router = APIRouter(prefix="/sec", tags=["sec"])
edgar_client = EdgarClient()
ingestor = SECFilingIngestionService()
comparator = FilingComparator()
agent = ResearchAgent()
queue_processor = SECFilingQueueProcessor()


class SECFilingSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    start: int = Field(0, ge=0)
    count: int = Field(10, ge=1, le=100)
    form_types: Optional[List[str]] = None
    date_from: Optional[str] = Field(None, description="YYYY-MM-DD")
    date_to: Optional[str] = Field(None, description="YYYY-MM-DD")


class SECFilingIngestRequest(BaseModel):
    cik: str = Field(..., min_length=1, max_length=10)
    accession_number: str = Field(..., min_length=10, max_length=25)
    form_type: str = Field(..., min_length=1, max_length=20)
    filed_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    company_name: Optional[str] = Field(None, max_length=255)
    filing_url: Optional[str] = Field(None)


class SECFilingEnqueueRequest(BaseModel):
    cik: str = Field(..., min_length=1, max_length=10)
    accession_number: str = Field(..., min_length=10, max_length=25)
    form_type: str = Field(..., min_length=1, max_length=20)
    filed_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    company_name: Optional[str] = Field(None, max_length=255)
    filing_url: Optional[str] = Field(None)


class SECJobListResponse(BaseModel):
    jobs: List[dict]
    limit: int
    offset: int


class SECResearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    form_types: Optional[List[str]] = None
    date_from: Optional[str] = Field(None, description="YYYY-MM-DD")
    date_to: Optional[str] = Field(None, description="YYYY-MM-DD")
    max_results: int = Field(5, ge=1, le=25)
    include_compare: bool = True


class SECCompareRequest(BaseModel):
    accession_a: str = Field(..., min_length=10, max_length=25)
    accession_b: str = Field(..., min_length=10, max_length=25)
    focus_topic: Optional[str] = Field(None, max_length=2000)
    top_k: int = Field(6, ge=1, le=20)


@router.post("/search", response_model=APIResponse)
async def search_filings(
    request: SECFilingSearchRequest,
    http_request: Request,
):
    request_id = getattr(http_request.state, "request_id", None)
    results = await edgar_client.search_filings(
        query=request.query,
        start=request.start,
        count=request.count,
        form_types=request.form_types,
        date_from=request.date_from,
        date_to=request.date_to,
    )
    return APIResponse(
        success=True,
        data={
            "results": [r.__dict__ for r in results],
            "count": len(results),
        },
        request_id=request_id,
    )


@router.post("/ingest", response_model=APIResponse)
async def ingest_filing(
    request: SECFilingIngestRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    try:
        filing = await ingestor.ingest_filing(
            db=db,
            cik=request.cik,
            accession_number=request.accession_number,
            form_type=request.form_type,
            filed_date=request.filed_date,
            company_name=request.company_name,
            filing_url=request.filing_url,
        )
    except Exception as exc:
        logger.error(f"SEC ingest failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    return APIResponse(
        success=True,
        data={
            "accession_number": filing.accession_number,
            "form_type": filing.form_type,
            "filed_date": filing.filed_date.isoformat() if filing.filed_date else None,
            "document_id": str(filing.document_id) if filing.document_id else None,
            "status": filing.status,
        },
        request_id=request_id,
    )


@router.post("/ingest/queue", response_model=APIResponse)
async def enqueue_filing(
    request: SECFilingEnqueueRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    job = SECIngestionJobRepository.create_job(
        db=db,
        cik=request.cik,
        accession_number=request.accession_number,
        form_type=request.form_type,
        filed_date=request.filed_date,
        company_name=request.company_name,
        filing_url=request.filing_url,
    )
    return APIResponse(
        success=True,
        data={
            "job_id": str(job.id),
            "status": job.status,
        },
        request_id=request_id,
    )


@router.post("/ingest/queue/process-next", response_model=APIResponse)
async def process_next_job(
    http_request: Request,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    processed = await queue_processor.process_next(db=db)
    return APIResponse(
        success=True,
        data={"processed": processed},
        request_id=request_id,
    )


@router.get("/ingest/jobs", response_model=APIResponse)
async def list_ingest_jobs(
    http_request: Request,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    jobs = SECIngestionJobRepository.list_jobs(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )
    return APIResponse(
        success=True,
        data=SECJobListResponse(
            jobs=[
                {
                    "id": str(job.id),
                    "cik": job.cik,
                    "accession_number": job.accession_number,
                    "form_type": job.form_type,
                    "filed_date": job.filed_date.isoformat() if job.filed_date else None,
                    "status": job.status,
                    "attempts": job.attempts,
                    "error_message": job.error_message,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                }
                for job in jobs
            ],
            limit=limit,
            offset=offset,
        ).dict(),
        request_id=request_id,
    )


@router.get("/ingest/jobs/{job_id}", response_model=APIResponse)
async def get_ingest_job(
    job_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    from uuid import UUID

    job = SECIngestionJobRepository.get_job(db=db, job_id=UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return APIResponse(
        success=True,
        data={
            "id": str(job.id),
            "cik": job.cik,
            "accession_number": job.accession_number,
            "form_type": job.form_type,
            "filed_date": job.filed_date.isoformat() if job.filed_date else None,
            "status": job.status,
            "attempts": job.attempts,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        },
        request_id=request_id,
    )


@router.post("/research", response_model=APIResponse)
async def research(
    request: SECResearchRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    result = await agent.run(
        db=db,
        question=request.question,
        form_types=request.form_types,
        date_from=request.date_from,
        date_to=request.date_to,
        max_results=request.max_results,
        include_compare=request.include_compare,
    )
    return APIResponse(success=True, data=result, request_id=request_id)


@router.post("/compare", response_model=APIResponse)
async def compare_filings(
    request: SECCompareRequest,
    http_request: Request,
):
    request_id = getattr(http_request.state, "request_id", None)
    result = await comparator.compare(
        accession_a=request.accession_a,
        accession_b=request.accession_b,
        focus_topic=request.focus_topic,
        top_k=request.top_k,
    )
    return APIResponse(success=True, data=result, request_id=request_id)


@router.get("/filings", response_model=APIResponse)
async def list_indexed_filings(
    http_request: Request,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    request_id = getattr(http_request.state, "request_id", None)
    filings = (
        db.query(SECFiling)
        .order_by(SECFiling.filed_date.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return APIResponse(
        success=True,
        data={
            "filings": [
                {
                    "accession_number": f.accession_number,
                    "form_type": f.form_type,
                    "filed_date": f.filed_date.isoformat() if f.filed_date else None,
                    "document_id": str(f.document_id) if f.document_id else None,
                    "status": f.status,
                }
                for f in filings
            ],
            "limit": limit,
            "offset": offset,
        },
        request_id=request_id,
    )
