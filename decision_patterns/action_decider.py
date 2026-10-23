"""Strands Decider 2B Action Decision Module.

Stage 4: Typed decision integration for selecting resume workflow actions
(ANALYZE_RESUME, MATCH_JOB, IMPROVE_RESUME) according to official Strands Decider 2B
System 1 specifications.
"""

from dataclasses import dataclass
from enum import Enum
import os
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import requests

load_dotenv()


class ResumeAction(str, Enum):
    """Allowed actions for ResumePilot AI workflows."""

    ANALYZE_RESUME = "ANALYZE_RESUME"
    MATCH_JOB = "MATCH_JOB"
    IMPROVE_RESUME = "IMPROVE_RESUME"


# Official Strands Decider 2B question definition for choice classification
DECIDER_QUESTION_ID = "action_selection"
DECIDER_INSTRUCTIONS = (
    "Evaluate candidate resume text, target job description, and user instructions "
    "to select the single most appropriate career action."
)

DECIDER_CRITERIA: Dict[str, str] = {
    ResumeAction.ANALYZE_RESUME.value: (
        "Perform a comprehensive structural and skills audit, identifying gaps, strengths, "
        "and formatting opportunities without requiring a target job description."
    ),
    ResumeAction.MATCH_JOB.value: (
        "Evaluate the alignment between candidate qualifications and a specific target job "
        "description, analyzing keyword density, prerequisites, and match fitness."
    ),
    ResumeAction.IMPROVE_RESUME.value: (
        "Synthesize targeted resume improvements, rewrite bullet points with measurable impact, "
        "and polish content for clarity and executive tone."
    ),
}


