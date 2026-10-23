"""Unit tests for ResumePilot AI input validation logic."""

from types import SimpleNamespace
import unittest
from app import validate_action_inputs


class TestInputValidation(unittest.TestCase):
    def test_missing_file_fails_validation(self):
        is_valid, errors = validate_action_inputs("Analyze Resume", None, "")
        self.assertFalse(is_valid)
        self.assertTrue(any("upload your resume" in err.lower() for err in errors))

    def test_unsupported_file_extension(self):
        mock_file = SimpleNamespace(name="resume.txt", size=1024)
        is_valid, errors = validate_action_inputs("Analyze Resume", mock_file, "")
        self.assertFalse(is_valid)
        self.assertTrue(any("unsupported format" in err.lower() for err in errors))

    def test_valid_pdf_file_for_analysis(self):
        mock_file = SimpleNamespace(name="my_resume.pdf", size=2048)
        is_valid, errors = validate_action_inputs("Analyze Resume", mock_file, "")
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_valid_docx_file_for_analysis(self):
        mock_file = SimpleNamespace(name="my_resume.docx", size=3072)
        is_valid, errors = validate_action_inputs("Analyze Resume", mock_file, "")
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_job_matching_requires_job_description(self):
        mock_file = SimpleNamespace(name="my_resume.pdf", size=2048)
        is_valid, errors = validate_action_inputs("Job Matching", mock_file, "")
        self.assertFalse(is_valid)
        self.assertTrue(any("job description is required" in err.lower() for err in errors))

    def test_job_matching_passes_when_both_provided(self):
        mock_file = SimpleNamespace(name="my_resume.pdf", size=2048)
        is_valid, errors = validate_action_inputs(
            "Job Matching",
            mock_file,
            "Looking for a Python software engineer with 3+ years experience.",
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
