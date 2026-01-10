"""
Document parsers for different file types.
"""
from typing import Optional
from pathlib import Path
import mimetypes

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TextParser:
    """Parser for plain text files."""
    
    @staticmethod
    def parse(content: bytes, encoding: str = "utf-8") -> str:
        """Parse text content."""
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            # Try with error handling
            return content.decode(encoding, errors="replace")


class MarkdownParser:
    """Parser for Markdown files."""
    
    @staticmethod
    def parse(content: bytes, encoding: str = "utf-8") -> str:
        """Parse markdown content (for now, just return as text)."""
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            return content.decode(encoding, errors="replace")


class PDFParser:
    """Parser for PDF files."""
    
    @staticmethod
    def parse(content: bytes) -> str:
        """Parse PDF content."""
        try:
            import PyPDF2
            import io
            
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
            
            return "\n\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2"
            )
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}", exc_info=True)
            raise ValueError(f"Failed to parse PDF: {str(e)}")


def parse_document(file_path: Optional[str] = None, content: Optional[bytes] = None) -> str:
    """
    Parse a document based on file type.
    
    Args:
        file_path: Path to file
        content: Raw file content (bytes)
        
    Returns:
        Extracted text content
    """
    if file_path:
        path = Path(file_path)
        if content is None:
            content = path.read_bytes()
        
        mime_type, _ = mimetypes.guess_type(str(path))
        extension = path.suffix.lower()
        
        # Determine parser based on extension or MIME type
        if extension == ".pdf" or mime_type == "application/pdf":
            return PDFParser.parse(content)
        elif extension in [".md", ".markdown"] or mime_type == "text/markdown":
            return MarkdownParser.parse(content)
        else:
            # Default to text parser
            return TextParser.parse(content)
    
    elif content:
        # Try to parse as text if no file path
        return TextParser.parse(content)
    
    else:
        raise ValueError("Either file_path or content must be provided")
