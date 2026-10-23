"""ResumePilot AI - Strands Agent Foundation

Stage 5: Secure Bedrock configuration integration and agent initialization
without executing remote model inference.
"""

from dataclasses import dataclass
import os
from typing import List, Optional, Tuple
from dotenv import load_dotenv

from services.bedrock_service import (
    DEFAULT_AWS_REGION,
    DEFAULT_BEDROCK_MODEL_ID,
    BedrockHealthResult,
    check_bedrock_health,
    get_bedrock_config,
)

# Load local environment configuration if present
load_dotenv()

# System prompt defining ResumePilot AI's core behavior
RESUME_PILOT_SYSTEM_PROMPT = """You are ResumePilot AI, an expert executive resume strategist and career coach.
Your mission is to provide rigorous, actionable, and objective career advice, including:
1. Identifying structural, technical, and qualitative gaps in resumes.
2. Aligning candidate achievements against target job descriptions.
3. Enhancing resume bullet points using the Action-Context-Result (ACR) framework with measurable impact.
4. Providing realistic career trajectory advice without fabricating metrics or false praise.

Always maintain objectivity, high professional standards, and precision in your analysis.
"""


@dataclass
class AgentPrerequisitesResult:
    """Holds status of Strands Agents prerequisites and environment variables."""

    is_ready: bool
    missing_items: List[str]
    setup_message: str
    region: str
    model_id: str
    credential_source: str
    can_initialize_client: bool


def get_agent_config() -> dict:
    """Read agent and model configuration from environment variables."""
    cfg = get_bedrock_config()
    return {
        "aws_region": cfg.region,
        "bedrock_model_id": cfg.model_id,
        "aws_profile": cfg.profile_name,
    }


def check_agent_prerequisites() -> AgentPrerequisitesResult:
    """Check whether Strands Agents and Bedrock prerequisites are met safely."""
    bedrock_health = check_bedrock_health()
    missing: List[str] = list(bedrock_health.missing_items)

    # Check for SDK presence
    try:
        import strands  # noqa: F401
    except ImportError:
        missing.append("strands-agents SDK (pip install strands-agents)")

    is_ready = bedrock_health.is_configured and ("strands-agents SDK" not in str(missing))

    if is_ready:
        setup_message = (
            f"✅ Strands Agent environment verified.\n"
            f"- Credential Source: {bedrock_health.credential_source}\n"
            f"- Target Region: `{bedrock_health.region}`\n"
            f"- Model ID: `{bedrock_health.model_id}`\n"
            f"- Key Identifier: `{bedrock_health.masked_key or 'Managed by Provider'}`\n"
            f"- Live Inference: Disabled (Stage 5 safety constraint)"
        )
    else:
        instructions = [
            "⚠️ **Strands Agent & Bedrock Setup Incomplete:**",
            f"- Missing components: {', '.join(missing)}.",
            "- Credentials can be provided via standard AWS CLI (`aws configure`), AWS SSO, IAM roles, or local `.env`.",
            "- Secrets or long-term keys are never hardcoded or exposed.",
            "- In Stage 5, actual model inference remains safely disabled until access is confirmed in AWS Console.",
        ]
        setup_message = "\n".join(instructions)

    return AgentPrerequisitesResult(
        is_ready=is_ready,
        missing_items=missing,
        setup_message=setup_message,
        region=bedrock_health.region,
        model_id=bedrock_health.model_id,
        credential_source=bedrock_health.credential_source,
        can_initialize_client=bedrock_health.can_initialize_client,
    )


def create_resume_agent() -> Tuple[Optional[object], str]:
    """Initialize a reusable Strands Agent configured with BedrockModel.

    Does NOT execute any API calls to Amazon Bedrock.
    If prerequisites are missing, returns (None, setup_message) cleanly without crashing.

    Returns:
        Tuple of (agent_instance, status_message)
    """
    prereqs = check_agent_prerequisites()

    if not prereqs.is_ready:
        return None, prereqs.setup_message

    try:
        from strands import Agent
        from strands.models.bedrock import BedrockModel

        cfg = get_bedrock_config()

        # Instantiate BedrockModel client (offline initialization, no remote inference made)
        bedrock_model = BedrockModel(
            model_id=cfg.model_id,
            region_name=cfg.region,
        )

        agent = Agent(
            model=bedrock_model,
            system_prompt=RESUME_PILOT_SYSTEM_PROMPT,
        )

        return agent, prereqs.setup_message

    except Exception as exc:
        error_msg = f"Failed to initialize Strands Agent: {str(exc)}"
        return None, error_msg
