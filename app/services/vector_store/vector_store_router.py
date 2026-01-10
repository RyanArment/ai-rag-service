"""
Vector store factory/router.
"""
from typing import Optional
from app.services.vector_store.base import BaseVectorStore
from app.services.vector_store.pgvector_store import PgVectorStore
from app.core.config import VECTOR_STORE_PROVIDER
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton vector store instance
_vector_store: Optional[BaseVectorStore] = None


def get_vector_store(provider: Optional[str] = None) -> BaseVectorStore:
    """
    Get or create vector store instance (singleton pattern).
    
    Args:
        provider: Vector store provider ("pgvector" or "chroma")
                  Defaults to VECTOR_STORE_PROVIDER from config
        
    Returns:
        BaseVectorStore instance
    """
    global _vector_store
    
    provider = provider or VECTOR_STORE_PROVIDER
    
    if provider == "pgvector":
        # Return existing if same provider
        if _vector_store and isinstance(_vector_store, PgVectorStore):
            return _vector_store
        
        _vector_store = PgVectorStore()
        logger.info("Initialized PostgreSQL vector store with pgvector")
        
    elif provider == "chroma":
        # Keep ChromaDB as fallback option
        from app.services.vector_store.chroma_store import ChromaVectorStore
        from app.core.config import CHROMA_PERSIST_DIR
        
        if _vector_store and isinstance(_vector_store, ChromaVectorStore):
            return _vector_store
        
        _vector_store = ChromaVectorStore(
            collection_name="documents",
            persist_directory=CHROMA_PERSIST_DIR,
        )
        logger.info("Initialized ChromaDB vector store")
        
    else:
        raise ValueError(f"Unsupported vector store provider: {provider}")
    
    return _vector_store


def reset_vector_store() -> None:
    """Reset the singleton vector store (useful for testing)."""
    global _vector_store
    if _vector_store and hasattr(_vector_store, 'db'):
        _vector_store.db.close()
    _vector_store = None
