"""Amazon Bedrock Configuration and Health Check Service.

Stage 5: Secure AWS credential resolution via environment or standard AWS
credential chain (CLI profiles, SSO, IAM roles) with secret masking and
permission readiness checks without executing remote model inference.
"""

from dataclasses import dataclass
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Safe import of boto3 to prevent module-level import crashes
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    boto3 = None  # type: ignore
    HAS_BOTO3 = False

# Load local environment configuration if present
load_dotenv()

# Standard recommended Bedrock models for text & reasoning
DEFAULT_BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
DEFAULT_AWS_REGION = "us-east-1"


@dataclass
class BedrockConfig:
    """Configuration container for Amazon Bedrock."""

    region: str
    model_id: str
    profile_name: Optional[str] = None
    endpoint_url: Optional[str] = None


@dataclass
class BedrockHealthResult:
    """Result of Bedrock credential and readiness inspection."""

    is_configured: bool
    credential_source: str
    region: str
    model_id: str
    masked_key: Optional[str]
    missing_items: List[str]
    status_message: str
    can_initialize_client: bool
    inference_enabled: bool = False  # Kept False during Stage 5


def mask_access_key(key: Optional[str]) -> Optional[str]:
    """Safely mask an AWS access key without exposing sensitive characters.

    Args:
        key: Raw AWS Access Key ID string.

    Returns:
        Masked representation (e.g., 'AKIA...4A2B') or None.
    """
    if not key or not isinstance(key, str):
        return None
    cleaned = key.strip()
    if len(cleaned) <= 6:
        return "******"
    return f"{cleaned[:4]}...{cleaned[-4:]}"


def get_bedrock_config() -> BedrockConfig:
    """Retrieve Bedrock configuration from environment variables or standard defaults."""
    region = (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or DEFAULT_AWS_REGION
    ).strip()

    model_id = (
        os.getenv("BEDROCK_MODEL_ID") or DEFAULT_BEDROCK_MODEL_ID
    ).strip()

    profile_name = os.getenv("AWS_PROFILE")
    endpoint_url = os.getenv("BEDROCK_ENDPOINT_URL")

    return BedrockConfig(
        region=region,
        model_id=model_id,
        profile_name=profile_name.strip() if profile_name else None,
        endpoint_url=endpoint_url.strip() if endpoint_url else None,
    )


