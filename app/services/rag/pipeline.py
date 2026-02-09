"""
RAG Pipeline: Retrieval-Augmented Generation.
"""
from typing import List, Optional, Dict, Any
from app.services.embeddings.embedding_router import get_embedding_model
from app.services.vector_store.vector_store_router import get_vector_store
from app.services.llm_router import get_llm_client
from app.services.vector_store.base import SearchResult
from app.core.logging_config import get_logger
from app.core.config import OPENAI_API_KEY, EMBEDDING_PROVIDER

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
        llm_provider: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
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
        # Step 1: Generate query embedding (optional)
        search_results: List[SearchResult] = []
        embedding_provider = EMBEDDING_PROVIDER
        embedding_key = embedding_api_key or OPENAI_API_KEY if embedding_provider == "openai" else None
        if embedding_provider != "openai" or embedding_key:
            embedding_model = get_embedding_model(provider=embedding_provider, api_key=embedding_key)
            query_embedding = embedding_model.embed(question)
            
            # Step 2: Retrieve relevant documents
            vector_store = get_vector_store()
            search_results = vector_store.search(
                query_embedding=query_embedding,
                top_k=self.top_k,
                filter=filter,
            )
        else:
            logger.info("Skipping retrieval; no embedding key available")
        
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
        if context_chunks:
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
        else:
            if system_prompt:
                prompt = f"""{system_prompt}

Question: {question}

Answer:"""
            else:
                prompt = f"""Answer the question as best you can.

Question: {question}

Answer:"""
        
        # Step 5: Generate answer using LLM
        llm_client = get_llm_client(provider=llm_provider, api_key=llm_api_key)
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
        llm_provider: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        embedding_api_key: Optional[str] = None,
    ) -> dict:
        """Async version of query()."""
        # Step 1: Generate query embedding (optional)
        search_results: List[SearchResult] = []
        embedding_provider = EMBEDDING_PROVIDER
        embedding_key = embedding_api_key or OPENAI_API_KEY if embedding_provider == "openai" else None
        if embedding_provider != "openai" or embedding_key:
            embedding_model = get_embedding_model(provider=embedding_provider, api_key=embedding_key)
            query_embedding = await embedding_model.embed_async(question)
            
            # Step 2: Retrieve relevant documents
            vector_store = get_vector_store()
            search_results = vector_store.search(
                query_embedding=query_embedding,
                top_k=self.top_k,
                filter=filter,
            )
        else:
            logger.info("Skipping retrieval; no embedding key available")
        
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
        if context_chunks:
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
        else:
            if system_prompt:
                prompt = f"""{system_prompt}

Question: {question}

Answer:"""
            else:
                prompt = f"""Answer the question as best you can.

Question: {question}

Answer:"""
        
        # Step 5: Generate answer
        llm_client = get_llm_client(provider=llm_provider, api_key=llm_api_key)
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
