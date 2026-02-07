"""
RAG Pipeline: Retrieval-Augmented Generation.
"""
from typing import List, Optional, Dict, Any
from app.services.embeddings.embedding_router import get_embedding_model
from app.services.vector_store.vector_store_router import get_vector_store
from app.services.llm_router import get_llm_client
from app.services.vector_store.base import SearchResult
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RAGPipeline:
    """RAG pipeline that combines retrieval and generation."""
    
    def __init__(
        self,
        top_k: int = 5,
        context_window: int = 4000,
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            top_k: Number of documents to retrieve
            context_window: Maximum context length for LLM
        """
        self.top_k = top_k
        self.context_window = context_window
    
    def query(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Execute RAG query: retrieve context and generate answer.
        
        Args:
            question: User question
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with answer, context, and metadata
        """
        # Step 1: Generate query embedding
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.embed(question)
        
        # Step 2: Retrieve relevant documents
        vector_store = get_vector_store()
        search_results = vector_store.search(
            query_embedding=query_embedding,
            top_k=self.top_k,
            filter=filter,
        )
        
        # Step 3: Build context from retrieved documents
        context_chunks = []
        total_length = 0
        
        for result in search_results:
            chunk_text = result.document.content
            chunk_length = len(chunk_text)
            
            if total_length + chunk_length > self.context_window:
                break
            
            context_chunks.append(chunk_text)
            total_length += chunk_length
        
        context = "\n\n".join(context_chunks)
        
        # Step 4: Build prompt with context
        if system_prompt:
            prompt = f"""{system_prompt}

Context:
{context}

Question: {question}

Answer:"""
        else:
            prompt = f"""Use the following context to answer the question. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        # Step 5: Generate answer using LLM
        llm_client = get_llm_client()
        response = llm_client.ask(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return {
            "answer": response.content,
            "context": context_chunks,
            "sources": [
                {
                    "content": result.document.content,
                    "score": result.score,
                    "metadata": result.document.metadata,
                }
                for result in search_results[:len(context_chunks)]
            ],
            "model": response.model,
            "provider": response.provider,
            "usage": response.usage,
        }
    
    async def query_async(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Async version of query()."""
        # Step 1: Generate query embedding
        embedding_model = get_embedding_model()
        query_embedding = await embedding_model.embed_async(question)
        
        # Step 2: Retrieve relevant documents
        vector_store = get_vector_store()
        search_results = vector_store.search(
            query_embedding=query_embedding,
            top_k=self.top_k,
            filter=filter,
        )
        
        # Step 3: Build context
        context_chunks = []
        total_length = 0
        
        for result in search_results:
            chunk_text = result.document.content
            chunk_length = len(chunk_text)
            
            if total_length + chunk_length > self.context_window:
                break
            
            context_chunks.append(chunk_text)
            total_length += chunk_length
        
        context = "\n\n".join(context_chunks)
        
        # Step 4: Build prompt
        if system_prompt:
            prompt = f"""{system_prompt}

Context:
{context}

Question: {question}

Answer:"""
        else:
            prompt = f"""Use the following context to answer the question. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        # Step 5: Generate answer
        llm_client = get_llm_client()
        response = await llm_client.ask_async(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return {
            "answer": response.content,
            "context": context_chunks,
            "sources": [
                {
                    "content": result.document.content,
                    "score": result.score,
                    "metadata": result.document.metadata,
                }
                for result in search_results[:len(context_chunks)]
            ],
            "model": response.model,
            "provider": response.provider,
            "usage": response.usage,
        }
