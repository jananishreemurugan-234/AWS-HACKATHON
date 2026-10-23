"""Unit tests for Strands Decider 2B decision pattern module."""

import unittest
from unittest.mock import MagicMock, patch

from decision_patterns.action_decider import (
    DECIDER_CRITERIA,
    DECIDER_QUESTION_ID,
    DecisionInput,
    ResumeAction,
    build_strands_decider_payload,
    evaluate_resume_action_decision,
    prepare_agent_workflow_context,
)


class TestStrandsDecider(unittest.TestCase):
    def test_allowed_actions_enum(self):
        """Ensure allowed actions match specified values exactly."""
        actions = {a.value for a in ResumeAction}
        expected = {"ANALYZE_RESUME", "MATCH_JOB", "IMPROVE_RESUME"}
        self.assertEqual(actions, expected)

    def test_decision_input_validation_empty_resume(self):
        """Validation fails if resume content is missing."""
        inp = DecisionInput(resume_text="")
        is_valid, errors = inp.validate()
        self.assertFalse(is_valid)
        self.assertTrue(any("resume content is empty" in e.lower() for e in errors))

    def test_decision_input_validation_match_job_requires_jd(self):
        """Validation fails if MATCH_JOB is requested without job description."""
        inp = DecisionInput(
            resume_text="Senior Python Developer with AWS experience.",
            job_description="",
            manual_action=ResumeAction.MATCH_JOB,
        )
        is_valid, errors = inp.validate()
        self.assertFalse(is_valid)
        self.assertTrue(any("job description is required" in e.lower() for e in errors))

    def test_decision_input_validation_passes(self):
        """Validation passes with valid inputs."""
        inp = DecisionInput(
            resume_text="Senior Python Developer with AWS experience.",
            job_description="Seeking AWS Cloud Engineer.",
            manual_action=ResumeAction.MATCH_JOB,
        )
        is_valid, errors = inp.validate()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_build_strands_decider_payload_schema(self):
        """Verify payload matches official Strands Decider 2B choice schema."""
        inp = DecisionInput(
            resume_text="Sample Resume Content",
            job_description="Sample Job Description",
            user_request="Focus on cloud skills",
        )
        payload = build_strands_decider_payload(inp)

        self.assertIn("model", payload)
        self.assertIn("state", payload)
        self.assertIn("questions", payload)
        self.assertIn(DECIDER_QUESTION_ID, payload["questions"])

        question_obj = payload["questions"][DECIDER_QUESTION_ID]
        self.assertEqual(question_obj["type"], "choice")
        self.assertIn("instructions", question_obj)
        self.assertIn("criteria", question_obj)

        for action in ResumeAction:
            self.assertIn(action.value, question_obj["criteria"])

    @patch("decision_patterns.action_decider.check_decider_endpoint")
    def test_unreachable_endpoint_returns_pending_without_fake_data(self, mock_check):
        """When decider server is offline, returns PENDING_INTEGRATION with no fake values."""
        mock_check.return_value = (False, "Endpoint offline")

        inp = DecisionInput(resume_text="Sample Resume Text")
        output = evaluate_resume_action_decision(inp)

        self.assertEqual(output.status, "PENDING_INTEGRATION")
        self.assertIsNone(output.selected_action)
        self.assertIsNone(output.confidence)
        self.assertFalse(output.is_ready)
        self.assertIn("pending", output.message.lower())
        self.assertIsNotNone(output.systemone_payload)

    @patch("decision_patterns.action_decider.check_decider_endpoint")
    @patch("requests.post")
    def test_live_decider_response_parsing(self, mock_post, mock_check):
        """Verify parsing when a real decider response is received."""
        mock_check.return_value = (True, "Endpoint reachable")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "answers": {
                DECIDER_QUESTION_ID: {
                    "choice": "MATCH_JOB",
                    "confidence": 0.94,
                }
            }
        }
        mock_post.return_value = mock_resp

        inp = DecisionInput(
            resume_text="Python Engineer",
            job_description="Python Job",
        )
        output = evaluate_resume_action_decision(inp)

        self.assertEqual(output.status, "COMPLETED")
        self.assertEqual(output.selected_action, ResumeAction.MATCH_JOB)
        self.assertEqual(output.confidence, 0.94)
        self.assertTrue(output.is_ready)

    def test_prepare_agent_workflow_context(self):
        """Verify routing into agent workflow context."""
        inp = DecisionInput(
            resume_text="Resume Data",
            job_description="Job Data",
            user_request="User Instructions",
        )
        ctx = prepare_agent_workflow_context(ResumeAction.IMPROVE_RESUME, inp)

        self.assertEqual(ctx.action, ResumeAction.IMPROVE_RESUME)
        self.assertEqual(ctx.resume_text, "Resume Data")
        self.assertEqual(ctx.job_description, "Job Data")
        self.assertEqual(ctx.user_request, "User Instructions")
        self.assertTrue(len(ctx.strategy_note) > 0)


if __name__ == "__main__":
    unittest.main()
