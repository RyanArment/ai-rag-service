"""
Database repository layer for database operations.
"""
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models import User, Document, DocumentChunk, Query, APIKey
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
