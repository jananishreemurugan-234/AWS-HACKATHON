"""ResumePilot AI - Reusable UI Components.

Provides polished headers, 4-way integration status cards, KPI metrics,
skills tag clouds, and before/after comparison layouts using clean vector
icons and zero emoji clutter.
"""

from typing import List, Optional
import streamlit as st

from decision_patterns import check_decider_endpoint, get_decider_config
from services.bedrock_service import check_bedrock_health
from services.tesseract_service import is_tesseract_installed


# Clean SVG Icon definitions
SVG_DOC = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>'
SVG_SCAN = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"></path><path d="M17 3h2a2 2 0 0 1 2 2v2"></path><path d="M21 17v2a2 2 0 0 1-2 2h-2"></path><path d="M7 21H5a2 2 0 0 1-2-2v-2"></path><line x1="7" y1="12" x2="17" y2="12"></line></svg>'
SVG_CLOUD = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>'
SVG_ROUTER = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"></polygon></svg>'

SVG_AUDIT = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>'
SVG_TARGET = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="22" y1="12" x2="18" y2="12"></line><line x1="6" y1="12" x2="2" y2="12"></line><line x1="12" y1="6" x2="12" y2="2"></line><line x1="12" y1="22" x2="12" y2="18"></line></svg>'
SVG_IMPROVE = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'


