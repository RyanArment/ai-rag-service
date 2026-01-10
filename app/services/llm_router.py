"""
LLM Router - Factory for creating and managing LLM clients.
"""
from typing import Optional
from app.core.config import LLM_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY
from app.services.llm.openai_client import OpenAIClient
from app.services.llm.anthropic_client import AnthropicClient
from app.services.llm.base import BaseLLMClient
from app.core.exceptions import ConfigurationError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Singleton client instance
_llm_client: Optional[BaseLLMClient] = None


def get_llm_client(provider: Optional[str] = None) -> BaseLLMClient:
    """
    Get or create LLM client instance (singleton pattern).
    
    Args:
        provider: Override default provider from config
        
    Returns:
        BaseLLMClient instance
        
    Raises:
        ConfigurationError: If provider or API key is missing
    """
    global _llm_client
    
    provider = provider or LLM_PROVIDER
    
    # Return existing client if provider matches
    if _llm_client and _llm_client.provider_name == provider:
        return _llm_client
    
    # Create new client
    if provider == "openai":
        if not OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY not found in environment variables",
                details={"provider": "openai"}
            )
        _llm_client = OpenAIClient(api_key=OPENAI_API_KEY)
        logger.info("Initialized OpenAI client", extra={"provider": "openai", "model": _llm_client.model})
        
    elif provider == "anthropic":
        if not ANTHROPIC_API_KEY:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY not found in environment variables",
                details={"provider": "anthropic"}
            )
        _llm_client = AnthropicClient(api_key=ANTHROPIC_API_KEY)
        logger.info("Initialized Anthropic client", extra={"provider": "anthropic", "model": _llm_client.model})
        
    else:
        raise ConfigurationError(
            f"Unsupported LLM provider: {provider}",
            details={"supported_providers": ["openai", "anthropic"]}
        )
    
    return _llm_client


def reset_client() -> None:
    """Reset the singleton client (useful for testing)."""
    global _llm_client
    _llm_client = None
