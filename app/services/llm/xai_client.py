"""
xAI (Grok) LLM client — OpenAI-compatible Chat Completions API.
"""
from app.services.llm.openai_client import OpenAIClient


class XAIClient(OpenAIClient):
    """Grok models via https://api.x.ai/v1."""

    def __init__(
        self,
        api_key: str,
        model: str = "grok-4.7",
        base_url: str = "https://api.x.ai/v1",
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            provider="xai",
        )
