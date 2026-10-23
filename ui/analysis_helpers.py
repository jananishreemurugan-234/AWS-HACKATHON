"""ResumePilot AI - Structural Analysis & Keyword Matching Helpers.

Computes genuine, deterministic metrics directly from extracted resume
text and job descriptions without fabricating AI responses or fake scores.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Set, Tuple


# Curated standard skills vocabulary across Tech, Cloud, Data, and Management
KNOWN_SKILLS = [
    # Programming & Frameworks
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
    "SQL", "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
    "Spring Boot", "Next.js", "GraphQL", "REST APIs", "gRPC",
    # Cloud & DevOps
    "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes",
    "Terraform", "CI/CD", "Linux", "Git", "GitHub", "Jenkins", "Ansible", "CloudFormation",
    "Bedrock", "Lambda", "EC2", "S3", "CloudWatch", "Serverless",
    # Data & AI/ML
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "PyTorch", "TensorFlow",
    "Pandas", "NumPy", "Scikit-Learn", "Spark", "Kafka", "PostgreSQL", "MySQL", "MongoDB",
    "Redis", "Elasticsearch", "Airflow", "Snowflake", "Databricks",
    # Architecture, Methods & Soft Skills
    "Microservices", "System Design", "Agile", "Scrum", "DevOps", "Unit Testing",
    "TDD", "Integration Testing", "Security", "IAM", "Project Management", "Leadership",
    "Problem Solving", "Cross-Functional Collaboration", "Code Review", "Data Analysis",
]

# Standard resume section headings
SECTION_PATTERNS = {
    "Contact Information": r"\b(email|phone|linkedin|github|portfolio|address|contact)\b",
    "Summary / Objective": r"\b(professional summary|career objective|about me|summary|executive summary)\b",
    "Work Experience": r"\b(experience|employment history|work history|professional experience)\b",
    "Education": r"\b(education|academic background|degree|university|college)\b",
    "Skills & Competencies": r"\b(technical skills|skills|technologies|core competencies|tooling)\b",
    "Projects": r"\b(projects|key projects|personal projects|notable work)\b",
    "Certifications": r"\b(certifications|credentials|licenses|accreditations)\b",
}

# Strong action verbs vs passive phrases
STRONG_ACTION_VERBS = [
    "Architected", "Spearheaded", "Engineered", "Implemented", "Optimized",
    "Reduced", "Increased", "Accelerated", "Delivered", "Automated",
    "Designed", "Developed", "Led", "Streamlined", "Orchestrated",
]

PASSIVE_PHRASES = [
    "Responsible for", "Helped with", "Worked on", "Assisted in", "Tasked with",
    "Participated in", "Handled duties of",
]


@dataclass
class StructuralMetrics:
    """Deterministic structural properties of candidate resume."""
    word_count: int
    char_count: int
    reading_time_minutes: float
    bullet_count: int
    has_metrics_numbers: bool
    detected_sections: List[str]
    missing_sections: List[str]
    identified_skills: List[str]
    strong_verbs_found: List[str]
    passive_phrases_found: List[str]


def compute_structural_metrics(resume_text: str) -> StructuralMetrics:
    """Analyze real structural composition of the parsed resume."""
    if not resume_text or not resume_text.strip():
        return StructuralMetrics(
            word_count=0,
            char_count=0,
            reading_time_minutes=0.0,
            bullet_count=0,
            has_metrics_numbers=False,
            detected_sections=[],
            missing_sections=list(SECTION_PATTERNS.keys()),
            identified_skills=[],
            strong_verbs_found=[],
            passive_phrases_found=[],
        )

    words = resume_text.split()
    word_count = len(words)
    char_count = len(resume_text)
    reading_time = round(word_count / 220.0, 1)  # standard ~220 WPM reading speed

    # Count bullet points
    bullet_count = len(re.findall(r"(?:^|\n)\s*[•\-\*\u2022\u2023\u25E6]\s+", resume_text))

    # Detect numerical metrics (e.g. 40%, $100K, 15ms, 1,000+ users)
    metrics_match = re.search(r"(\d+[\%kmb\+]?|\$\d+|\d+\s*(?:percent|users|ms|req/s|x))", resume_text, re.IGNORECASE)
    has_metrics_numbers = metrics_match is not None

    # Detect sections
    detected_sections: List[str] = []
    missing_sections: List[str] = []
    text_lower = resume_text.lower()

    for sec_name, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, text_lower):
            detected_sections.append(sec_name)
        else:
            missing_sections.append(sec_name)

    # Extract detected skills from text
    identified_skills: Set[str] = set()
    for skill in KNOWN_SKILLS:
        # Match as whole word/phrase
        escaped_skill = re.escape(skill)
        if re.search(rf"\b{escaped_skill}\b", resume_text, re.IGNORECASE):
            identified_skills.add(skill)

    # Strong action verbs vs passive phrases
    strong_verbs_found = [v for v in STRONG_ACTION_VERBS if re.search(rf"\b{re.escape(v)}\b", resume_text, re.IGNORECASE)]
    passive_phrases_found = [p for p in PASSIVE_PHRASES if re.search(rf"\b{re.escape(p)}\b", resume_text, re.IGNORECASE)]

    return StructuralMetrics(
        word_count=word_count,
        char_count=char_count,
        reading_time_minutes=reading_time,
        bullet_count=bullet_count,
        has_metrics_numbers=has_metrics_numbers,
        detected_sections=detected_sections,
        missing_sections=missing_sections,
        identified_skills=sorted(list(identified_skills)),
        strong_verbs_found=strong_verbs_found,
        passive_phrases_found=passive_phrases_found,
    )


@dataclass
class JobMatchComparison:
    """Genuine keyword match comparison between resume and job description."""
    matched_skills: List[str]
    missing_skills: List[str]
    match_percentage: float
    total_jd_skills: int
    has_meaningful_match: bool


def compare_resume_to_job(resume_text: str, job_description: str) -> JobMatchComparison:
    """Compare candidate resume directly against job description keywords."""
    if not resume_text.strip() or not job_description.strip():
        return JobMatchComparison(
            matched_skills=[],
            missing_skills=[],
            match_percentage=0.0,
            total_jd_skills=0,
            has_meaningful_match=False,
        )

    # Find which skills exist in the Job Description
    jd_skills: Set[str] = set()
    for skill in KNOWN_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", job_description, re.IGNORECASE):
            jd_skills.add(skill)

    if not jd_skills:
        # Fallback: extract prominent capitalized words/technical terms from JD
        jd_words = re.findall(r"\b[A-Z][a-zA-Z0-9\+\#\.\-]{2,}\b", job_description)
        common_words = {"The", "And", "You", "Our", "We", "Will", "With", "Are", "For", "Job", "Role"}
        filtered_words = {w for w in jd_words if w not in common_words}
        jd_skills = set(list(filtered_words)[:15])

    # Find which of those skills exist in candidate resume
    matched: Set[str] = set()
    missing: Set[str] = set()

    for skill in jd_skills:
        if re.search(rf"\b{re.escape(skill)}\b", resume_text, re.IGNORECASE):
            matched.add(skill)
        else:
            missing.add(skill)

    total = len(jd_skills)
    match_pct = round((len(matched) / total * 100.0), 1) if total > 0 else 0.0

    return JobMatchComparison(
        matched_skills=sorted(list(matched)),
        missing_skills=sorted(list(missing)),
        match_percentage=match_pct,
        total_jd_skills=total,
        has_meaningful_match=total > 0,
    )
