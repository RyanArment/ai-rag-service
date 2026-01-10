"""
Base vector store interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class Document(BaseModel):
    """Document with metadata for vector storage."""
    id: str
    content: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    """Search result from vector store."""
    document: Document
    score: float


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects with embeddings
            
        Returns:
            List of document IDs that were added
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Document]:
        """Get a document by ID."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all documents from the store."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total number of documents in the store."""
        pass
