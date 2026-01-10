"""
ChromaDB vector store implementation.
"""
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.services.vector_store.base import BaseVectorStore, Document, SearchResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB vector store implementation."""
    
    def __init__(self, collection_name: str = "documents", persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB vector store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data (local storage)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(name=collection_name)
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to ChromaDB."""
        if not documents:
            return []
        
        ids = []
        contents = []
        metadatas = []
        embeddings = []
        
        for doc in documents:
            if not doc.embedding:
                raise ValueError(f"Document {doc.id} missing embedding")
            
            ids.append(doc.id)
            contents.append(doc.content)
            metadatas.append(doc.metadata)
            embeddings.append(doc.embedding)
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
            )
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}", exc_info=True)
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar documents."""
        try:
            where = filter if filter else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
            )
            
            search_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    doc_id = results['ids'][0][i]
                    content = results['documents'][0][i]
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    
                    # Convert distance to similarity score (ChromaDB uses distance, we want similarity)
                    # Distance is typically L2, so similarity = 1 / (1 + distance)
                    score = 1.0 / (1.0 + distance)
                    
                    document = Document(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                    )
                    
                    search_results.append(SearchResult(
                        document=document,
                        score=score,
                    ))
            
            logger.info(f"Found {len(search_results)} results for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}", exc_info=True)
            raise
    
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by IDs."""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
            return True
        except Exception as e:
            logger.error(f"Error deleting documents from ChromaDB: {e}", exc_info=True)
            return False
    
    def get_by_id(self, id: str) -> Optional[Document]:
        """Get a document by ID."""
        try:
            results = self.collection.get(ids=[id])
            
            if results['ids'] and len(results['ids']) > 0:
                content = results['documents'][0]
                metadata = results['metadatas'][0] if results['metadatas'] else {}
                
                return Document(
                    id=id,
                    content=content,
                    metadata=metadata,
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting document from ChromaDB: {e}", exc_info=True)
            return None
    
    def clear(self) -> bool:
        """Clear all documents from the store."""
        try:
            # Delete collection and recreate
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {e}", exc_info=True)
            return False
    
    def count(self) -> int:
        """Get total number of documents."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting documents in ChromaDB: {e}", exc_info=True)
            return 0
