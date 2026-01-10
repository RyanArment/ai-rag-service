"""
Base embedding interface for provider abstraction.
"""
from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np


class BaseEmbeddingModel(ABC):
    """Abstract base class for all embedding models."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.dimension = None  # Will be set by implementation
    
    @abstractmethod
    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Single embedding vector (list of floats) or list of embedding vectors
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        pass
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
