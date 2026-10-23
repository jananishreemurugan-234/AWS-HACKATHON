"""Amazon Textract OCR Service for ResumePilot AI.

Provides automatic OCR fallback when standard text extraction returns
no meaningful text from scanned or image-only PDF resumes.
"""

import io
from typing import Optional, Tuple
import pypdf

try:
    import boto3
    from botocore.exceptions import (
        BotoCoreError,
        ClientError,
        ConnectTimeoutError,
        EndpointConnectionError,
        NoCredentialsError,
        ReadTimeoutError,
    )
    HAS_BOTO3 = True
except ImportError:
    boto3 = None  # type: ignore
    HAS_BOTO3 = False
    BotoCoreError = Exception  # type: ignore
    ClientError = Exception  # type: ignore
    ConnectTimeoutError = Exception  # type: ignore
    EndpointConnectionError = Exception  # type: ignore
    NoCredentialsError = Exception  # type: ignore
    ReadTimeoutError = Exception  # type: ignore

from services.bedrock_service import DEFAULT_AWS_REGION, get_bedrock_config

# Amazon Textract synchronous document size limit is 10 MB
TEXTRACT_MAX_BYTES = 10 * 1024 * 1024


def get_textract_client():
    """Instantiate a boto3 Textract client using the existing AWS credential chain.

    Returns:
        boto3 Textract client instance.
    """
    if not HAS_BOTO3 or boto3 is None:
        raise ImportError(
            "boto3 is not installed. Please install boto3 to use Amazon Textract OCR."
        )

    cfg = get_bedrock_config()
    session = boto3.Session(
        profile_name=cfg.profile_name,
        region_name=cfg.region or DEFAULT_AWS_REGION,
    )
    return session.client("textract", region_name=cfg.region or DEFAULT_AWS_REGION)


def extract_text_from_blocks(blocks: list) -> str:
    """Extract and reconstruct plain text lines from Textract response blocks.

    Args:
        blocks: List of block dictionaries from detect_document_text response.

    Returns:
        Newline-joined string of detected text lines.
    """
    lines = []
    for block in blocks:
        if block.get("BlockType") == "LINE" and block.get("Text"):
            line_text = block["Text"].strip()
            if line_text:
                lines.append(line_text)
    return "\n".join(lines).strip()


