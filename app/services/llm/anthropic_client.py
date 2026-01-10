"""
Anthropic LLM client implementation.
"""
import time
from typing import Optional, Iterator, AsyncIterator
from anthropic import Anthropic, AsyncAnthropic
from anthropic import APIError as AnthropicAPIError

from app.services.llm.base import BaseLLMClient, LLMResponse
from app.core.exceptions import LLMProviderError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic LLM client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
    
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Synchronous completion."""
        start_time = time.time()
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None,
                finish_reason=response.stop_reason,
            )
        except AnthropicAPIError as e:
            logger.error(f"Anthropic API error: {e}", extra={"provider": "anthropic", "error": str(e)})
            raise LLMProviderError(
                f"Anthropic API error: {str(e)}",
                provider="anthropic",
                status_code=getattr(e, "status_code", 500),
                details={"error_type": type(e).__name__}
            )
        except Exception as e:
            logger.error(f"Unexpected error in Anthropic client: {e}", exc_info=True)
            raise LLMProviderError(
                f"Unexpected error: {str(e)}",
                provider="anthropic",
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
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            with self.client.messages.stream(**kwargs) as stream:
                for text_event in stream.text_stream:
                    yield text_event
        except AnthropicAPIError as e:
            logger.error(f"Anthropic streaming error: {e}", extra={"provider": "anthropic"})
            raise LLMProviderError(
                f"Anthropic streaming error: {str(e)}",
                provider="anthropic",
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
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self.async_client.messages.create(**kwargs)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                provider="anthropic",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                } if response.usage else None,
                finish_reason=response.stop_reason,
            )
        except AnthropicAPIError as e:
            logger.error(f"Anthropic async API error: {e}", extra={"provider": "anthropic"})
            raise LLMProviderError(
                f"Anthropic API error: {str(e)}",
                provider="anthropic",
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
        messages = [{"role": "user", "content": prompt}]
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or 1024,
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            async with self.async_client.messages.stream(**kwargs) as stream:
                async for text_event in stream.text_stream:
                    yield text_event
        except AnthropicAPIError as e:
            logger.error(f"Anthropic async streaming error: {e}", extra={"provider": "anthropic"})
            raise LLMProviderError(
                f"Anthropic streaming error: {str(e)}",
                provider="anthropic",
                status_code=getattr(e, "status_code", 500),
            )
