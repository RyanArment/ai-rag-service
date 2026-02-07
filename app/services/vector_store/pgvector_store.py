"""
PostgreSQL + pgvector vector store implementation.
"""
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from pgvector.sqlalchemy import Vector

from app.services.vector_store.base import BaseVectorStore, Document, SearchResult
from app.database.models import DocumentChunk as DocumentChunkModel
from app.database.database import SessionLocal
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PgVectorStore(BaseVectorStore):
    """PostgreSQL + pgvector vector store implementation."""
    
    def __init__(self):
        """Initialize PostgreSQL vector store."""
        self.db = SessionLocal()
        logger.info("Initialized PostgreSQL vector store with pgvector")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to PostgreSQL."""
        if not documents:
            return []
        
        ids = []
        try:
            for doc in documents:
                if not doc.embedding:
                    raise ValueError(f"Document {doc.id} missing embedding")
                
                # Parse document_id from metadata or use doc.id
                document_id = doc.metadata.get("document_id") if doc.metadata else None
                chunk_index = doc.metadata.get("chunk_index", 0) if doc.metadata else 0
                
                if not document_id:
                    raise ValueError(f"Document {doc.id} missing document_id in metadata")
                
                from uuid import UUID
                doc_uuid = UUID(document_id)
                
                # Create chunk record
                filed_date = None
                if doc.metadata:
                    filed_date_value = doc.metadata.get("filed_date")
                    if filed_date_value:
                        try:
                            if hasattr(filed_date_value, "date"):
                                filed_date = filed_date_value
                            else:
                                from datetime import datetime
                                filed_date = datetime.fromisoformat(str(filed_date_value)).date()
                        except Exception:
                            filed_date = None

                chunk = DocumentChunkModel(
                    id=UUID(doc.id) if self._is_uuid(doc.id) else None,
                    document_id=doc_uuid,
                    chunk_index=chunk_index,
                    content=doc.content,
                    content_preview=doc.content[:200] if doc.content else None,
                    embedding=doc.embedding,
                    chunk_metadata=json.dumps(doc.metadata) if doc.metadata else None,
                    source_type=doc.metadata.get("source_type") if doc.metadata else None,
                    form_type=doc.metadata.get("form_type") if doc.metadata else None,
                    cik=doc.metadata.get("cik") if doc.metadata else None,
                    accession_number=doc.metadata.get("accession_number") if doc.metadata else None,
                    filed_date=filed_date,
                    filing_section=doc.metadata.get("filing_section") if doc.metadata else None,
                )
                
                self.db.add(chunk)
                ids.append(doc.id)
            
            self.db.commit()
            logger.info(f"Added {len(documents)} documents to PostgreSQL vector store")
            return ids
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding documents to PostgreSQL: {e}", exc_info=True)
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents using pgvector."""
        try:
            # Build query
            query = self.db.query(
                DocumentChunkModel,
                func.cosine_distance(
                    DocumentChunkModel.embedding,
                    query_embedding
                ).label('distance')
            )
            
            # Apply filters if provided
            if filter:
                if 'document_id' in filter:
                    from uuid import UUID
                    query = query.filter(DocumentChunkModel.document_id == UUID(filter['document_id']))
                if 'source_type' in filter:
                    query = query.filter(DocumentChunkModel.source_type == filter['source_type'])
                if 'form_type' in filter:
                    query = query.filter(DocumentChunkModel.form_type == filter['form_type'])
                if 'cik' in filter:
                    query = query.filter(DocumentChunkModel.cik == filter['cik'])
                if 'accession_number' in filter:
                    query = query.filter(DocumentChunkModel.accession_number == filter['accession_number'])
                if 'filed_date_from' in filter:
                    query = query.filter(DocumentChunkModel.filed_date >= filter['filed_date_from'])
                if 'filed_date_to' in filter:
                    query = query.filter(DocumentChunkModel.filed_date <= filter['filed_date_to'])
            
            # Order by distance and limit
            results = query.order_by('distance').limit(top_k).all()
            
            search_results = []
            for chunk, distance in results:
                # Convert distance to similarity score (1 - distance)
                score = 1.0 - float(distance)
                
                # Parse metadata
                metadata = {}
                if chunk.chunk_metadata:
                    try:
                        metadata = json.loads(chunk.chunk_metadata)
                    except:
                        pass
                
                document = Document(
                    id=str(chunk.id),
                    content=chunk.content,
                    metadata=metadata,
                )
                
                search_results.append(SearchResult(
                    document=document,
                    score=score,
                ))
            
            logger.info(f"Found {len(search_results)} results for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching PostgreSQL: {e}", exc_info=True)
            raise
    
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs."""
        try:
            from uuid import UUID
            
            uuid_ids = []
            for id_str in ids:
                try:
                    uuid_ids.append(UUID(id_str))
                except ValueError:
                    # If not UUID, try to find by content or other means
                    pass
            
            if uuid_ids:
                count = self.db.query(DocumentChunkModel).filter(
                    DocumentChunkModel.id.in_(uuid_ids)
                ).delete(synchronize_session=False)
                self.db.commit()
                logger.info(f"Deleted {count} documents from PostgreSQL vector store")
            
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting documents from PostgreSQL: {e}", exc_info=True)
            return False
    
    def get_by_id(self, id: str) -> Optional[Document]:
        """Get a document by ID."""
        try:
            from uuid import UUID
            chunk = self.db.query(DocumentChunkModel).filter(
                DocumentChunkModel.id == UUID(id)
            ).first()
            
            if chunk:
                metadata = {}
                if chunk.chunk_metadata:
                    try:
                        metadata = json.loads(chunk.chunk_metadata)
                    except:
                        pass
                
                return Document(
                    id=str(chunk.id),
                    content=chunk.content,
                    metadata=metadata,
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting document from PostgreSQL: {e}", exc_info=True)
            return None
    
    def clear(self) -> bool:
        """Clear all documents from the store."""
        try:
            count = self.db.query(DocumentChunkModel).delete()
            self.db.commit()
            logger.info(f"Cleared {count} documents from PostgreSQL vector store")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing PostgreSQL vector store: {e}", exc_info=True)
            return False
    
    def count(self) -> int:
        """Get total number of documents."""
        try:
            return self.db.query(DocumentChunkModel).count()
        except Exception as e:
            logger.error(f"Error counting documents in PostgreSQL: {e}", exc_info=True)
            return 0
    
    def _is_uuid(self, value: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            from uuid import UUID
            UUID(value)
            return True
        except ValueError:
            return False
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
