# ResumePilot AI

> **Smarter Resumes. Better Job Matches. Stronger Careers.**

ResumePilot AI is an AI-powered resume analysis, job matching, and resume improvement application built with Python and Streamlit.

---

## Project Structure

```text
ResumePilot AI/
├── agent/                  # Orchestration logic and agent workflows
│   └── __init__.py
├── services/               # Parsing services, external integrations, model clients
│   └── __init__.py
├── decision_patterns/      # Strategic routing, deciders, and heuristics
│   └── __init__.py
├── tests/                  # Automated tests (pytest)
│   └── __init__.py
├── app.py                  # Main Streamlit dashboard application
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules for Python & environments
└── README.md               # Project documentation
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (Verified on Python 3.13)

### 2. Set Up a Virtual Environment (Recommended)

In PowerShell or Command Prompt, run:

```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment:
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows CMD:
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
copy .env.example .env
```

*(Note: In this initial stage, no external API credentials or AWS keys are required.)*

### 5. Launch the Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` to view the dashboard.
