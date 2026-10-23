"""Unit tests for UI analysis helpers and keyword comparison."""

import unittest
from ui.analysis_helpers import (
    compare_resume_to_job,
    compute_structural_metrics,
)


class TestUIAnalysisHelpers(unittest.TestCase):
    def test_compute_metrics_empty(self):
        metrics = compute_structural_metrics("")
        self.assertEqual(metrics.word_count, 0)
        self.assertEqual(metrics.char_count, 0)
        self.assertEqual(metrics.reading_time_minutes, 0.0)
        self.assertEqual(metrics.bullet_count, 0)
        self.assertEqual(len(metrics.identified_skills), 0)

    def test_compute_metrics_with_content(self):
        sample_resume = """
        John Doe
        Email: john@example.com | Phone: 555-0199
        
        Professional Summary
        Results-driven Cloud Engineer with 4 years experience.
        
        Technical Skills
        Python, AWS, Docker, Kubernetes, SQL, Git, Linux
        
        Work Experience
        Senior Cloud Developer | TechCorp (2021 - Present)
        • Architected microservices on AWS ECS reducing latency by 35%.
        • Automated CI/CD deployment pipelines using GitHub Actions.
        • Spearheaded migration of legacy MySQL databases to Amazon Aurora.
        
        Education
        Bachelor of Science in Computer Science | State University
        """
        metrics = compute_structural_metrics(sample_resume)
        self.assertGreater(metrics.word_count, 40)
        self.assertGreater(metrics.reading_time_minutes, 0.0)
        self.assertEqual(metrics.bullet_count, 3)
        self.assertTrue(metrics.has_metrics_numbers)
        self.assertIn("Skills & Competencies", metrics.detected_sections)
        self.assertIn("Work Experience", metrics.detected_sections)
        self.assertIn("Education", metrics.detected_sections)
        self.assertIn("Python", metrics.identified_skills)
        self.assertIn("AWS", metrics.identified_skills)
        self.assertIn("Docker", metrics.identified_skills)
        self.assertIn("Architected", metrics.strong_verbs_found)
        self.assertIn("Spearheaded", metrics.strong_verbs_found)

    def test_compare_resume_to_job_empty(self):
        comparison = compare_resume_to_job("", "")
        self.assertEqual(comparison.match_percentage, 0.0)
        self.assertEqual(len(comparison.matched_skills), 0)
        self.assertEqual(len(comparison.missing_skills), 0)
        self.assertFalse(comparison.has_meaningful_match)

    def test_compare_resume_to_job_overlap(self):
        resume = "Experienced with Python, AWS, Docker, Git, and Linux."
        jd = "Seeking a Software Engineer skilled in Python, AWS, Kubernetes, Terraform, and Docker."

        comp = compare_resume_to_job(resume, jd)
        self.assertTrue(comp.has_meaningful_match)
        self.assertIn("Python", comp.matched_skills)
        self.assertIn("AWS", comp.matched_skills)
        self.assertIn("Docker", comp.matched_skills)
        self.assertIn("Kubernetes", comp.missing_skills)
        self.assertIn("Terraform", comp.missing_skills)
        self.assertEqual(comp.total_jd_skills, 5)
        self.assertEqual(comp.match_percentage, 60.0)


if __name__ == "__main__":
    unittest.main()
