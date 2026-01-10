"""
Embedding model factory/router.
"""
from typing import Optional
from app.core.config import OPENAI_API_KEY
from app.services.embeddings.openai_embeddings import OpenAIEmbeddings
from app.services.embeddings.base import BaseEmbeddingModel
from app.core.exceptions import ConfigurationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton embedding model instance
_embedding_model: Optional[BaseEmbeddingModel] = None


def get_embedding_model(
    provider: str = "openai",
    model_name: Optional[str] = None
) -> BaseEmbeddingModel:
    """
    Get or create embedding model instance (singleton pattern).
    
    Args:
        provider: Embedding provider ("openai")
        model_name: Specific model name (optional)
        
    Returns:
        BaseEmbeddingModel instance
        
    Raises:
        ConfigurationError: If provider or API key is missing
    """
    global _embedding_model
    
    if provider == "openai":
        if not OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY not found in environment variables",
                details={"provider": "openai"}
            )
        
        model = model_name or "text-embedding-3-small"
        
        # Return existing if same provider and model
        if _embedding_model and isinstance(_embedding_model, OpenAIEmbeddings):
            if _embedding_model.model_name == model:
                return _embedding_model
        
        _embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model_name=model)
        logger.info(
            "Initialized OpenAI embeddings",
            extra={"provider": "openai", "model": model, "dimension": _embedding_model.get_dimension()}
        )
        
    else:
        raise ConfigurationError(
            f"Unsupported embedding provider: {provider}",
            details={"supported_providers": ["openai"]}
        )
    
    return _embedding_model


def reset_embedding_model() -> None:
    """Reset the singleton embedding model (useful for testing)."""
    global _embedding_model
    _embedding_model = None
