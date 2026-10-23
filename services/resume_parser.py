"""Resume parser service supporting PDF and DOCX documents.

Extracts raw and structured text from uploaded resume files using pypdf
and python-docx without relying on external cloud APIs or OCR engines.
"""

import io
import os
from typing import Optional, Tuple
import docx
import pypdf

from services.tesseract_service import extract_text_with_tesseract
from services.textract_service import extract_text_with_textract


def pdf_has_images(reader: pypdf.PdfReader) -> bool:
    """Detect whether any page in the PDF contains embedded images.

    Args:
        reader: An initialized pypdf.PdfReader instance.

    Returns:
        True if at least one image is found, False otherwise.
    """
    for page in reader.pages:
        try:
            if hasattr(page, "images") and len(page.images) > 0:
                return True
        except Exception:
            pass

        try:
            resources = page.get("/Resources", {})
            if hasattr(resources, "get_object"):
                resources = resources.get_object()
            if "/XObject" in resources:
                xobjects = resources["/XObject"]
                if hasattr(xobjects, "get_object"):
                    xobjects = xobjects.get_object()
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    if hasattr(obj, "get_object"):
                        obj = obj.get_object()
                    if obj.get("/Subtype") == "/Image":
                        return True
        except Exception:
            pass

    return False


def extract_text_from_pdf(file_source: io.BytesIO) -> str:
    """Extract plain text from a PDF file stream.

    Args:
        file_source: In-memory bytes stream containing the PDF.

    Returns:
        Extracted text content from all pages joined by newlines.
    """
    file_source.seek(0)
    reader = pypdf.PdfReader(file_source)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
        if reader.is_encrypted:
            raise PermissionError("The PDF document is encrypted or password-protected.")

    extracted_pages = []

    for idx, page in enumerate(reader.pages):
        page_text = ""
        try:
            page_text = page.extract_text()
        except Exception:
            page_text = ""

        # Fallback to layout mode if standard extraction yielded nothing
        if not page_text or not page_text.strip():
            try:
                page_text = page.extract_text(extraction_mode="layout")
            except Exception:
                pass

        if page_text and page_text.strip():
            extracted_pages.append(page_text.strip())

    return "\n\n".join(extracted_pages).strip()


def extract_text_from_docx(file_source: io.BytesIO) -> str:
    """Extract plain text from a DOCX file stream.

    Args:
        file_source: In-memory bytes stream containing the DOCX.

    Returns:
        Extracted text content joined by newlines.
    """
    file_source.seek(0)
    document = docx.Document(file_source)
    extracted_paragraphs = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            extracted_paragraphs.append(text)

    # Also capture text inside tables (common in resume templates)
    for table in document.tables:
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                extracted_paragraphs.append(" | ".join(row_cells))

    return "\n".join(extracted_paragraphs).strip()


def parse_resume_document(uploaded_file) -> Tuple[bool, str, str]:
    """Safely parse uploaded Streamlit file or bytes stream.

    Args:
        uploaded_file: Uploaded file object with .name and .read()/.getvalue() methods.

    Returns:
        Tuple of (success: bool, extracted_text: str, message: str)
    """
    if uploaded_file is None:
        return False, "", "No file provided for parsing."

    filename = getattr(uploaded_file, "name", "document").lower()

    try:
        # Streamlit UploadedFile provides a getvalue() or read()
        if hasattr(uploaded_file, "getvalue"):
            raw_bytes = uploaded_file.getvalue()
        elif hasattr(uploaded_file, "read"):
            raw_bytes = uploaded_file.read()
        else:
            return False, "", "Unable to read binary data from file object."

        if not raw_bytes or len(raw_bytes) == 0:
            return False, "", f"The uploaded file '{getattr(uploaded_file, 'name', 'document')}' is empty (0 bytes)."

        file_bytes = io.BytesIO(raw_bytes)

        if filename.endswith(".pdf"):
            # Inspect PDF structure
            try:
                reader = pypdf.PdfReader(file_bytes)
            except Exception as read_err:
                return (
                    False,
                    "",
                    f"Failed to parse {getattr(uploaded_file, 'name', 'document')}: Invalid or corrupted PDF file ({str(read_err)}).",
                )

            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    pass
                if reader.is_encrypted:
                    return (
                        False,
                        "",
                        f"Failed to parse {getattr(uploaded_file, 'name', 'document')}: The PDF document is password-protected or encrypted.",
                    )

            if len(reader.pages) == 0:
                return (
                    False,
                    "",
                    "The document was successfully read, but contains no pages.",
                )

            file_bytes.seek(0)
            text = extract_text_from_pdf(file_bytes)

            if not text:
                # If the PDF contains no text and no images, it is a blank document.
                if not pdf_has_images(reader):
                    return (
                        False,
                        "",
                        "The document was successfully read, but no readable text or content was found (the pages appear blank).",
                    )

                # Scanned / image-only PDF: Automatically fall back to local Tesseract OCR
                file_bytes.seek(0)
                display_name = getattr(uploaded_file, "name", filename)
                ocr_success, ocr_text, ocr_msg = extract_text_with_tesseract(
                    file_bytes, filename=display_name
                )
                if ocr_success:
                    return True, ocr_text, ocr_msg

                # Optional cloud fallback if explicitly enabled via environment
                enable_cloud = os.getenv("ENABLE_CLOUD_TEXTRACT_FALLBACK", "false").lower() in ("true", "1")
                if enable_cloud:
                    file_bytes.seek(0)
                    cloud_success, cloud_text, cloud_msg = extract_text_with_textract(
                        file_bytes, filename=display_name
                    )
                    if cloud_success:
                        return True, cloud_text, cloud_msg

                return False, "", ocr_msg

        elif filename.endswith(".docx"):
            text = extract_text_from_docx(file_bytes)
            if not text:
                return (
                    False,
                    "",
                    "The DOCX document was successfully read, but no readable text was found (it may be empty or contain only images).",
                )
        else:
            return (
                False,
                "",
                f"Unsupported file format '{getattr(uploaded_file, 'name', 'document')}'. Only .pdf and .docx are supported.",
            )

        file_display_name = getattr(uploaded_file, "name", "document")
        return True, text, f"Successfully extracted {len(text)} characters from {file_display_name}."

    except Exception as exc:
        return False, "", f"Failed to parse {getattr(uploaded_file, 'name', filename)}: {str(exc)}"
