"""
Document processing: parsing, chunking, and metadata extraction.
"""
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import mimetypes
from pydantic import BaseModel

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DocumentChunk(BaseModel):
    """A chunk of a document."""
    content: str
    metadata: Dict[str, Any] = {}
    chunk_index: int = 0


class DocumentProcessor:
    """Process documents: parse, chunk, and extract metadata."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunk_strategy: str = "sentence",
    ):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
            chunk_strategy: "sentence", "token", or "fixed"
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_strategy = chunk_strategy
    
    def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[DocumentChunk]:
        """
        Process text into chunks.
        
        Args:
            text: Raw text content
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of DocumentChunk objects
        """
        metadata = metadata or {}
        
        if self.chunk_strategy == "sentence":
            chunks = self._chunk_by_sentence(text)
        elif self.chunk_strategy == "token":
            chunks = self._chunk_by_tokens(text)
        else:  # fixed
            chunks = self._chunk_fixed(text)
        
        result = []
        for i, chunk_text in enumerate(chunks):
            result.append(DocumentChunk(
                content=chunk_text,
                metadata={**metadata, "chunk_index": i},
                chunk_index=i,
            ))
        
        logger.info(f"Processed text into {len(result)} chunks")
        return result
    
    def _chunk_by_sentence(self, text: str) -> List[str]:
        """Chunk text by sentences."""
        # Split by sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_size + 1  # +1 for space
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _chunk_by_tokens(self, text: str) -> List[str]:
        """Chunk text by approximate tokens (4 chars = 1 token)."""
        # Simple approximation: 4 characters ≈ 1 token
        token_size = self.chunk_size * 4
        overlap_size = self.chunk_overlap * 4
        
        return self._chunk_fixed(text, token_size, overlap_size)
    
    def _chunk_fixed(
        self,
        text: str,
        size: Optional[int] = None,
        overlap: Optional[int] = None,
    ) -> List[str]:
        """Chunk text into fixed-size pieces."""
        size = size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + size
            chunk = text[start:end]
            
            # Try to break at word boundary
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > size * 0.5:  # If space is in second half
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            
            # Move start forward with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def extract_metadata(self, file_path: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract metadata from file or content.
        
        Args:
            file_path: Path to file
            content: Text content
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        if file_path:
            path = Path(file_path)
            metadata["filename"] = path.name
            metadata["file_extension"] = path.suffix
            metadata["file_size"] = path.stat().st_size if path.exists() else None
            
            # Guess MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            metadata["mime_type"] = mime_type
        
        if content:
            metadata["content_length"] = len(content)
            metadata["word_count"] = len(content.split())
            metadata["line_count"] = len(content.splitlines())
        
        return metadata