@dataclass
class DecisionInput:
    """Typed inputs required for Strands Decider action evaluation."""

    resume_text: str
    job_description: str = ""
    user_request: str = ""
    manual_action: Optional[ResumeAction] = None

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate input constraints before submitting to decider."""
        errors: List[str] = []

        if not self.resume_text or not self.resume_text.strip():
            errors.append("Resume content is empty. A valid resume is required.")

        # If MATCH_JOB is specifically requested, job description is mandatory
        if self.manual_action == ResumeAction.MATCH_JOB and not self.job_description.strip():
            errors.append("Target job description is required for MATCH_JOB evaluation.")

        return len(errors) == 0, errors


@dataclass
class DecisionOutput:
    """Expected output schema from Strands Decider 2B."""

    selected_action: Optional[ResumeAction]
    confidence: Optional[float]
    status: str  # "PENDING_INTEGRATION", "COMPLETED", "VALIDATION_ERROR", "ERROR"
    message: str
    systemone_payload: Optional[Dict[str, Any]] = None
    raw_response: Optional[Dict[str, Any]] = None
    is_ready: bool = False


@dataclass
class AgentWorkflowContext:
    """Carries the decision outcome and inputs into the Strands Agent workflow."""

    action: ResumeAction
    resume_text: str
    job_description: str
    user_request: str
    strategy_note: str


def get_decider_config() -> Dict[str, str]:
    """Retrieve Strands Decider 2B endpoint and model configurations."""
    return {
        "endpoint": os.getenv(
            "STRANDS_DECIDER_ENDPOINT", "http://localhost:11434/v1/systemone"
        ),
        "model_id": os.getenv(
            "STRANDS_DECIDER_MODEL_ID", "StrandsAgents/strands-decider-2B-qwen3.5-v1-2610"
        ),
    }


def check_decider_endpoint(endpoint_url: Optional[str] = None) -> Tuple[bool, str]:
    """Verify if the official Strands Decider 2B server or Ollama instance is reachable."""
    config = get_decider_config()
    target_url = endpoint_url or config["endpoint"]

    try:
        # Quick non-blocking ping to base server URL (stripping /v1/systemone)
        base_url = target_url.replace("/v1/systemone", "")
        response = requests.get(base_url, timeout=1.0)
        if response.status_code < 500:
            return True, f"Decider endpoint reachable at {target_url}."
    except Exception:
        pass

    return (
        False,
        f"Strands Decider 2B service is not running at {target_url}. "
        "Local inference server (e.g., 'strands-decider serve' or Ollama) is not active.",
    )


def build_strands_decider_payload(decision_input: DecisionInput) -> Dict[str, Any]:
    """Construct a compliant System 1 payload for Strands Decider 2B."""
    config = get_decider_config()

    # Formulate input state combining available contexts
    state_parts = [f"RESUME CONTENT:\n{decision_input.resume_text.strip()}"]
    if decision_input.job_description.strip():
        state_parts.append(f"TARGET JOB DESCRIPTION:\n{decision_input.job_description.strip()}")
    if decision_input.user_request.strip():
        state_parts.append(f"USER SPECIFIC REQUEST:\n{decision_input.user_request.strip()}")

    state_text = "\n\n".join(state_parts)

    payload = {
        "model": config["model_id"],
        "state": state_text,
        "questions": {
            DECIDER_QUESTION_ID: {
                "type": "choice",
                "instructions": DECIDER_INSTRUCTIONS,
                "criteria": DECIDER_CRITERIA,
            }
        },
    }
    return payload


def evaluate_resume_action_decision(decision_input: DecisionInput) -> DecisionOutput:
    """Evaluate or prepare the typed action decision.

    If the local Strands Decider service is not running, marks integration as pending
    without fabricating fake decisions or confidence values.
    """
    is_valid, errors = decision_input.validate()
    if not is_valid:
        return DecisionOutput(
            selected_action=None,
            confidence=None,
            status="VALIDATION_ERROR",
            message="; ".join(errors),
            is_ready=False,
        )

    payload = build_strands_decider_payload(decision_input)
    is_reachable, reachability_msg = check_decider_endpoint()

    # If the endpoint is not reachable, do NOT pretend a decision occurred
    if not is_reachable:
        return DecisionOutput(
            selected_action=None,
            confidence=None,
            status="PENDING_INTEGRATION",
            message=(
                f"Strands Decider 2B endpoint pending: {reachability_msg}\n"
                "In Stage 4, the verified interface and payload schema are prepared, "
                "but no mock decisions or fake confidence metrics are generated."
            ),
            systemone_payload=payload,
            is_ready=False,
        )

    # If endpoint IS reachable, perform real HTTP POST
    config = get_decider_config()
    try:
        response = requests.post(config["endpoint"], json=payload, timeout=5.0)
        if response.status_code == 200:
            result_data = response.json()
            # Parse official answer structure
            answer_data = (
                result_data.get("answers", {}).get(DECIDER_QUESTION_ID, {})
                or result_data.get(DECIDER_QUESTION_ID, {})
            )
            choice_str = answer_data.get("choice") or answer_data.get("answer")
            confidence_val = answer_data.get("confidence") or answer_data.get("probability")

            selected_action = None
            if choice_str in [a.value for a in ResumeAction]:
                selected_action = ResumeAction(choice_str)

            return DecisionOutput(
                selected_action=selected_action,
                confidence=confidence_val,
                status="COMPLETED",
                message=f"Strands Decider 2B selected action: {selected_action}",
                systemone_payload=payload,
                raw_response=result_data,
                is_ready=True,
            )
        else:
            return DecisionOutput(
                selected_action=None,
                confidence=None,
                status="ERROR",
                message=f"Strands Decider server returned HTTP {response.status_code}: {response.text}",
                systemone_payload=payload,
                is_ready=False,
            )
    except Exception as exc:
        return DecisionOutput(
            selected_action=None,
            confidence=None,
            status="ERROR",
            message=f"Failed to communicate with Strands Decider server: {str(exc)}",
            systemone_payload=payload,
            is_ready=False,
        )


def prepare_agent_workflow_context(
    action: ResumeAction,
    decision_input: DecisionInput,
) -> AgentWorkflowContext:
    """Route selected action into agent workflow execution context."""
    strategy_descriptions = {
        ResumeAction.ANALYZE_RESUME: "Audit resume structure, identify missing skills, and rate section impact.",
        ResumeAction.MATCH_JOB: "Calculate alignment against target job requirements, highlighting overlap and gaps.",
        ResumeAction.IMPROVE_RESUME: "Rewrite bullet points using Action-Context-Result (ACR) model for maximum clarity.",
    }

    return AgentWorkflowContext(
        action=action,
        resume_text=decision_input.resume_text,
        job_description=decision_input.job_description,
        user_request=decision_input.user_request,
        strategy_note=strategy_descriptions.get(action, "Execute designated career workflow."),
    )