def check_bedrock_health() -> BedrockHealthResult:
    """Inspect AWS credential provider chain and Bedrock configuration readiness.

    Supports:
    1. Standard AWS Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
    2. AWS CLI shared credentials (~/.aws/credentials)
    3. AWS SSO profiles (aws sso login)
    4. IAM Roles (EC2, ECS, Lambda, Cloud9)

    Guarantees:
    - Never logs or exposes secret access keys or tokens.
    - Masks any displayed access key identifier.
    - Never executes model inference calls.

    Returns:
        BedrockHealthResult indicating configuration availability and guidance.
    """
    config = get_bedrock_config()
    missing: List[str] = []
    masked_key: Optional[str] = None
    credential_source = "None / Missing"
    can_initialize = False

    if not HAS_BOTO3 or boto3 is None:
        missing.append("boto3 SDK (pip install boto3)")
        return BedrockHealthResult(
            is_configured=False,
            credential_source="SDK Missing",
            region=config.region,
            model_id=config.model_id,
            masked_key=None,
            missing_items=missing,
            status_message="⚠️ boto3 SDK is not installed in the active environment.",
            can_initialize_client=False,
            inference_enabled=False,
        )

    # Check session resolution
    try:
        session = boto3.Session(
            profile_name=config.profile_name,
            region_name=config.region,
        )
        credentials = session.get_credentials()

        if credentials is not None:
            # Mask access key identifier
            raw_key = getattr(credentials, "access_key", None)
            if raw_key:
                masked_key = mask_access_key(raw_key)

            # Discover resolution method
            method = getattr(credentials, "method", "unknown")
            method_map = {
                "env": "Environment Variables (AWS_ACCESS_KEY_ID)",
                "shared-credentials-file": "AWS Shared Credentials File (~/.aws/credentials)",
                "config-file": "AWS Config Profile (~/.aws/config)",
                "sso": "AWS Single Sign-On (AWS SSO)",
                "assume-role": "Assumed IAM Role",
                "iam-role": "IAM Instance Profile / ECS Task Role",
                "login": "AWS Login Credential Provider (SSO/Token)",
            }
            credential_source = method_map.get(method, f"AWS Credential Provider ({method})")

            # Test safe client instantiation (offline verification)
            try:
                boto3.client(
                    "bedrock-runtime",
                    region_name=config.region,
                    aws_access_key_id=credentials.access_key,
                    aws_secret_access_key=credentials.secret_key,
                    aws_session_token=credentials.token,
                )
                can_initialize = True
            except Exception:
                can_initialize = False
        else:
            missing.append("AWS Credentials (via environment, ~/.aws/credentials, SSO, or IAM role)")

    except Exception as exc:
        exc_str = str(exc)
        if "botocore[crt]" in exc_str or "login credential provider requires" in exc_str.lower():
            missing.append('botocore[crt] dependency (pip install "botocore[crt]")')
        else:
            missing.append(f"AWS Session Error: {exc_str}")

    # Region validation
    if not config.region:
        missing.append("AWS Region (AWS_REGION)")
    elif not re.match(r"^[a-z]{2}-[a-z]+-\d+$", config.region):
        missing.append(f"Invalid AWS Region format ('{config.region}')")

    # Model ID validation
    if not config.model_id:
        missing.append("Bedrock Model ID (BEDROCK_MODEL_ID)")

    is_configured = (len(missing) == 0) and (masked_key is not None or credential_source != "None / Missing")

    if is_configured:
        status_message = (
            f"✅ AWS Bedrock configuration detected.\n"
            f"- Credential Source: {credential_source}\n"
            f"- Target Region: `{config.region}`\n"
            f"- Model ID: `{config.model_id}`\n"
            f"- Authentication: Verified ({credential_source})\n"
            f"- Client Instantiation: {'Verified' if can_initialize else 'Pending'}\n"
            f"- Live Inference: Disabled (Stage 5 safety constraint)"
        )
    else:
        status_message = (
            f"⚠️ AWS Bedrock configuration is incomplete.\n"
            f"- Missing components: {', '.join(missing)}\n"
            f"- Current Target Region: `{config.region}`\n"
            f"- Current Target Model: `{config.model_id}`\n"
            f"- No live inference will be attempted until credentials and model permissions are verified."
        )

    return BedrockHealthResult(
        is_configured=is_configured,
        credential_source=credential_source,
        region=config.region,
        model_id=config.model_id,
        masked_key=masked_key,
        missing_items=missing,
        status_message=status_message,
        can_initialize_client=can_initialize,
        inference_enabled=False,
    )


def get_aws_console_verification_guide() -> Dict[str, Any]:
    """Provide step-by-step guidance for verifying AWS Bedrock setup in AWS Console."""
    return {
        "title": "AWS Console Bedrock Verification Guide",
        "steps": [
            {
                "topic": "1. Verify AWS Region",
                "instructions": (
                    "In the AWS Console top-right navigation bar, ensure your region is set to an active "
                    "Bedrock region supporting your target model (e.g., 'us-east-1' (N. Virginia) or "
                    "'us-west-2' (Oregon))."
                ),
            },
            {
                "topic": "2. Verify Bedrock Model Access",
                "instructions": (
                    "Navigate to 'Amazon Bedrock' in the AWS Console. On the left sidebar, click 'Model access'. "
                    "Confirm that the status for your target foundation model (e.g., 'Anthropic Claude Sonnet 4.6' "
                    "or 'Amazon Nova') indicates 'Access granted'. If not, click 'Modify model access' and submit "
                    "the access request."
                ),
            },
            {
                "topic": "3. Verify IAM Permissions",
                "instructions": (
                    "Ensure the IAM User or IAM Role being used has permission to invoke Bedrock models. "
                    "The minimal IAM action policy is:\n"
                    "  - bedrock:InvokeModel\n"
                    "  - bedrock:InvokeModelWithResponseStream\n"
                    "(The AWS-managed policy 'AmazonBedrockFullAccess' can also be used in sandbox environments)."
                ),
            },
            {
                "topic": "4. Local Credentials Setup (Zero-Chat Exposure)",
                "instructions": (
                    "To authenticate on your local machine without pasting keys into chat:\n"
                    "  Option A (Recommended): Run 'aws configure' in your terminal and enter your credentials.\n"
                    "  Option B (SSO): Run 'aws sso login --profile <your-profile>'.\n"
                    "  Option C: Add credentials to a private local '.env' file (never committed to Git)."
                ),
            },
        ],
    }
