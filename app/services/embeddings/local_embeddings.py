"""
Local embeddings implementation using sentence-transformers.
"""
from typing import List, Union
import asyncio
from sentence_transformers import SentenceTransformer

from app.services.embeddings.base import BaseEmbeddingModel


class LocalEmbeddings(BaseEmbeddingModel):
    """Sentence-transformers embeddings model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__(model_name)
        self.model = SentenceTransformer(model_name)
        self.dimension = int(self.model.get_sentence_embedding_dimension())

    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        if is_single:
            return embeddings[0].tolist()
        return [embedding.tolist() for embedding in embeddings]

    async def embed_async(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        return await asyncio.to_thread(self.embed, text)

    def get_dimension(self) -> int:
        return self.dimension
