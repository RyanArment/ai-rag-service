"""
OpenAI embeddings implementation.
"""
from typing import List, Union
from openai import OpenAI, AsyncOpenAI
from openai import APIError as OpenAIAPIError

from app.services.embeddings.base import BaseEmbeddingModel
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OpenAIEmbeddings(BaseEmbeddingModel):
    """OpenAI embeddings model."""
    
    # Model dimensions (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        super().__init__(model_name)
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.dimension = self.MODEL_DIMENSIONS.get(model_name, 1536)
    
    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings using OpenAI API.
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Single embedding vector or list of embedding vectors
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=texts,
            )
            
            embeddings = [item.embedding for item in response.data]
            
            return embeddings[0] if is_single else embeddings
            
        except OpenAIAPIError as e:
            logger.error(f"OpenAI embeddings error: {e}", extra={"model": self.model_name})
            raise LLMProviderError(
                f"OpenAI embeddings error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI embeddings: {e}", exc_info=True)
            raise LLMProviderError(
                f"Unexpected error: {str(e)}",
                provider="openai",
                details={"error_type": type(e).__name__}
            )
    
    async def embed_async(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Async version of embed()."""
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        try:
            response = await self.async_client.embeddings.create(
                model=self.model_name,
                input=texts,
            )
            
            embeddings = [item.embedding for item in response.data]
            
            return embeddings[0] if is_single else embeddings
            
        except OpenAIAPIError as e:
            logger.error(f"OpenAI async embeddings error: {e}", extra={"model": self.model_name})
            raise LLMProviderError(
                f"OpenAI embeddings error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
    
    def get_dimension(self) -> int:
        """Return embedding dimension."""
        return self.dimension
