"""Unit tests for Amazon Bedrock configuration and health-check service."""

import os
import unittest
from unittest.mock import MagicMock, patch

from services.bedrock_service import (
    DEFAULT_AWS_REGION,
    DEFAULT_BEDROCK_MODEL_ID,
    check_bedrock_health,
    get_aws_console_verification_guide,
    get_bedrock_config,
    mask_access_key,
)


class TestBedrockService(unittest.TestCase):
    def test_mask_access_key(self):
        """Ensure access key is masked safely and secret key is never touched."""
        self.assertIsNone(mask_access_key(None))
        self.assertIsNone(mask_access_key(""))
        self.assertEqual(mask_access_key("AKIA1234567890ABCDEF"), "AKIA...CDEF")
        self.assertEqual(mask_access_key("SHORT"), "******")

    def test_default_bedrock_config(self):
        """Ensure standard defaults are loaded when env is empty."""
        self.assertEqual(DEFAULT_BEDROCK_MODEL_ID, "us.anthropic.claude-sonnet-4-6")
        self.assertEqual(DEFAULT_AWS_REGION, "us-east-1")
        with patch.dict(os.environ, {}, clear=True):
            cfg = get_bedrock_config()
            self.assertEqual(cfg.region, DEFAULT_AWS_REGION)
            self.assertEqual(cfg.model_id, DEFAULT_BEDROCK_MODEL_ID)
            self.assertIsNone(cfg.profile_name)

    def test_custom_bedrock_config(self):
        """Ensure custom environment variables are read properly."""
        custom_env = {
            "AWS_REGION": "us-west-2",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0",
            "AWS_PROFILE": "dev-profile",
        }
        with patch.dict(os.environ, custom_env, clear=True):
            cfg = get_bedrock_config()
            self.assertEqual(cfg.region, "us-west-2")
            self.assertEqual(cfg.model_id, "anthropic.claude-3-sonnet-20240229-v1:0")
            self.assertEqual(cfg.profile_name, "dev-profile")

    @patch("boto3.Session")
    def test_missing_credentials_reported_safely(self, mock_session_cls):
        """When credentials are absent, reports unconfigured safely without crashing."""
        mock_session = mock_session_cls.return_value
        mock_session.get_credentials.return_value = None

        with patch.dict(os.environ, {}, clear=True):
            health = check_bedrock_health()
            self.assertFalse(health.is_configured)
            self.assertIsNone(health.masked_key)
            self.assertFalse(health.inference_enabled)
            self.assertTrue(any("credentials" in item.lower() for item in health.missing_items))

    @patch("boto3.client")
    @patch("boto3.Session")
    def test_discovered_credentials_identified_safely(self, mock_session_cls, mock_boto_client):
        """When credentials are discovered, verifies client without enabling inference."""
        mock_creds = MagicMock()
        mock_creds.access_key = "AKIA9876543210ZYXWVU"
        mock_creds.secret_key = "dummy_secret_not_logged"
        mock_creds.token = None
        mock_creds.method = "shared-credentials-file"

        mock_session = mock_session_cls.return_value
        mock_session.get_credentials.return_value = mock_creds

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            health = check_bedrock_health()
            self.assertTrue(health.is_configured)
            self.assertEqual(health.masked_key, "AKIA...XWVU")
            self.assertIn("Shared Credentials File", health.credential_source)
            self.assertTrue(health.can_initialize_client)
            # Critical constraint: live inference must remain disabled
            self.assertFalse(health.inference_enabled)

    @patch("boto3.client")
    @patch("boto3.Session")
    def test_login_credential_provider_identified(self, mock_session_cls, mock_boto_client):
        """When login credential provider (SSO/Token) is used, identifies credential source correctly."""
        mock_creds = MagicMock()
        mock_creds.access_key = "ASIA1234567890ABCDEF"
        mock_creds.secret_key = "dummy_secret"
        mock_creds.token = "dummy_token"
        mock_creds.method = "login"

        mock_session = mock_session_cls.return_value
        mock_session.get_credentials.return_value = mock_creds

        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            health = check_bedrock_health()
            self.assertTrue(health.is_configured)
            self.assertEqual(health.masked_key, "ASIA...CDEF")
            self.assertIn("Login Credential Provider", health.credential_source)
            self.assertTrue(health.can_initialize_client)
            self.assertFalse(health.inference_enabled)

    @patch("boto3.Session")
    def test_missing_crt_dependency_error_handled(self, mock_session_cls):
        """When botocore raises a CRT missing dependency error, reports it clearly."""
        mock_session = mock_session_cls.return_value
        mock_session.get_credentials.side_effect = Exception(
            'Using the login credential provider requires an additional dependency. You will need to pip install "botocore[crt]"'
        )

        with patch.dict(os.environ, {}, clear=True):
            health = check_bedrock_health()
            self.assertFalse(health.is_configured)
            self.assertTrue(any("botocore[crt]" in item.lower() for item in health.missing_items))

    def test_verification_guide_contents(self):
        """Ensure verification guide has topics for region, model access, and IAM."""
        guide = get_aws_console_verification_guide()
        self.assertIn("steps", guide)
        topics = [s["topic"].lower() for s in guide["steps"]]
        self.assertTrue(any("region" in t for t in topics))
        self.assertTrue(any("model access" in t for t in topics))
        self.assertTrue(any("iam" in t for t in topics))


if __name__ == "__main__":
    unittest.main()
