"""Local Tesseract OCR Service for ResumePilot AI.

Provides on-device, privacy-preserving OCR fallback for scanned and
image-only PDF resumes without sending documents to cloud APIs.
"""

import io
import os
import shutil
from typing import List, Optional, Tuple
from PIL import Image

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    pytesseract = None  # type: ignore
    HAS_PYTESSERACT = False

try:
    import pypdfium2 as pdfium
    HAS_PDFIUM = True
except ImportError:
    pdfium = None  # type: ignore
    HAS_PDFIUM = False

import pypdf

# Maximum file size for local OCR (25 MB)
MAX_OCR_FILE_SIZE_BYTES = 25 * 1024 * 1024
# Maximum page count for local OCR to avoid excessive resource usage
MAX_OCR_PAGES = 20


def find_tesseract_binary() -> Optional[str]:
    """Locate the Tesseract executable on the local system.

    Checks explicit environment variables, system PATH, and standard
    platform installation directories.

    Returns:
        Path to tesseract binary if found, None otherwise.
    """
    # 1. Check explicit environment override
    env_path = os.getenv("TESSERACT_CMD") or os.getenv("TESSERACT_PATH")
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    # 2. Check system PATH
    which_bin = shutil.which("tesseract")
    if which_bin:
        return which_bin

    # 3. Standard Windows installation paths
    windows_candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in windows_candidates:
        if os.path.isfile(candidate):
            return candidate

    # 4. Standard POSIX / macOS installation paths
    posix_candidates = [
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    for candidate in posix_candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None


def is_tesseract_installed() -> bool:
    """Check whether Tesseract OCR is installed and available locally."""
    if not HAS_PYTESSERACT or pytesseract is None:
        return False
    return find_tesseract_binary() is not None


def configure_pytesseract() -> bool:
    """Ensure pytesseract points to the detected Tesseract binary."""
    if not HAS_PYTESSERACT or pytesseract is None:
        return False
    binary = find_tesseract_binary()
    if binary:
        pytesseract.pytesseract.tesseract_cmd = binary
        return True
    return False


def get_tesseract_install_instructions() -> str:
    """Return clear, multi-platform installation instructions for Tesseract OCR."""
    return (
        "**Local Tesseract OCR is not installed or not found on your system PATH.**\n\n"
        "To enable local, private OCR for scanned PDF resumes without cloud dependencies:\n\n"
        "• **Windows:** Run in PowerShell/Terminal:\n"
        "  `winget install UB-Mannheim.TesseractOCR`\n"
        "  *(or download the installer from: https://github.com/UB-Mannheim/tesseract/wiki)*\n\n"
        "• **macOS:** Run in Terminal:\n"
        "  `brew install tesseract`\n\n"
        "• **Linux (Ubuntu/Debian):** Run:\n"
        "  `sudo apt-get install tesseract-ocr`\n\n"
        "Once installed, restart the app or ensure Tesseract is on your PATH "
        "(default Windows path: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`)."
    )


def render_pdf_to_images(
    file_source: io.BytesIO, max_pages: int = MAX_OCR_PAGES
) -> List[Image.Image]:
    """Render PDF pages to PIL Images for OCR processing.

    Uses pypdfium2 if available, or falls back to extracting embedded images
    via pypdf.

    Args:
        file_source: In-memory bytes stream containing the PDF.
        max_pages: Maximum number of pages to render.

    Returns:
        List of PIL Image objects for each page.
    """
    file_source.seek(0)
    images: List[Image.Image] = []

    if HAS_PDFIUM and pdfium is not None:
        try:
            doc = pdfium.PdfDocument(file_source)
            page_count = min(len(doc), max_pages)
            for i in range(page_count):
                page = doc[i]
                # Render at 2x scale (~144 dpi) for high-accuracy OCR
                image = page.render(scale=2.0).to_pil()
                images.append(image)
            return images
        except Exception:
            images = []

    # Fallback to extracting embedded images from pages via pypdf
    file_source.seek(0)
    try:
        reader = pypdf.PdfReader(file_source)
        page_count = min(len(reader.pages), max_pages)
        for i in range(page_count):
            page = reader.pages[i]
            if hasattr(page, "images") and len(page.images) > 0:
                for img in page.images:
                    try:
                        im = Image.open(io.BytesIO(img.data))
                        images.append(im.convert("RGB"))
                    except Exception:
                        pass
    except Exception:
        pass

    return images


def extract_text_with_tesseract(
    file_source: io.BytesIO,
    filename: str = "document.pdf",
) -> Tuple[bool, str, str]:
    """Perform local OCR on a scanned or image-only PDF using Tesseract.

    Args:
        file_source: In-memory byte stream containing the PDF.
        filename: Name of the file for reporting and diagnostics.

    Returns:
        Tuple of (success: bool, extracted_text: str, message: str)
    """
    if not HAS_PYTESSERACT or pytesseract is None:
        return (
            False,
            "",
            "pytesseract Python library is not installed. Please run `pip install pytesseract`.",
        )

    # Validate file size
    file_source.seek(0, io.SEEK_END)
    file_size = file_source.tell()
    file_source.seek(0)

    if file_size == 0:
        return False, "", f"The document '{filename}' is empty (0 bytes)."

    if file_size > MAX_OCR_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return (
            False,
            "",
            f"The document '{filename}' ({size_mb:.1f} MB) exceeds the maximum local OCR limit of 25 MB. "
            "Please upload a smaller file.",
        )

    # Verify Tesseract binary exists
    if not configure_pytesseract():
        return False, "", get_tesseract_install_instructions()

    # Render pages to images
    try:
        images = render_pdf_to_images(file_source)
    except Exception as render_err:
        return (
            False,
            "",
            f"Failed to render pages from '{filename}' for local OCR: {str(render_err)}",
        )

    if not images:
        return (
            False,
            "",
            f"No readable pages or embedded images could be extracted from '{filename}' for OCR.",
        )

    extracted_pages = []

    try:
        for idx, img in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(img)
                if page_text and page_text.strip():
                    extracted_pages.append(page_text.strip())
            except pytesseract.TesseractNotFoundError:
                return False, "", get_tesseract_install_instructions()
            except Exception as page_ocr_err:
                # If one page fails in a multi-page document, continue if possible
                pass

        combined_text = "\n\n".join(extracted_pages).strip()

        if not combined_text:
            return (
                False,
                "",
                f"Local Tesseract OCR scanned '{filename}', but no readable text was detected on the page(s).",
            )

        return (
            True,
            combined_text,
            f"Successfully extracted {len(combined_text)} characters from {filename} using local Tesseract OCR.",
        )

    except pytesseract.TesseractNotFoundError:
        return False, "", get_tesseract_install_instructions()
    except Exception as exc:
        return (
            False,
            "",
            f"Local Tesseract OCR failed while processing '{filename}': {str(exc)}",
        )
