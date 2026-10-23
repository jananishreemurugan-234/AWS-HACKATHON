"""Unit tests for local Tesseract OCR fallback service."""

import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from PIL import Image
import pypdf

from services.resume_parser import parse_resume_document
from services.tesseract_service import (
    configure_pytesseract,
    extract_text_with_tesseract,
    find_tesseract_binary,
    get_tesseract_install_instructions,
    is_tesseract_installed,
    render_pdf_to_images,
)


def create_sample_image_pdf(text: str = "Test Image PDF") -> bytes:
    """Generate a single-page PDF containing a raster image."""
    img = Image.new("RGB", (120, 120), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


def create_multi_page_image_pdf(pages: int = 2) -> bytes:
    """Generate a multi-page PDF containing raster images."""
    writer = pypdf.PdfWriter()
    for _ in range(pages):
        img = Image.new("RGB", (100, 100), color="teal")
        img_buf = io.BytesIO()
        img.save(img_buf, format="PDF")
        img_buf.seek(0)
        reader = pypdf.PdfReader(img_buf)
        writer.add_page(reader.pages[0])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


class TestTesseractOCRService(unittest.TestCase):
    @patch("shutil.which")
    def test_find_tesseract_binary_from_path(self, mock_which):
        """Locates tesseract executable when present on PATH."""
        mock_which.return_value = "/usr/bin/tesseract"
        binary = find_tesseract_binary()
        self.assertEqual(binary, "/usr/bin/tesseract")

    @patch.dict("os.environ", {"TESSERACT_CMD": r"C:\Custom\tesseract.exe"})
    @patch("os.path.isfile")
    @patch("os.access")
    def test_find_tesseract_binary_from_env(self, mock_access, mock_isfile):
        """Honors explicit TESSERACT_CMD environment variable."""
        mock_isfile.return_value = True
        mock_access.return_value = True
        binary = find_tesseract_binary()
        self.assertEqual(binary, r"C:\Custom\tesseract.exe")

    @patch("services.tesseract_service.find_tesseract_binary")
    def test_is_tesseract_installed_flag(self, mock_find):
        """Verifies is_tesseract_installed reflects binary discovery."""
        mock_find.return_value = "/usr/bin/tesseract"
        self.assertTrue(is_tesseract_installed())

        mock_find.return_value = None
        self.assertFalse(is_tesseract_installed())

    def test_get_tesseract_install_instructions(self):
        """Ensures installation instructions contain clear Windows, Mac, and Linux guidance."""
        instructions = get_tesseract_install_instructions()
        self.assertIn("winget install UB-Mannheim.TesseractOCR", instructions)
        self.assertIn("brew install tesseract", instructions)
        self.assertIn("apt-get install tesseract-ocr", instructions)

    @patch("services.tesseract_service.find_tesseract_binary")
    def test_missing_tesseract_returns_instructions(self, mock_find):
        """When Tesseract is not installed, returns clear installation instructions."""
        mock_find.return_value = None
        pdf_bytes = create_sample_image_pdf()
        success, text, msg = extract_text_with_tesseract(io.BytesIO(pdf_bytes), filename="scan.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("Local Tesseract OCR is not installed", msg)
        self.assertIn("winget install", msg)

    @patch("services.tesseract_service.configure_pytesseract")
    @patch("pytesseract.image_to_string")
    def test_ocr_success_single_page(self, mock_image_to_string, mock_configure):
        """Extracts text successfully from a single-page scanned PDF."""
        mock_configure.return_value = True
        mock_image_to_string.return_value = "Jane Doe - Senior Machine Learning Engineer\nPyTorch, Python, AWS"

        pdf_bytes = create_sample_image_pdf()
        success, text, msg = extract_text_with_tesseract(io.BytesIO(pdf_bytes), filename="resume.pdf")

        self.assertTrue(success)
        self.assertIn("Jane Doe", text)
        self.assertIn("Machine Learning Engineer", text)
        self.assertIn("local Tesseract OCR", msg)

    @patch("services.tesseract_service.configure_pytesseract")
    @patch("pytesseract.image_to_string")
    def test_ocr_success_multi_page(self, mock_image_to_string, mock_configure):
        """Extracts and combines text across multiple pages safely."""
        mock_configure.return_value = True
        mock_image_to_string.side_effect = [
            "Page 1: Professional Experience and Projects",
            "Page 2: Education, Certifications, and Publications",
        ]

        pdf_bytes = create_multi_page_image_pdf(2)
        success, text, msg = extract_text_with_tesseract(io.BytesIO(pdf_bytes), filename="two_pages.pdf")

        self.assertTrue(success)
        self.assertIn("Page 1: Professional Experience", text)
        self.assertIn("Page 2: Education, Certifications", text)
        self.assertEqual(mock_image_to_string.call_count, 2)

    @patch("services.resume_parser.extract_text_with_tesseract")
    def test_automatic_tesseract_fallback_in_parser(self, mock_extract):
        """Scanned PDF automatically routes to local Tesseract OCR by default."""
        mock_extract.return_value = (
            True,
            "Alex Morgan - Full Stack Developer",
            "Successfully extracted 35 characters from Alex.pdf using local Tesseract OCR.",
        )

        pdf_bytes = create_sample_image_pdf()
        fake_file = SimpleNamespace(
            name="Alex.pdf",
            getvalue=lambda: pdf_bytes,
            size=len(pdf_bytes),
        )

        success, text, msg = parse_resume_document(fake_file)

        self.assertTrue(success)
        self.assertIn("Alex Morgan", text)
        self.assertIn("local Tesseract OCR", msg)
        mock_extract.assert_called_once()

    @patch("services.tesseract_service.configure_pytesseract")
    @patch("pytesseract.image_to_string")
    def test_ocr_failure_tesseract_error(self, mock_image_to_string, mock_configure):
        """Handles pytesseract execution error safely without crashing."""
        mock_configure.return_value = True
        mock_image_to_string.side_effect = Exception("Tesseract processing failed: signal 11")

        pdf_bytes = create_sample_image_pdf()
        success, text, msg = extract_text_with_tesseract(io.BytesIO(pdf_bytes), filename="error.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("no readable text was detected", msg.lower())

    @patch("services.tesseract_service.configure_pytesseract")
    @patch("pytesseract.image_to_string")
    def test_ocr_blank_scanned_page(self, mock_image_to_string, mock_configure):
        """Scanned blank image returns clear feedback that no text was detected."""
        mock_configure.return_value = True
        mock_image_to_string.return_value = "   \n\n   "

        pdf_bytes = create_sample_image_pdf()
        success, text, msg = extract_text_with_tesseract(io.BytesIO(pdf_bytes), filename="blank_scan.pdf")

        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("no readable text was detected", msg.lower())

    def test_ocr_file_too_large(self):
        """Rejects files larger than 25 MB safely."""
        fake_large_stream = io.BytesIO()
        fake_large_stream.write(b"0" * (26 * 1024 * 1024))
        fake_large_stream.seek(0)

        success, text, msg = extract_text_with_tesseract(fake_large_stream, filename="giant.pdf")
        self.assertFalse(success)
        self.assertEqual(text, "")
        self.assertIn("exceeds the maximum local ocr limit of 25 mb", msg.lower())

    @patch("services.textract_service.extract_text_with_textract")
    @patch("services.resume_parser.extract_text_with_tesseract")
    def test_cloud_textract_not_called_by_default(self, mock_tesseract, mock_textract):
        """Verifies no cloud OCR service is called by default."""
        mock_tesseract.return_value = (
            False,
            "",
            "Local Tesseract OCR is not installed",
        )

        pdf_bytes = create_sample_image_pdf()
        fake_file = SimpleNamespace(
            name="local_scan.pdf",
            getvalue=lambda: pdf_bytes,
            size=len(pdf_bytes),
        )

        success, text, msg = parse_resume_document(fake_file)
        self.assertFalse(success)
        # Cloud Textract should NOT be called by default
        mock_textract.assert_not_called()


if __name__ == "__main__":
    unittest.main()
