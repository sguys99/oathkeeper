"""File parser — extract plain text from Word (.docx) and PDF files."""

from __future__ import annotations

import io
import logging
from pathlib import PurePath

from docx import Document
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


class UnsupportedFileType(Exception):
    """Raised when the file extension is not supported."""


class FileParseError(Exception):
    """Raised when text extraction fails."""


def extract_text(filename: str, content: bytes) -> str:
    """Extract plain text from a .docx or .pdf file.

    Args:
        filename: Original filename (used to determine type).
        content: Raw file bytes.

    Returns:
        Extracted text content.

    Raises:
        UnsupportedFileType: If extension is not .docx or .pdf.
        FileParseError: If extraction fails.
    """
    ext = PurePath(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        msg = f"Unsupported file type: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        raise UnsupportedFileType(msg)

    try:
        if ext == ".docx":
            return _extract_docx(content)
        return _extract_pdf(content)
    except (UnsupportedFileType, FileParseError):
        raise
    except Exception as e:
        raise FileParseError(f"Failed to parse {filename}: {e}") from e


def _extract_docx(content: bytes) -> str:
    """Extract text from a Word document."""
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def _extract_pdf(content: bytes) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)