def render_brand_header(subtitle: Optional[str] = None):
    """Render the top SaaS hero brand header for ResumePilot AI."""
    default_sub = (
        "AI-Powered Career & Resume Intelligence Platform • Combining Local Privacy-First OCR, "
        "Strands Decider 2B System 1 Action Routing, and Amazon Bedrock Foundation Models."
    )
    st.markdown(
        f"""
        <div class="rp-brand-header">
            <div class="rp-header-badge">AWS Hackathon & College Project Showcase</div>
            <h1 class="rp-header-title">
                <span class="rp-header-logo-icon">{SVG_DOC}</span> ResumePilot AI
            </h1>
            <p class="rp-header-subtitle">{subtitle or default_sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_integration_status_grid():
    """Render the four integration status cards:
    1. Document Parser
    2. OCR Engine (Local Tesseract)
    3. Amazon Bedrock
    4. Strands Decider 2B
    """
    # 1. Document Parser
    parser_status_pill = '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Ready (PDF/DOCX)</span>'
    parser_desc = "pypdf & python-docx native stream extractors"

    # 2. Local OCR Engine
    tesseract_available = is_tesseract_installed()
    if tesseract_available:
        ocr_pill = '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Ready (Tesseract)</span>'
        ocr_desc = "On-device local Tesseract OCR active"
    else:
        ocr_pill = '<span class="rp-status-pill rp-status-pill-setup"><span class="rp-status-dot"></span> Setup Required</span>'
        ocr_desc = "Local binary missing (winget install needed)"

    # 3. Amazon Bedrock
    bedrock_health = check_bedrock_health()
    if bedrock_health.is_configured:
        bedrock_pill = '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Configured</span>'
        bedrock_desc = f"{bedrock_health.region} • {bedrock_health.model_id[:16]}..."
    else:
        bedrock_pill = '<span class="rp-status-pill rp-status-pill-setup"><span class="rp-status-dot"></span> Setup Required</span>'
        bedrock_desc = "SSO / token credentials verification required"

    # 4. Strands Decider 2B
    decider_reachable, _ = check_decider_endpoint()
    decider_config = get_decider_config()
    if decider_reachable:
        decider_pill = '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Connected</span>'
        decider_desc = "System 1 classifier online"
    else:
        decider_pill = '<span class="rp-status-pill rp-status-pill-pending"><span class="rp-status-dot"></span> Pending Integration</span>'
        decider_desc = "Awaiting local inference server at :11434"

    st.markdown(
        f"""
        <div class="rp-status-grid">
            <div class="rp-status-card">
                <div class="rp-status-card-header">
                    <span class="rp-status-card-title">{SVG_DOC} Document Parser</span>
                    {parser_status_pill}
                </div>
                <div class="rp-status-card-desc">{parser_desc}</div>
            </div>
            <div class="rp-status-card">
                <div class="rp-status-card-header">
                    <span class="rp-status-card-title">{SVG_SCAN} OCR Engine</span>
                    {ocr_pill}
                </div>
                <div class="rp-status-card-desc">{ocr_desc}</div>
            </div>
            <div class="rp-status-card">
                <div class="rp-status-card-header">
                    <span class="rp-status-card-title">{SVG_CLOUD} Amazon Bedrock</span>
                    {bedrock_pill}
                </div>
                <div class="rp-status-card-desc">{bedrock_desc}</div>
            </div>
            <div class="rp-status-card">
                <div class="rp-status-card-header">
                    <span class="rp-status-card-title">{SVG_ROUTER} Strands Decider 2B</span>
                    {decider_pill}
                </div>
                <div class="rp-status-card-desc">{decider_desc}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_file_summary_card(
    filename: str,
    file_size_kb: float,
    char_count: int,
    is_ocr: bool = False,
):
    """Render a clean summary card for uploaded & parsed resume document."""
    ocr_tag = " • <span style='color:#0891b2; font-weight:600;'>Local OCR Extracted</span>" if is_ocr else ""
    st.markdown(
        f"""
        <div class="rp-file-summary-card">
            <div class="rp-file-summary-left">
                <div class="rp-file-icon">{SVG_DOC}</div>
                <div>
                    <h4 class="rp-file-title">{filename}</h4>
                    <p class="rp-file-meta">{file_size_kb:.1f} KB • {char_count:,} characters extracted{ocr_tag}</p>
                </div>
            </div>
            <span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Parsed Successfully</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_metrics(
    word_count: int,
    char_count: int,
    reading_time: float,
    skills_count: int,
):
    """Render key metrics for structural resume evaluation."""
    st.markdown(
        f"""
        <div class="rp-kpi-grid">
            <div class="rp-kpi-card">
                <div class="rp-kpi-label">Total Words</div>
                <div class="rp-kpi-val">{word_count:,}</div>
                <div class="rp-kpi-sub">Target: 400 - 800 words</div>
            </div>
            <div class="rp-kpi-card">
                <div class="rp-kpi-label">Character Count</div>
                <div class="rp-kpi-val">{char_count:,}</div>
                <div class="rp-kpi-sub">Text layer density</div>
            </div>
            <div class="rp-kpi-card">
                <div class="rp-kpi-label">Estimated Read Time</div>
                <div class="rp-kpi-val">{reading_time} min</div>
                <div class="rp-kpi-sub">Recruiter scan window: ~30s</div>
            </div>
            <div class="rp-kpi-card">
                <div class="rp-kpi-label">Identified Core Skills</div>
                <div class="rp-kpi-val">{skills_count}</div>
                <div class="rp-kpi-sub">Recognized keyword tags</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_skills_chips(matched_skills: List[str], missing_skills: List[str]):
    """Visually distinguish matched and missing skills with chips."""
    if not matched_skills and not missing_skills:
        st.info("No target skills extracted. Provide a job description to view skill alignment.")
        return

    if matched_skills:
        st.markdown(
            f"**Matched Qualifications ({len(matched_skills)}):**"
        )
        chips_html = "".join(
            f'<span class="rp-skill-chip rp-skill-matched">{skill}</span>'
            for skill in matched_skills
        )
        st.markdown(f'<div class="rp-skills-container">{chips_html}</div>', unsafe_allow_html=True)

    if missing_skills:
        st.markdown(
            f"**Missing Qualifications ({len(missing_skills)}):**"
        )
        chips_html = "".join(
            f'<span class="rp-skill-chip rp-skill-missing">{skill}</span>'
            for skill in missing_skills
        )
        st.markdown(f'<div class="rp-skills-container">{chips_html}</div>', unsafe_allow_html=True)


def render_comparison_item(
    category: str,
    original_text: str,
    improved_text: str,
    rationale: str,
):
    """Render an attractive before/after resume enhancement diff card with rationale and copy controls."""
    st.markdown(
        f"""
        <div class="rp-compare-card">
            <div class="rp-compare-header">
                <span class="rp-compare-category">{category}</span>
                <span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Google X-Y-Z Standard</span>
            </div>
            <div class="rp-diff-row">
                <div class="rp-diff-box rp-diff-original">
                    <div class="rp-diff-label rp-diff-label-original">Before (Routine / Passive Phrase)</div>
                    <div class="rp-diff-text">{original_text}</div>
                </div>
                <div class="rp-diff-box rp-diff-improved">
                    <div class="rp-diff-label rp-diff-label-improved">After (Measurable Impact Achievement)</div>
                    <div class="rp-diff-text">{improved_text}</div>
                </div>
            </div>
            <div class="rp-diff-rationale">
                <strong>Strategy & Rationale:</strong> {rationale}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Click to Copy Formatted Bullet Point", expanded=False):
        st.code(improved_text, language="text")
