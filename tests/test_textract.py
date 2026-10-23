"""Unit tests for Amazon Textract OCR fallback service."""

import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    NoCredentialsError,
    ReadTimeoutError,
)
from PIL import Image
import pypdf

from services.resume_parser import parse_resume_document
from services.textract_service import (
    extract_text_from_blocks,
    extract_text_with_textract,
)


def create_image_pdf() -> bytes:
    """Helper to generate a valid single-page PDF containing a raster image."""
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def create_multi_page_image_pdf(pages: int = 2) -> bytes:
    """Helper to generate a multi-page PDF with raster images."""
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        img = Image.new("RGB", (100, 100), color="green")
        img_buf = io.BytesIO()
        img.save(img_buf, format="PDF")
        img_buf.seek(0)
        reader = pypdf.PdfReader(img_buf)
        writer.add_page(reader.pages[0])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


class TestTextractOCRService(unittest.TestCase):
    def test_extract_text_from_blocks(self):
        """Verify LINE blocks are correctly parsed into multi-line text."""
        blocks = [
            {"BlockType": "PAGE", "Id": "page-1"},
            {"BlockType": "LINE", "Text": "Jane Doe", "Confidence": 99.8},
            {"BlockType": "WORD", "Text": "Jane"},
            {"BlockType": "WORD", "Text": "Doe"},
            {"BlockType": "LINE", "Text": "Senior Cloud Engineer", "Confidence": 98.5},
            {"BlockType": "LINE", "Text": "Skills: Python, AWS, Docker", "Confidence": 97.2},
        ]
        result = extract_text_from_blocks(blocks)
        self.assertIn("Jane Doe", result)
        self.assertIn("Senior Cloud Engineer", result)
        self.assertIn("Skills: Python, AWS, Docker", result)
        self.assertEqual(len(result.split("\n")), 3)

    def test_extract_text_from_empty_blocks(self):
        """Verify blocks with no lines return empty string."""
        blocks = [
            {"BlockType": "PAGE", "Id": "page-1"},
            {"BlockType": "WORD", "Text": "orphan"},
        ]
        result = extract_text_from_blocks(blocks)
        self.assertEqual(result, "")

    @patch("services.textract_service.get_textract_client")
    def test_textract_success_single_page(self, mock_get_client):
        """Verify successful single-page OCR extraction."""
        mock_client = MagicMock()
        mock_client.detect_document_text.return_value = {
            "Blocks": [
                {"BlockType": "LINE", "Text": "Jane Doe - Python Architect"},
                {"BlockType": "LINE", "Text": "10+ years experience in distributed systems."},
            ]
        }
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="resume.pdf")

        self.assertTrue(success)
        self.assertIn("Jane Doe - Python Architect", text)
        self.assertIn("distributed systems", text)
        self.assertIn("Successfully extracted", msg)
        self.assertIn("Amazon Textract OCR", msg)

    @patch("services.textract_service.get_textract_client")
    def test_textract_success_multi_page(self, mock_get_client):
        """Verify multi-page scanned PDF processes each page and joins text."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = [
            {"Blocks": [{"BlockType": "LINE", "Text": "Page 1: Summary & Experience"}]},
            {"Blocks": [{"BlockType": "LINE", "Text": "Page 2: Education & Certifications"}]},
        ]
        mock_get_client.return_value = mock_client

        pdf_bytes = create_multi_page_image_pdf(2)
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="two_page.pdf")

        self.assertTrue(success)
        self.assertIn("Page 1: Summary & Experience", text)
        self.assertIn("Page 2: Education & Certifications", text)
        self.assertEqual(mock_client.detect_document_text.call_count, 2)

    @patch("services.textract_service.get_textract_client")
    def test_textract_access_denied_exception(self, mock_get_client):
        """Verify AccessDeniedException returns clear permission guidance."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "User is not authorized"}},
            "DetectDocumentText",
        )
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="resume.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("access denied", msg.lower())
        self.assertIn("textract:detectdocumenttext", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_subscription_required_exception(self, mock_get_client):
        """Verify SubscriptionRequiredException instructs the user to enable Textract."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = ClientError(
            {"Error": {"Code": "SubscriptionRequiredException", "Message": "Needs subscription"}},
            "DetectDocumentText",
        )
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="resume.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("subscription required", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_unsupported_document_exception(self, mock_get_client):
        """Verify UnsupportedDocumentException returns clear format message."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = ClientError(
            {"Error": {"Code": "UnsupportedDocumentException", "Message": "Unsupported format"}},
            "DetectDocumentText",
        )
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="resume.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("unsupported", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_document_too_large_exception(self, mock_get_client):
        """Verify DocumentTooLargeException informs the user about the 10 MB limit."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = ClientError(
            {"Error": {"Code": "DocumentTooLargeException", "Message": "Exceeds 10 MB"}},
            "DetectDocumentText",
        )
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="large.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("10 mb", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_bad_document_exception(self, mock_get_client):
        """Verify BadDocumentException informs user about corrupt or unreadable image."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = ClientError(
            {"Error": {"Code": "BadDocumentException", "Message": "Corrupt document"}},
            "DetectDocumentText",
        )
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="bad.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("unable to read", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_timeout_handling(self, mock_get_client):
        """Verify network timeout returns friendly retry instructions."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = ConnectTimeoutError(endpoint_url="https://textract.us-east-1.amazonaws.com")
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="timeout.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("timed out", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_no_credentials_handling(self, mock_get_client):
        """Verify NoCredentialsError instructs how to configure credentials."""
        mock_client = MagicMock()
        mock_client.detect_document_text.side_effect = NoCredentialsError()
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="resume.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("credentials are not configured", msg.lower())

    @patch("services.textract_service.get_textract_client")
    def test_textract_scanned_pdf_blank_no_text_detected(self, mock_get_client):
        """Verify scan with 0 detected text words returns informative failure."""
        mock_client = MagicMock()
        mock_client.detect_document_text.return_value = {"Blocks": [{"BlockType": "PAGE"}]}
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        success, text, msg = extract_text_with_textract(io.BytesIO(pdf_bytes), filename="blank_scan.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("no readable text or words were detected", msg.lower())

    @patch.dict("os.environ", {"ENABLE_CLOUD_TEXTRACT_FALLBACK": "true"})
    @patch("services.textract_service.get_textract_client")
    def test_automatic_ocr_fallback_in_parse_resume_document(self, mock_get_client):
        """Integration test: Scanned PDF falls back to Textract when cloud OCR fallback is enabled."""
        mock_client = MagicMock()
        mock_client.detect_document_text.return_value = {
            "Blocks": [
                {"BlockType": "LINE", "Text": "Alex Morgan - Lead Frontend Engineer"},
                {"BlockType": "LINE", "Text": "React, TypeScript, CSS, Design Systems"},
            ]
        }
        mock_get_client.return_value = mock_client

        pdf_bytes = create_image_pdf()
        fake_file = SimpleNamespace(
            name="Alex_Morgan_Scanned_Resume.pdf",
            getvalue=lambda: pdf_bytes,
            size=len(pdf_bytes),
        )

        success, text, msg = parse_resume_document(fake_file)

        self.assertTrue(success)
        self.assertIn("Alex Morgan", text)
        self.assertIn("Design Systems", text)
        self.assertIn("Amazon Textract OCR", msg)


if __name__ == "__main__":
    unittest.main()
