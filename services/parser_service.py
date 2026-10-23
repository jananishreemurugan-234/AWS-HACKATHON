"""Resume parser service supporting PDF and DOCX documents.

Re-exports parser functionality from services.resume_parser for backward compatibility.
"""

from services.resume_parser import (
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_with_tesseract,
    extract_text_with_textract,
    parse_resume_document,
    pdf_has_images,
)

__all__ = [
    "extract_text_from_docx",
    "extract_text_from_pdf",
    "extract_text_with_tesseract",
    "extract_text_with_textract",
    "parse_resume_document",
    "pdf_has_images",
]
