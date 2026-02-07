"""
Document upload and management endpoints.
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Form, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.document_processor.parsers import parse_document
from app.services.document_processor.processor import DocumentProcessor, DocumentChunk
from app.services.embeddings.embedding_router import get_embedding_model
from app.services.vector_store.vector_store_router import get_vector_store
from app.services.vector_store.base import Document as VectorDocument
from app.database.database import get_db
from app.database.repositories import DocumentRepository, DocumentChunkRepository
from app.core.responses import APIResponse
from app.core.config import MAX_UPLOAD_SIZE_MB
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}


def _validate_upload(filename: str, content_type: Optional[str], content: bytes) -> None:
    extension = (filename or "").lower()
    ext = None
    if "." in extension:
        ext = extension[extension.rfind("."):]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    if ext == ".pdf" or (content_type and "pdf" in content_type.lower()):
        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Invalid PDF file")
    else:
        # Basic binary check for text/markdown
        if b"\x00" in content[:1024]:
            raise HTTPException(status_code=400, detail="Invalid text file")

# Initialize document processor
document_processor = DocumentProcessor(
    chunk_size=1000,
    chunk_overlap=200,
    chunk_strategy="sentence",
)


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    document_id: str
    chunks_created: int
    total_chunks: int
    metadata: dict


@router.post("/upload", response_model=APIResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(1000),
    chunk_overlap: Optional[int] = Form(200),
    http_request: Request = None,
    db: Session = Depends(get_db),
):
    """
    Upload and process a document.
    
    Supports: PDF, TXT, MD files
    Stores metadata in PostgreSQL and embeddings in ChromaDB.
    """
    request_id = getattr(http_request.state, "request_id", None) if http_request else None
    
    logger.info(
        "Document upload request",
        extra={
            "request_id": request_id,
            "filename": file.filename,
            "content_type": file.content_type,
        }
    )
    
    # Create document record in PostgreSQL
    db_document = None
    try:
        # Read file content with size limit
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large")
        _validate_upload(file.filename, file.content_type, content)
        
        # Parse document
        text_content = parse_document(file_path=file.filename, content=content)
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Document appears to be empty")
        
        # Extract metadata
        metadata = document_processor.extract_metadata(
            file_path=file.filename,
            content=text_content,
        )
        metadata["upload_filename"] = file.filename
        metadata["content_type"] = file.content_type
        
        # Create document record in PostgreSQL
        db_document = DocumentRepository.create_document(
            db=db,
            filename=file.filename,
            file_size=len(content),
            file_type=file.content_type,
            status="processing",
        )
        
        # Process into chunks
        processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_strategy="sentence",
        )
        chunks = processor.process_text(text_content, metadata=metadata)
        
        # Generate embeddings
        embedding_model = get_embedding_model()
        texts = [chunk.content for chunk in chunks]
        embeddings = embedding_model.embed(texts)
        
        # Create vector documents with embeddings
        vector_documents = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{db_document.id}_chunk_{i}"
            vector_doc = VectorDocument(
                id=chunk_id,
                content=chunk.content,
                metadata={**chunk.metadata, "document_id": str(db_document.id), "chunk_index": i},
                embedding=embedding,
            )
            vector_documents.append(vector_doc)
        
        # Store in vector database (PostgreSQL with pgvector)
        vector_store = get_vector_store()
        vector_store.add_documents(vector_documents)
        
        # Update document status and chunk count
        DocumentRepository.update_document(
            db=db,
            document_id=db_document.id,
            status="completed",
            chunks_count=len(chunks),
        )
        
        logger.info(
            "Document uploaded successfully",
            extra={
                "request_id": request_id,
                "document_id": str(db_document.id),
                "chunks_created": len(chunks),
            }
        )
        
        return APIResponse(
            success=True,
            data=DocumentUploadResponse(
                document_id=str(db_document.id),
                chunks_created=len(chunks),
                total_chunks=len(chunks),
                metadata=metadata,
            ).dict(),
            request_id=request_id,
        )
        
    except Exception as e:
        # Update document status to failed
        if db_document:
            try:
                DocumentRepository.update_document(
                    db=db,
                    document_id=db_document.id,
                    status="failed",
                    error_message=str(e),
                )
            except:
                pass
        
        logger.error(
            f"Document upload failed: {str(e)}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/count", response_model=APIResponse)
async def get_document_count(
    http_request: Request,
    db: Session = Depends(get_db),
):
    """Get total number of documents and chunks."""
    request_id = getattr(http_request.state, "request_id", None)
    
    try:
        # Get counts from PostgreSQL
        from sqlalchemy import func
        from app.database.models import Document, DocumentChunk
        
        doc_count = db.query(func.count(Document.id)).scalar() or 0
        chunk_count = db.query(func.count(DocumentChunk.id)).scalar() or 0
        
        # Also get vector store count for comparison
        vector_store = get_vector_store()
        vector_count = vector_store.count()
        
        return APIResponse(
            success=True,
            data={
                "documents": doc_count,
                "chunks_postgres": chunk_count,
                "chunks_vector_store": vector_count,
            },
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"Error getting document count: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=APIResponse)
async def list_documents(
    http_request: Request,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List uploaded documents."""
    request_id = getattr(http_request.state, "request_id", None)
    
    try:
        documents = DocumentRepository.list_documents(
            db=db,
            limit=limit,
            offset=offset,
        )
        
        return APIResponse(
            success=True,
            data={
                "documents": [
                    {
                        "id": str(doc.id),
                        "filename": doc.filename,
                        "file_size": doc.file_size,
                        "file_type": doc.file_type,
                        "status": doc.status,
                        "chunks_count": doc.chunks_count,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    }
                    for doc in documents
                ],
                "limit": limit,
                "offset": offset,
            },
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(
    document_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """
    Delete a document and all its chunks.
    
    Note: This deletes metadata from PostgreSQL and chunks from ChromaDB.
    """
    request_id = getattr(http_request.state, "request_id", None)
    
    logger.info(
        "Document deletion request",
        extra={"request_id": request_id, "document_id": document_id}
    )
    
    try:
        from uuid import UUID
        doc_uuid = UUID(document_id)
        
        # Get document
        document = DocumentRepository.get_document(db=db, document_id=doc_uuid)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get all chunk IDs
        chunks = DocumentChunkRepository.get_chunks_by_document(db=db, document_id=doc_uuid)
        chunk_ids = [chunk.vector_chunk_id for chunk in chunks]
        
        # Delete from vector store
        if chunk_ids:
            vector_store = get_vector_store()
            vector_store.delete(chunk_ids)
        
        # Delete chunks from PostgreSQL
        DocumentChunkRepository.delete_chunks_by_document(db=db, document_id=doc_uuid)
        
        # Delete document from PostgreSQL
        db.delete(document)
        db.commit()
        
        logger.info(f"Deleted document: {document_id}")
        
        return APIResponse(
            success=True,
            data={"message": f"Document {document_id} deleted successfully"},
            request_id=request_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