def extract_text_with_textract(
    file_source: io.BytesIO,
    filename: str = "document.pdf",
) -> Tuple[bool, str, str]:
    """Extract text from a scanned or image-only PDF using Amazon Textract OCR.

    Args:
        file_source: In-memory byte stream containing the PDF or image.
        filename: Optional filename for logging and error reporting.

    Returns:
        Tuple of (success: bool, extracted_text: str, message: str)
    """
    if not HAS_BOTO3 or boto3 is None:
        return (
            False,
            "",
            "boto3 SDK is not installed. Please install boto3 to enable Amazon Textract OCR.",
        )

    file_source.seek(0)
    raw_bytes = file_source.read()

    if not raw_bytes or len(raw_bytes) == 0:
        return False, "", f"The document '{filename}' is empty (0 bytes)."

    if len(raw_bytes) > TEXTRACT_MAX_BYTES:
        size_mb = len(raw_bytes) / (1024 * 1024)
        return (
            False,
            "",
            f"The document '{filename}' ({size_mb:.1f} MB) exceeds Amazon Textract's 10 MB maximum limit. "
            "Please upload a smaller file.",
        )

    cfg = get_bedrock_config()
    region = cfg.region or DEFAULT_AWS_REGION

    try:
        client = get_textract_client()
    except Exception as init_err:
        return (
            False,
            "",
            f"Unable to initialize Amazon Textract client: {str(init_err)}",
        )

    # Process PDF: For multi-page or single-page PDFs, process each page cleanly
    try:
        file_source.seek(0)
        try:
            reader = pypdf.PdfReader(file_source)
            page_count = len(reader.pages)
        except Exception:
            # If not a valid PDF or is raw image bytes, attempt single document text detection
            reader = None
            page_count = 1

        extracted_page_texts = []

        if reader is not None and page_count > 1:
            # Multi-page PDF: Synchronous Textract operations require single-page documents.
            # We process each page individually so the user does not need to convert files.
            for idx, page in enumerate(reader.pages):
                page_payload: Optional[bytes] = None

                # If page contains extracted image, use image bytes directly
                if hasattr(page, "images") and len(page.images) > 0:
                    try:
                        page_payload = page.images[0].data
                    except Exception:
                        page_payload = None

                # Otherwise, write single page as a 1-page PDF
                if not page_payload:
                    writer = pypdf.PdfWriter()
                    writer.add_page(page)
                    buf = io.BytesIO()
                    writer.write(buf)
                    page_payload = buf.getvalue()

                if len(page_payload) > TEXTRACT_MAX_BYTES:
                    return (
                        False,
                        "",
                        f"Page {idx + 1} of '{filename}' exceeds Amazon Textract's 10 MB limit.",
                    )

                response = client.detect_document_text(
                    Document={"Bytes": page_payload}
                )
                blocks = response.get("Blocks", [])
                page_text = extract_text_from_blocks(blocks)
                if page_text:
                    extracted_page_texts.append(page_text)

        else:
            # Single-page PDF or image: Send directly
            page_payload = raw_bytes
            # If it's a PDF with a clean embedded image, passing either the PDF or the image works.
            if reader is not None and page_count == 1:
                page = reader.pages[0]
                if hasattr(page, "images") and len(page.images) > 0:
                    try:
                        page_payload = page.images[0].data
                    except Exception:
                        page_payload = raw_bytes

            response = client.detect_document_text(Document={"Bytes": page_payload})
            blocks = response.get("Blocks", [])
            page_text = extract_text_from_blocks(blocks)
            if page_text:
                extracted_page_texts.append(page_text)

        combined_text = "\n\n".join(extracted_page_texts).strip()

        if not combined_text:
            return (
                False,
                "",
                f"Amazon Textract scanned '{filename}', but no readable text or words were detected on the page(s).",
            )

        return (
            True,
            combined_text,
            f"Successfully extracted {len(combined_text)} characters from {filename} using Amazon Textract OCR.",
        )

    except ClientError as exc:
        error_info = exc.response.get("Error", {})
        code = error_info.get("Code", "ClientError")
        msg = error_info.get("Message", str(exc))

        if code == "SubscriptionRequiredException":
            return (
                False,
                "",
                "Amazon Textract subscription required: Your AWS account is not yet subscribed to the Amazon Textract service. "
                "Please enable Amazon Textract in your AWS account to process scanned documents.",
            )
        elif code in ("AccessDeniedException", "UnauthorizedOperation"):
            return (
                False,
                "",
                f"Amazon Textract access denied: Your AWS credentials lack the required 'textract:DetectDocumentText' permission. "
                f"Please ensure an IAM policy with 'textract:DetectDocumentText' is attached (Region: {region}).",
            )
        elif code == "UnsupportedDocumentException":
            return (
                False,
                "",
                "Amazon Textract unsupported document format or dimension. "
                "Supported formats include JPEG, PNG, PDF, and TIFF.",
            )
        elif code == "DocumentTooLargeException":
            return (
                False,
                "",
                f"The document '{filename}' exceeds Amazon Textract's maximum size limit (10 MB). "
                "Please upload a smaller file.",
            )
        elif code == "BadDocumentException":
            return (
                False,
                "",
                f"Amazon Textract was unable to read '{filename}'. The file may be corrupt, damaged, or unreadable.",
            )
        elif code in ("ProvisionedThroughputExceededException", "LimitExceededException"):
            return (
                False,
                "",
                "Amazon Textract request limit or quota exceeded. Please wait a moment and try again.",
            )
        elif code == "InternalServerError":
            return (
                False,
                "",
                "Amazon Textract encountered an internal service error. Please retry in a few moments.",
            )
        elif code == "InvalidParameterException":
            return (
                False,
                "",
                f"Amazon Textract invalid parameter error: {msg}",
            )
        else:
            return (
                False,
                "",
                f"Amazon Textract OCR error ({code}): {msg}",
            )

    except NoCredentialsError:
        return (
            False,
            "",
            "AWS credentials are not configured or available. "
            "To use Amazon Textract OCR on scanned documents, configure credentials via AWS CLI, AWS SSO, IAM role, or .env.",
        )
    except (ConnectTimeoutError, ReadTimeoutError):
        return (
            False,
            "",
            f"Amazon Textract request timed out while processing '{filename}'. Please check your network connection and retry.",
        )
    except EndpointConnectionError:
        return (
            False,
            "",
            f"Unable to connect to the Amazon Textract endpoint in region '{region}'. "
            "Please verify your internet connection and AWS region configuration.",
        )
    except BotoCoreError as bce:
        return (
            False,
            "",
            f"AWS error during Amazon Textract processing: {str(bce)}",
        )
    except Exception as exc:
        return (
            False,
            "",
            f"Failed to process '{filename}' with Amazon Textract OCR: {str(exc)}",
        )
