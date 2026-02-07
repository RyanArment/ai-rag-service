"""
Database repository layer for database operations.
"""
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import User, Document, DocumentChunk, Query, APIKey, SECIngestionJob
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document operations."""
    
    @staticmethod
    def create_document(
        db: Session,
        filename: str,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        status: str = "processing",
    ) -> Document:
        """Create a new document record."""
        document = Document(
            id=uuid4(),
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            status=status,
            chunks_count=0,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Created document: {document.id}")
        return document
    
    @staticmethod
    def update_document(
        db: Session,
        document_id: UUID,
        status: Optional[str] = None,
        chunks_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        """Update document record."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None
        
        if status:
            document.status = status
        if chunks_count is not None:
            document.chunks_count = chunks_count
        if error_message:
            document.error_message = error_message
        
        db.commit()
        db.refresh(document)
        return document
    
    @staticmethod
    def get_document(db: Session, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        return db.query(Document).filter(Document.id == document_id).first()
    
    @staticmethod
    def list_documents(
        db: Session,
        user_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """List documents."""
        query = db.query(Document)
        if user_id:
            query = query.filter(Document.user_id == user_id)
        return query.order_by(desc(Document.created_at)).limit(limit).offset(offset).all()


class DocumentChunkRepository:
    """Repository for document chunk operations."""
    
    @staticmethod
    def create_chunk(
        db: Session,
        document_id: UUID,
        chunk_index: int,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentChunk:
        """Create a document chunk record with embedding."""
        import json
        chunk = DocumentChunk(
            id=uuid4(),
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            content_preview=content[:200] if content else None,
            embedding=embedding,
            chunk_metadata=json.dumps(metadata) if metadata else None,
        )
        db.add(chunk)
        db.commit()
        db.refresh(chunk)
        return chunk
    
    @staticmethod
    def get_chunks_by_document(
        db: Session,
        document_id: UUID,
    ) -> List[DocumentChunk]:
        """Get all chunks for a document."""
        return (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )
    
    @staticmethod
    def delete_chunks_by_document(db: Session, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        count = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .delete()
        )
        db.commit()
        return count
    
    @staticmethod
    def get_chunk_by_id(db: Session, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk by ID."""
        return db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()


class QueryRepository:
    """Repository for query operations."""
    
    @staticmethod
    def create_query(
        db: Session,
        question: str,
        answer: Optional[str] = None,
        sources_count: int = 0,
        latency_ms: Optional[float] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        tokens_used: Optional[int] = None,
        user_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
    ) -> Query:
        """Create a query record."""
        query = Query(
            id=uuid4(),
            user_id=user_id,
            question=question,
            answer=answer,
            sources_count=sources_count,
            latency_ms=latency_ms,
            model=model,
            provider=provider,
            tokens_used=tokens_used,
            error_message=error_message,
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        logger.info(f"Created query record: {query.id}")
        return query
    
    @staticmethod
    def get_query(db: Session, query_id: UUID) -> Optional[Query]:
        """Get query by ID."""
        return db.query(Query).filter(Query.id == query_id).first()
    
    @staticmethod
    def list_queries(
        db: Session,
        user_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Query]:
        """List queries."""
        query = db.query(Query)
        if user_id:
            query = query.filter(Query.user_id == user_id)
        return query.order_by(desc(Query.created_at)).limit(limit).offset(offset).all()


class SECIngestionJobRepository:
    """Repository for SEC ingestion jobs."""

    @staticmethod
    def create_job(
        db: Session,
        cik: str,
        accession_number: str,
        form_type: str,
        filed_date: Optional[str] = None,
        company_name: Optional[str] = None,
        filing_url: Optional[str] = None,
    ) -> SECIngestionJob:
        """Create a new ingestion job."""
        from datetime import datetime
        filed_date_value = None
        if filed_date:
            try:
                filed_date_value = datetime.fromisoformat(filed_date).date()
            except Exception:
                filed_date_value = None

        job = SECIngestionJob(
            id=uuid4(),
            cik=cik,
            accession_number=accession_number,
            form_type=form_type,
            filed_date=filed_date_value,
            company_name=company_name,
            filing_url=filing_url,
            status="pending",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job(db: Session, job_id: UUID) -> Optional[SECIngestionJob]:
        """Get job by ID."""
        return db.query(SECIngestionJob).filter(SECIngestionJob.id == job_id).first()

    @staticmethod
    def list_jobs(
        db: Session,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SECIngestionJob]:
        """List jobs."""
        query = db.query(SECIngestionJob)
        if status:
            query = query.filter(SECIngestionJob.status == status)
        return query.order_by(desc(SECIngestionJob.created_at)).limit(limit).offset(offset).all()

    @staticmethod
    def claim_next_pending(db: Session) -> Optional[SECIngestionJob]:
        """Claim the next pending job."""
        from datetime import datetime
        job = (
            db.query(SECIngestionJob)
            .filter(SECIngestionJob.status == "pending")
            .order_by(SECIngestionJob.created_at)
            .first()
        )
        if not job:
            return None
        job.status = "running"
        job.attempts = (job.attempts or 0) + 1
        job.started_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def mark_completed(db: Session, job: SECIngestionJob) -> SECIngestionJob:
        """Mark job completed."""
        from datetime import datetime
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def mark_failed(db: Session, job: SECIngestionJob, error_message: str) -> SECIngestionJob:
        """Mark job failed."""
        from datetime import datetime
        job.status = "failed"
        job.error_message = error_message
        job.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return job
