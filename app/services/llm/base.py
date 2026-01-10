"""
Base LLM client interface for provider abstraction.
This ensures all providers implement the same contract.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Standardized message format across providers."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Unified response schema for all LLM providers."""
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None  # tokens, cost, etc.
    finish_reason: Optional[str] = None


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__.replace("Client", "").lower()
    
    @abstractmethod
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Synchronous completion request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with standardized format
        """
        pass
    
    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """
        Streaming completion request.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system message
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Yields:
            Chunks of text as they're generated
        """
        pass
    
    @abstractmethod
    async def ask_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Async version of ask()."""
        pass
    
    @abstractmethod
    async def stream_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Async version of stream()."""
        pass
