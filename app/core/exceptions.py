"""
Custom exceptions for the RAG service.
"""
from typing import Optional


class RAGServiceError(Exception):
    """Base exception for all RAG service errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class LLMProviderError(RAGServiceError):
    """Error from LLM provider API."""
    
    def __init__(self, message: str, provider: str, status_code: int = 500, details: Optional[dict] = None):
        self.provider = provider
        super().__init__(
            f"[{provider}] {message}",
            status_code=status_code,
            details=details
        )


class ConfigurationError(RAGServiceError):
    """Configuration or environment setup error."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)


class ValidationError(RAGServiceError):
    """Input validation error."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)
