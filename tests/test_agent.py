"""Unit tests for ResumePilot AI Strands Agent foundation."""

import os
import unittest
from unittest.mock import patch

from agent.resume_agent import (
    check_agent_prerequisites,
    create_resume_agent,
    get_agent_config,
)


class TestAgentFoundation(unittest.TestCase):
    def test_get_agent_config_defaults(self):
        config = get_agent_config()
        self.assertIn("aws_region", config)
        self.assertIn("bedrock_model_id", config)
        self.assertIn("claude", config["bedrock_model_id"].lower())

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials_shows_setup_message_without_crashing(self):
        with patch("boto3.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            mock_session.get_credentials.return_value = None

            prereqs = check_agent_prerequisites()
            self.assertFalse(prereqs.is_ready)
            self.assertTrue(any("credentials" in item.lower() for item in prereqs.missing_items))

            agent, msg = create_resume_agent()
            self.assertIsNone(agent)
            self.assertIn("Setup Incomplete", msg)

    @patch.dict(
        os.environ,
        {
            "AWS_ACCESS_KEY_ID": "mock_access_key",
            "AWS_SECRET_ACCESS_KEY": "mock_secret_key",
            "AWS_REGION": "us-east-1",
            "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-6",
        },
    )
    def test_configured_credentials_initializes_agent_without_bedrock_calls(self):
        prereqs = check_agent_prerequisites()
        self.assertTrue(prereqs.is_ready)

        agent, msg = create_resume_agent()
        self.assertIsNotNone(agent)
        self.assertIn("verified", msg.lower())


if __name__ == "__main__":
    unittest.main()
