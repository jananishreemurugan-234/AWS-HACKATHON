"""Services module for document parsing, model invocation, and external APIs."""

from services.bedrock_service import (
    DEFAULT_AWS_REGION,
    DEFAULT_BEDROCK_MODEL_ID,
    BedrockConfig,
    BedrockHealthResult,
    check_bedrock_health,
    get_aws_console_verification_guide,
    get_bedrock_config,
    mask_access_key,
)
from services.resume_parser import (
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_with_tesseract,
    extract_text_with_textract,
    parse_resume_document,
    pdf_has_images,
)

__all__ = [
    "parse_resume_document",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "extract_text_with_tesseract",
    "extract_text_with_textract",
    "pdf_has_images",
    "BedrockConfig",
    "BedrockHealthResult",
    "DEFAULT_BEDROCK_MODEL_ID",
    "DEFAULT_AWS_REGION",
    "get_bedrock_config",
    "check_bedrock_health",
    "mask_access_key",
    "get_aws_console_verification_guide",
]
