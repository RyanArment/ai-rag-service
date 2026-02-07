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


def get_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> BaseLLMClient:
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
    
    # Return existing client if provider matches and no override key
    if not api_key and _llm_client and _llm_client.provider_name == provider:
        return _llm_client
    
    # Create new client
    if provider == "openai":
        resolved_key = api_key or OPENAI_API_KEY
        if not resolved_key:
            raise ConfigurationError(
                "OPENAI_API_KEY not found in environment variables",
                details={"provider": "openai"}
            )
        if api_key:
            return OpenAIClient(api_key=resolved_key)
        _llm_client = OpenAIClient(api_key=resolved_key)
        logger.info("Initialized OpenAI client", extra={"provider": "openai", "model": _llm_client.model})
        
    elif provider == "anthropic":
        resolved_key = api_key or ANTHROPIC_API_KEY
        if not resolved_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY not found in environment variables",
                details={"provider": "anthropic"}
            )
        if api_key:
            return AnthropicClient(api_key=resolved_key)
        _llm_client = AnthropicClient(api_key=resolved_key)
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
