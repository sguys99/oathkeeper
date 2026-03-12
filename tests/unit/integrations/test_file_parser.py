"""Tests for file parser — Word (.docx) and PDF text extraction."""

import io

import pytest
from docx import Document

from backend.app.utils.file_parser import (
    FileParseError,
    UnsupportedFileType,
    extract_text,
)

pytestmark = pytest.mark.unit


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    """Create a minimal .docx file in memory and return its bytes."""
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestExtractDocx:
    def test_extracts_paragraphs(self):
        content = _make_docx_bytes(["첫 번째 문단", "두 번째 문단"])
        result = extract_text("test.docx", content)
        assert "첫 번째 문단" in result
        assert "두 번째 문단" in result

    def test_skips_empty_paragraphs(self):
        content = _make_docx_bytes(["내용", "", "  ", "더 많은 내용"])
        result = extract_text("test.docx", content)
        lines = result.strip().split("\n")
        assert len(lines) == 2


class TestUnsupportedFileType:
    def test_txt_raises(self):
        with pytest.raises(UnsupportedFileType):
            extract_text("readme.txt", b"plain text")

    def test_csv_raises(self):
        with pytest.raises(UnsupportedFileType):
            extract_text("data.csv", b"a,b,c")

    def test_no_extension_raises(self):
        with pytest.raises(UnsupportedFileType):
            extract_text("noext", b"data")


class TestCorruptedFiles:
    def test_corrupted_docx_raises_parse_error(self):
        with pytest.raises(FileParseError):
            extract_text("corrupt.docx", b"this is not a docx file")

    def test_corrupted_pdf_raises_parse_error(self):
        with pytest.raises(FileParseError):
            extract_text("corrupt.pdf", b"this is not a pdf file")


class TestExtractPdf:
    def test_extracts_from_valid_pdf(self):
        # Create a minimal valid PDF with text
        # This is the simplest possible valid PDF
        pdf_content = (
            b"%PDF-1.0\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]"
            b"/Contents 4 0 R/Parent 2 0 R/Resources"
            b"<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>endobj\n"
            b"4 0 obj<</Length 44>>stream\n"
            b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"0000000306 00000 n \n"
            b"trailer<</Size 5/Root 1 0 R>>\n"
            b"startxref\n400\n%%EOF"
        )
        result = extract_text("test.pdf", pdf_content)
        assert "Hello World" in result
