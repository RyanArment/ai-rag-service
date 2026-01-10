"""
OpenAI LLM client implementation.
"""
import time
from typing import Optional, Iterator, AsyncIterator
from openai import OpenAI, AsyncOpenAI
from openai import APIError as OpenAIAPIError

from app.services.llm.base import BaseLLMClient, LLMResponse
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI LLM client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
    
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Synchronous completion."""
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
            )
        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error: {e}", extra={"provider": "openai", "error": str(e)})
            raise LLMProviderError(
                f"OpenAI API error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI client: {e}", exc_info=True)
            raise LLMProviderError(
                f"Unexpected error: {str(e)}",
                provider="openai",
                details={"error_type": type(e).__name__}
            )
    
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Streaming completion."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIAPIError as e:
            logger.error(f"OpenAI streaming error: {e}", extra={"provider": "openai"})
            raise LLMProviderError(
                f"OpenAI streaming error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
    
    async def ask_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Async completion."""
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=self.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
            )
        except OpenAIAPIError as e:
            logger.error(f"OpenAI async API error: {e}", extra={"provider": "openai"})
            raise LLMProviderError(
                f"OpenAI API error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
    
    async def stream_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Async streaming completion."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except OpenAIAPIError as e:
            logger.error(f"OpenAI async streaming error: {e}", extra={"provider": "openai"})
            raise LLMProviderError(
                f"OpenAI streaming error: {str(e)}",
                provider="openai",
                status_code=getattr(e, "status_code", 500),
            )
