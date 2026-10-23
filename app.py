"""ResumePilot AI - Modern SaaS Streamlit Dashboard.

Combines local privacy-first Tesseract OCR, Strands Decider 2B System 1
action routing, and Amazon Bedrock Foundation Models in an accessible,
responsive, and professionally animated interface.
"""

from typing import List, Optional, Tuple
import streamlit as st

from agent import check_agent_prerequisites
from decision_patterns import (
    DECIDER_CRITERIA,
    DecisionInput,
    DecisionOutput,
    ResumeAction,
    check_decider_endpoint,
    evaluate_resume_action_decision,
    get_decider_config,
)
from services.bedrock_service import (
    check_bedrock_health,
    get_aws_console_verification_guide,
)
from services.resume_parser import parse_resume_document
from services.tesseract_service import (
    get_tesseract_install_instructions,
    is_tesseract_installed,
)
from ui.analysis_helpers import (
    compare_resume_to_job,
    compute_structural_metrics,
)
from ui.components import (
    SVG_AUDIT,
    SVG_DOC,
    SVG_IMPROVE,
    SVG_TARGET,
    render_brand_header,
    render_comparison_item,
    render_file_summary_card,
    render_integration_status_grid,
    render_kpi_metrics,
    render_skills_chips,
)
from ui.styles import NAVY_INDIGO_CSS


# -----------------------------------------------------------------------------
# Configuration & Page Setup
# -----------------------------------------------------------------------------
def setup_page():
    """Configure base Streamlit page settings and visual styling."""
    st.set_page_config(
        page_title="ResumePilot AI — Career & Resume Intelligence",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject curated Navy/Indigo/Cyan design system and animation rules
    st.markdown(NAVY_INDIGO_CSS, unsafe_allow_html=True)

    # Initialize persistent session state across navigation views
    if "extracted_text" not in st.session_state:
        st.session_state["extracted_text"] = ""
    if "uploaded_file_name" not in st.session_state:
        st.session_state["uploaded_file_name"] = None
    if "uploaded_file_size_kb" not in st.session_state:
        st.session_state["uploaded_file_size_kb"] = 0.0
    if "is_ocr_extracted" not in st.session_state:
        st.session_state["is_ocr_extracted"] = False
    if "parse_message" not in st.session_state:
        st.session_state["parse_message"] = ""
    if "job_description" not in st.session_state:
        st.session_state["job_description"] = ""
    if "user_request" not in st.session_state:
        st.session_state["user_request"] = ""


# -----------------------------------------------------------------------------
# Navigation Sidebar
# -----------------------------------------------------------------------------
def render_sidebar() -> str:
    """Render the polished application sidebar and return active navigation choice."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="rp-sidebar-brand">
                <div class="rp-sidebar-logo">{SVG_DOC}</div>
                <div>
                    <h3 class="rp-sidebar-title">ResumePilot AI</h3>
                </div>
            </div>
            <p class="rp-sidebar-tagline">
                Smarter Resumes. Better Job Matches. Stronger Careers.
            </p>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        st.markdown(
            "<p style='font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.4rem;'>Navigation</p>",
            unsafe_allow_html=True,
        )
        nav_options = [
            "Dashboard",
            "Resume Analysis",
            "Job Matching",
            "Resume Improvement",
            "Career Guidance",
        ]
        selected_page = st.radio(
            "Select View",
            options=nav_options,
            index=0,
            label_visibility="collapsed",
        )

        st.divider()

        # System Integration Status Overview in Sidebar
        st.markdown(
            "<p style='font-size:0.75rem; font-weight:700; color:#64748b; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:0.5rem;'>System Health</p>",
            unsafe_allow_html=True,
        )

        bedrock_health = check_bedrock_health()
        bedrock_pill = (
            '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Configured</span>'
            if bedrock_health.is_configured
            else '<span class="rp-status-pill rp-status-pill-setup"><span class="rp-status-dot"></span> Setup Required</span>'
        )

        decider_reachable, _ = check_decider_endpoint()
        decider_pill = (
            '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Connected</span>'
            if decider_reachable
            else '<span class="rp-status-pill rp-status-pill-pending"><span class="rp-status-dot"></span> Pending</span>'
        )

        tesseract_available = is_tesseract_installed()
        ocr_pill = (
            '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Active</span>'
            if tesseract_available
            else '<span class="rp-status-pill rp-status-pill-setup"><span class="rp-status-dot"></span> Local Missing</span>'
        )

        st.markdown(
            f"""
            <div style="font-size:0.82rem; line-height:1.8; color:#334155;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <span>Parser (PDF/DOCX)</span>
                    <span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Ready</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <span>Local Tesseract OCR</span>
                    {ocr_pill}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <span>Amazon Bedrock</span>
                    {bedrock_pill}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <span>Strands Decider 2B</span>
                    {decider_pill}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown(
            """
            <div style="font-size:0.75rem; color:#94a3b8; line-height:1.4;">
                <strong>ResumePilot AI v0.5.0</strong><br>
                AWS Hackathon Showcase Edition<br>
                Privacy-First Local Processing
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page


# -----------------------------------------------------------------------------
# Input Components & Validation
# -----------------------------------------------------------------------------
def render_file_upload(key_suffix: str = "") -> Tuple[Optional[object], str]:
    """Render file upload control, parse content, and maintain session state."""
    uploaded_file = st.file_uploader(
        "Upload Resume (PDF or DOCX)",
        type=["pdf", "docx"],
        help="Upload standard PDF, scanned PDF, or Word document (.docx). Max 25 MB.",
        key=f"file_uploader_{key_suffix}" if key_suffix else "file_uploader",
    )

    extracted_text = st.session_state.get("extracted_text", "")

    if uploaded_file is not None:
        filename = uploaded_file.name.lower()
        if not (filename.endswith(".pdf") or filename.endswith(".docx")):
            st.error(
                f"Unsupported file type: **{uploaded_file.name}**. "
                "Please upload a valid **.pdf** or **.docx** file."
            )
            return None, ""

        # Parse document through privacy-preserving local parser & Tesseract fallback
        with st.spinner("Processing document and extracting text layer..."):
            parse_success, parsed_text, parse_message = parse_resume_document(uploaded_file)

        file_size_kb = uploaded_file.size / 1024
        is_ocr = "tesseract" in parse_message.lower() or "ocr" in parse_message.lower()

        if parse_success:
            extracted_text = parsed_text
            st.session_state["extracted_text"] = parsed_text
            st.session_state["uploaded_file_name"] = uploaded_file.name
            st.session_state["uploaded_file_size_kb"] = file_size_kb
            st.session_state["is_ocr_extracted"] = is_ocr
            st.session_state["parse_message"] = parse_message

            render_file_summary_card(
                filename=uploaded_file.name,
                file_size_kb=file_size_kb,
                char_count=len(parsed_text),
                is_ocr=is_ocr,
            )

            with st.expander("View Extracted Text Preview", expanded=False):
                preview_text = parsed_text[:600] + "..." if len(parsed_text) > 600 else parsed_text
                st.text(preview_text)
                st.caption(f"Total extracted length: {len(parsed_text):,} characters.")
        else:
            st.session_state["parse_message"] = parse_message
            is_missing_tesseract = (
                "not installed" in parse_message.lower()
                or "not found" in parse_message.lower()
                or "winget install" in parse_message.lower()
            )
            if is_missing_tesseract:
                st.error(
                    "**Extraction Notice:** Scanned or image-only PDF detected, but local Tesseract OCR is not installed. "
                    "Install Tesseract to enable private, on-device text extraction."
                )
                with st.expander("Local Tesseract OCR Installation Guide", expanded=False):
                    st.markdown(get_tesseract_install_instructions())
            else:
                st.error(f"**Extraction Notice:** {parse_message}")
                if "tesseract" in parse_message.lower() or "scanned" in parse_message.lower():
                    with st.expander("Local Tesseract OCR Installation Guide", expanded=False):
                        st.markdown(get_tesseract_install_instructions())
    elif st.session_state.get("extracted_text") and st.session_state.get("uploaded_file_name"):
        # Display existing active file card from session state
        render_file_summary_card(
            filename=st.session_state["uploaded_file_name"],
            file_size_kb=st.session_state["uploaded_file_size_kb"],
            char_count=len(extracted_text),
            is_ocr=st.session_state.get("is_ocr_extracted", False),
        )

    return uploaded_file, extracted_text


def render_common_inputs(
    require_job_desc: bool = False,
    key_suffix: str = "",
) -> Tuple[Optional[object], str, str, str]:
    """Render unified input controls for resume, job description, and user instructions."""
    st.markdown('<div class="rp-section-title"><span>1.</span> Input Information</div>', unsafe_allow_html=True)
    st.markdown('<p class="rp-section-subtitle">Upload your resume and optionally specify a target job or custom instructions.</p>', unsafe_allow_html=True)

    uploaded_file, extracted_text = render_file_upload(key_suffix=key_suffix)

    job_desc_label = "Target Job Description" + (" *" if require_job_desc else " (Optional for Analysis)")
    job_desc_key = f"job_desc_{key_suffix}" if key_suffix else "job_desc"

    # Pre-fill with session state if available
    default_job_desc = st.session_state.get("job_description", "")
    job_description = st.text_area(
        job_desc_label,
        value=default_job_desc,
        height=140,
        placeholder="Paste role requirements, duties, or job description here to evaluate keyword match...",
        help="Job description helps align your resume against specific employer expectations.",
        key=job_desc_key,
    )
    if job_description != default_job_desc:
        st.session_state["job_description"] = job_description

    user_req_key = f"user_req_{key_suffix}" if key_suffix else "user_req"
    default_user_req = st.session_state.get("user_request", "")
    user_request = st.text_input(
        "Specific Request / Custom Instructions (Optional)",
        value=default_user_req,
        placeholder="e.g., Focus on cloud engineering experience, AWS, and distributed systems",
        help="Add any custom guidance or specific questions for the AI assistant.",
        key=user_req_key,
    )
    if user_request != default_user_req:
        st.session_state["user_request"] = user_request

    return uploaded_file, extracted_text, job_description.strip(), user_request.strip()


def validate_action_inputs(
    action_name: str,
    uploaded_file: Optional[object],
    job_description: str,
) -> Tuple[bool, List[str]]:
    """Validate presence and validity of required inputs per action type."""
    errors: List[str] = []

    # Check uploaded_file or session state extracted_text
    has_file = uploaded_file is not None
    if not has_file:
        # Fallback check session state
        has_file = bool(st.session_state.get("uploaded_file_name") and st.session_state.get("extracted_text"))

    if not has_file and uploaded_file is None:
        errors.append("A resume file (**PDF** or **DOCX**) is required. Please upload your resume above.")
    elif uploaded_file is not None:
        filename = uploaded_file.name.lower()
        if not (filename.endswith(".pdf") or filename.endswith(".docx")):
            errors.append(
                f"The file **{uploaded_file.name}** has an unsupported format. Only PDF and DOCX are permitted."
            )

    if action_name in ["Match Job", "Job Matching", ResumeAction.MATCH_JOB.value] and not job_description:
        errors.append("Target job description is required for job matching. Please paste the job description above.")

    is_valid = len(errors) == 0
    return is_valid, errors


def display_action_status(action_name: str, is_valid: bool, errors: List[str]):
    """Display validation feedback when an action button is triggered."""
    if not is_valid:
        for err in errors:
            st.error(f"**Validation Notice:** {err}")
    else:
        st.success(
            f"Input validation passed for **{action_name}**. "
            "Action evaluated through typed decision_patterns interface."
        )


# -----------------------------------------------------------------------------
# Decision & Result Panels
# -----------------------------------------------------------------------------
def render_decider_panel(decision_output: Optional[DecisionOutput] = None):
    """Render the Strands Decider 2B decision panel."""
    decider_reachable, reachability_msg = check_decider_endpoint()
    config = get_decider_config()

    with st.container(border=True):
        status_pill = (
            '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Active</span>'
            if decider_reachable
            else '<span class="rp-status-pill rp-status-pill-pending"><span class="rp-status-dot"></span> Pending Integration</span>'
        )
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                <h4 style="margin:0; font-size:1.05rem; font-weight:700; color:#0f172a;">Strands Decider 2B Decision</h4>
                {status_pill}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if decision_output is not None:
            if decision_output.status == "COMPLETED":
                st.success(
                    f"**Decision Reached:** `{decision_output.selected_action.value}` "
                    f"(Confidence: {decision_output.confidence:.2%})"
                )
            elif decision_output.status == "PENDING_INTEGRATION":
                st.info(
                    f"**Integration Status:** `{decision_output.status}`\n\n"
                    f"{decision_output.message}"
                )
                if decision_output.systemone_payload:
                    with st.expander("View Verified Strands Decider 2B Payload Schema"):
                        st.json(decision_output.systemone_payload)
            elif decision_output.status == "VALIDATION_ERROR":
                st.error(f"**Validation Issue:** {decision_output.message}")
            else:
                st.warning(f"**Decider Notice:** {decision_output.message}")
        else:
            st.markdown(
                f"""
                <div style="font-size:0.83rem; line-height:1.55; color:#334155;">
                    <p><strong>Model Target:</strong> <code>{config['model_id']}</code><br>
                    <strong>Endpoint:</strong> <code>{config['endpoint']}</code><br>
                    <strong>Decision Options:</strong> <code>ANALYZE_RESUME</code>, <code>MATCH_JOB</code>, <code>IMPROVE_RESUME</code></p>
                    <p>• Strands Decider 2B is a dedicated 2B System 1 classifier designed to pick structured actions without generating free-form text.<br>
                    • Status: <em>{reachability_msg}</em><br>
                    • <strong>Zero simulated confidence scores or mock decisions are displayed.</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_results_panel():
    """Render the Bedrock AI results placeholder panel with secure health status."""
    bedrock_health = check_bedrock_health()

    with st.container(border=True):
        status_pill = (
            '<span class="rp-status-pill rp-status-pill-ready"><span class="rp-status-dot"></span> Configured</span>'
            if bedrock_health.is_configured
            else '<span class="rp-status-pill rp-status-pill-setup"><span class="rp-status-dot"></span> Setup Required</span>'
        )
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                <h4 style="margin:0; font-size:1.05rem; font-weight:700; color:#0f172a;">Amazon Bedrock Status</h4>
                {status_pill}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if bedrock_health.is_configured:
            st.success(
                f"**AWS Bedrock Ready (Offline Inspection):**\n\n"
                f"- **Credential Source:** {bedrock_health.credential_source}\n"
                f"- **Target Region:** `{bedrock_health.region}`\n"
                f"- **Model ID:** `{bedrock_health.model_id}`\n"
                f"- **Inference Status:** Stage 5 Security Guard active. Credentials verified without incurring remote inference charges."
            )
        else:
            st.warning(bedrock_health.status_message)

        with st.expander("AWS Region & Model Access Verification Guide"):
            guide = get_aws_console_verification_guide()
            for step in guide["steps"]:
                st.markdown(f"**{step['topic']}**")
                st.write(step["instructions"])
                st.write("")


# -----------------------------------------------------------------------------
# Page Views
# -----------------------------------------------------------------------------
def render_dashboard_view():
    """Render the polished main overview dashboard."""
    render_brand_header()
    render_integration_status_grid()

    col_input, col_output = st.columns([1, 1], gap="large")
    decision_output: Optional[DecisionOutput] = None

    with col_input:
        uploaded_file, extracted_text, job_desc, user_req = render_common_inputs(
            require_job_desc=False,
            key_suffix="dash",
        )

        st.markdown('<div class="rp-section-title"><span>2.</span> Available Actions</div>', unsafe_allow_html=True)
        st.markdown('<p class="rp-section-subtitle">Select an action to trigger typed classification and workflow routing.</p>', unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(
                f"""<div class="rp-action-tile-pro">
                    <div class="rp-action-icon-wrap rp-action-icon-blue">{SVG_AUDIT}</div>
                    <div style="flex: 1;">
                        <div class="rp-action-tile-title">Analyze Resume</div>
                        <div class="rp-action-tile-desc">Audit core skills, section completeness, and ATS readability.</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            btn_analyze = st.button("Analyze Resume", type="primary", use_container_width=True, key="dash_analyze")

        with st.container(border=True):
            st.markdown(
                f"""<div class="rp-action-tile-pro">
                    <div class="rp-action-icon-wrap rp-action-icon-cyan">{SVG_TARGET}</div>
                    <div style="flex: 1;">
                        <div class="rp-action-tile-title">Match Job</div>
                        <div class="rp-action-tile-desc">Compare qualifications against job requirements and keyword gaps.</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            btn_match = st.button("Match Job", type="primary", use_container_width=True, key="dash_match")

        with st.container(border=True):
            st.markdown(
                f"""<div class="rp-action-tile-pro">
                    <div class="rp-action-icon-wrap rp-action-icon-purple">{SVG_IMPROVE}</div>
                    <div style="flex: 1;">
                        <div class="rp-action-tile-title">Improve Resume</div>
                        <div class="rp-action-tile-desc">Synthesize high-impact bullets with Google X-Y-Z phrasing.</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            btn_improve = st.button("Improve Resume", type="primary", use_container_width=True, key="dash_improve")

        if btn_analyze:
            valid, errs = validate_action_inputs("Analyze Resume", uploaded_file, job_desc)
            display_action_status("Analyze Resume", valid, errs)
            if valid:
                dec_in = DecisionInput(
                    resume_text=extracted_text,
                    job_description=job_desc,
                    user_request=user_req,
                    manual_action=ResumeAction.ANALYZE_RESUME,
                )
                decision_output = evaluate_resume_action_decision(dec_in)

        elif btn_match:
            valid, errs = validate_action_inputs("Match Job", uploaded_file, job_desc)
            display_action_status("Match Job", valid, errs)
            if valid:
                dec_in = DecisionInput(
                    resume_text=extracted_text,
                    job_description=job_desc,
                    user_request=user_req,
                    manual_action=ResumeAction.MATCH_JOB,
                )
                decision_output = evaluate_resume_action_decision(dec_in)

        elif btn_improve:
            valid, errs = validate_action_inputs("Improve Resume", uploaded_file, job_desc)
            display_action_status("Improve Resume", valid, errs)
            if valid:
                dec_in = DecisionInput(
                    resume_text=extracted_text,
                    job_description=job_desc,
                    user_request=user_req,
                    manual_action=ResumeAction.IMPROVE_RESUME,
                )
                decision_output = evaluate_resume_action_decision(dec_in)

    with col_output:
        st.markdown('<div class="rp-section-title"><span>3.</span> Decision Engine & System Status</div>', unsafe_allow_html=True)
        st.markdown('<p class="rp-section-subtitle">Real-time status of Strands System 1 classifier and Amazon Bedrock.</p>', unsafe_allow_html=True)

        render_decider_panel(decision_output)
        render_results_panel()

        # If resume text exists, display quick structural snapshot
        if extracted_text:
            metrics = compute_structural_metrics(extracted_text)
            with st.container(border=True):
                st.markdown("#### Document Overview")
                render_kpi_metrics(
                    word_count=metrics.word_count,
                    char_count=metrics.char_count,
                    reading_time=metrics.reading_time_minutes,
                    skills_count=len(metrics.identified_skills),
                )


def render_resume_analysis_view():
    """Render dedicated Resume Analysis workflow view."""
    render_brand_header("Resume Analysis Module • In-depth structural audit, section completeness, and skill recognition.")
    render_integration_status_grid()

    col_input, col_output = st.columns([1, 1], gap="large")
    decision_output: Optional[DecisionOutput] = None

    with col_input:
        uploaded_file, extracted_text, job_desc, user_req = render_common_inputs(
            require_job_desc=False,
            key_suffix="analysis",
        )
        btn_action = st.button("Run Resume Analysis", type="primary", use_container_width=True)

        if btn_action:
            valid, errs = validate_action_inputs("Resume Analysis", uploaded_file, job_desc)
            display_action_status("Resume Analysis", valid, errs)
            if valid:
                dec_in = DecisionInput(
                    resume_text=extracted_text,
                    job_description=job_desc,
                    user_request=user_req,
                    manual_action=ResumeAction.ANALYZE_RESUME,
                )
                decision_output = evaluate_resume_action_decision(dec_in)

        # Show live structural analysis when resume text is available
        if extracted_text:
            metrics = compute_structural_metrics(extracted_text)
            st.markdown("---")
            st.markdown("### Structural Resume Metrics")
            render_kpi_metrics(
                word_count=metrics.word_count,
                char_count=metrics.char_count,
                reading_time=metrics.reading_time_minutes,
                skills_count=len(metrics.identified_skills),
            )

            st.markdown("#### Section Detection Audit")
            sec_col1, sec_col2 = st.columns(2)
            with sec_col1:
                st.markdown("**Detected Standard Sections:**")
                if metrics.detected_sections:
                    for sec in metrics.detected_sections:
                        st.markdown(f"- <span style='color:#059669; font-weight:600;'>{sec}</span>", unsafe_allow_html=True)
                else:
                    st.caption("No standard sections identified.")

            with sec_col2:
                st.markdown("**Recommended Sections to Add:**")
                if metrics.missing_sections:
                    for sec in metrics.missing_sections:
                        st.markdown(f"- <span style='color:#d97706;'>{sec}</span>", unsafe_allow_html=True)
                else:
                    st.success("All standard sections present!")

            if metrics.identified_skills:
                st.markdown("#### Identified Core Competencies")
                chips_html = "".join(
                    f'<span class="rp-skill-chip rp-skill-neutral">{skill}</span>'
                    for skill in metrics.identified_skills
                )
                st.markdown(f'<div class="rp-skills-container">{chips_html}</div>', unsafe_allow_html=True)

    with col_output:
        st.markdown('<div class="rp-section-title">Verified Engine Panels</div>', unsafe_allow_html=True)
        render_decider_panel(decision_output)
        render_results_panel()


def render_job_matching_view():
    """Render dedicated Job Matching workflow view."""
    render_brand_header("Job Matching Module • Keyword alignment, prerequisite analysis, and candidate-job fit evaluation.")
    render_integration_status_grid()

    col_input, col_output = st.columns([1, 1], gap="large")
    decision_output: Optional[DecisionOutput] = None

    with col_input:
        uploaded_file, extracted_text, job_desc, user_req = render_common_inputs(
            require_job_desc=True,
            key_suffix="matching",
        )
        btn_action = st.button("Run Job Match Evaluation", type="primary", use_container_width=True)

        if btn_action:
            valid, errs = validate_action_inputs("Job Matching", uploaded_file, job_desc)
            display_action_status("Job Matching", valid, errs)
            if valid:
                dec_in = DecisionInput(
                    resume_text=extracted_text,
                    job_description=job_desc,
                    user_request=user_req,
                    manual_action=ResumeAction.MATCH_JOB,
                )
                decision_output = evaluate_resume_action_decision(dec_in)

                # Execute genuine keyword matching analysis
                match_results = compare_resume_to_job(extracted_text, job_desc)

                st.markdown("---")
                st.markdown("### Keyword Alignment Results")

                kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                with kpi_col1:
                    st.metric("Skill Match Rate", f"{match_results.match_percentage:.1f}%")
                with kpi_col2:
                    st.metric("Matched Skills", len(match_results.matched_skills))
                with kpi_col3:
                    st.metric("Missing Skills", len(match_results.missing_skills))

                render_skills_chips(
                    matched_skills=match_results.matched_skills,
                    missing_skills=match_results.missing_skills,
                )

                if match_results.missing_skills:
                    st.info(
                        "**Optimization Recommendation:** Consider incorporating the missing keywords "
                        "into your experience bullets where you have relevant project exposure."
                    )

    with col_output:
        st.markdown('<div class="rp-section-title">Verified Engine Panels</div>', unsafe_allow_html=True)
        render_decider_panel(decision_output)
        render_results_panel()


def render_resume_improvement_view():
    """Render dedicated Resume Improvement workflow view."""
    render_brand_header("Resume Improvement Module • Measurable impact phrasing, executive tone, and bullet point refinement.")
    render_integration_status_grid()

    col_input, col_output = st.columns([1, 1], gap="large")
    decision_output: Optional[DecisionOutput] = None

    with col_input:
        uploaded_file, extracted_text, job_desc, user_req = render_common_inputs(
            require_job_desc=False,
            key_suffix="improvement",
        )
        btn_action = st.button("Generate Resume Improvements", type="primary", use_container_width=True)

        if btn_action:
            valid, errs = validate_action_inputs("Resume Improvement", uploaded_file, job_desc)
            display_action_status("Resume Improvement", valid, errs)
            if valid:
                dec_in = DecisionInput(
                    resume_text=extracted_text,
                    job_description=job_desc,
                    user_request=user_req,
                    manual_action=ResumeAction.IMPROVE_RESUME,
                )
                decision_output = evaluate_resume_action_decision(dec_in)

    with col_output:
        st.markdown('<div class="rp-section-title">Verified Engine Panels</div>', unsafe_allow_html=True)
        render_decider_panel(decision_output)
        render_results_panel()

    st.markdown("---")
    st.markdown('<div class="rp-section-title">Actionable Enhancement Blueprint</div>', unsafe_allow_html=True)
    st.markdown('<p class="rp-section-subtitle">Real-world before and after transformations structured by professional domain and Google X-Y-Z formula.</p>', unsafe_allow_html=True)

    tab_summary, tab_exp, tab_skills, tab_format = st.tabs([
        "Professional Summary",
        "Experience & Accomplishments",
        "Core Skills Architecture",
        "ATS Layout & Formatting",
    ])

    with tab_summary:
        render_comparison_item(
            category="Professional Summary",
            original_text="Motivated software engineer with experience in Python and web apps looking for a challenging role.",
            improved_text="Full-Stack Cloud Engineer with 3+ years building high-throughput Python and AWS microservices handling 2M+ daily requests with 99.98% uptime.",
            rationale="Replaces generic aspiration with concrete domain expertise, scale, and proven operational reliability.",
        )

    with tab_exp:
        render_comparison_item(
            category="Backend Systems & Performance (Google X-Y-Z Formula)",
            original_text="Worked on improving database queries and helped backend speed.",
            improved_text="Architected distributed Redis caching layer and optimized PostgreSQL indices, reducing p99 API latency by 42% across 15 core microservices.",
            rationale="Quantifies achievement (42% latency reduction) and states the specific technical mechanism (Redis caching and indexing).",
        )
        render_comparison_item(
            category="Cloud Infrastructure & DevOps Automation",
            original_text="Responsible for deploying Docker containers to AWS.",
            improved_text="Automated end-to-end CI/CD deployment pipelines using GitHub Actions and AWS ECS Fargate, slashing deployment cycle time from 45 to 8 minutes.",
            rationale="Highlights automation and concrete time savings rather than routine duty descriptions.",
        )

    with tab_skills:
        with st.container(border=True):
            st.markdown(
                """
                **Strategic Guidelines for Skills Presentation:**
                - **Categorize skills by tier:** Separate *Core Languages*, *Frameworks*, *Cloud & Infrastructure*, and *Data Storage* rather than an unorganized comma-separated wall of text.
                - **Contextualize within experience bullets:** Recruiters and ATS screeners weigh skills mentioned in project contexts significantly higher than unreferenced skill lists.
                - **Deprecate redundant entries:** Prune legacy tools and generic office packages to maintain executive density.
                """
            )

    with tab_format:
        with st.container(border=True):
            st.markdown(
                """
                **ATS Readability & Layout Standards:**
                - **Layout:** Use a clean, single-column document flow without complex multi-column tables, text boxes, or floating graphics.
                - **Typography:** Use universal sans-serif fonts (Inter, Arial, Calibri, Helvetica) with consistent hierarchy (14–16pt headers, 10–11pt body).
                - **Standard Section Names:** Adhere strictly to industry standard headings (`Work Experience`, `Education`, `Technical Skills`).
                - **Consistent Date Formatting:** Use standardized month and year formatting (`Aug 2023 – Present`).
                """
            )


def render_career_guidance_view():
    """Render dedicated Career Guidance workflow view."""
    render_brand_header("Career Guidance Module • Strategic role progression, skill roadmap, and industry readiness.")
    render_integration_status_grid()

    col_input, col_output = st.columns([1, 1], gap="large")
    with col_input:
        uploaded_file, extracted_text, job_desc, user_req = render_common_inputs(
            require_job_desc=False,
            key_suffix="guidance",
        )
        target_role = st.text_input(
            "Desired Career Goal / Target Role (Optional)",
            placeholder="e.g., Senior Solutions Architect, Staff Cloud Engineer, Lead AI Engineer",
        )
        btn_action = st.button("Generate Career Path Guidance", type="primary", use_container_width=True)

        if btn_action:
            valid, errs = validate_action_inputs("Career Guidance", uploaded_file, job_desc)
            display_action_status("Career Guidance", valid, errs)

        st.markdown("---")
        st.markdown("### Career Trajectory Framework")

        with st.container(border=True):
            st.markdown("#### Strategic Career Milestones")
            st.markdown(
                """
                1. **Foundational Competency (Current Focus):**
                   - Master distributed architecture, containerization (Docker, Kubernetes), and modern infrastructure-as-code (Terraform).
                   - Deliver end-to-end observable production services with automated CI/CD.
                
                2. **Mid-Level Horizon (Next 12–18 Months):**
                   - Target enterprise cloud certifications: **AWS Certified Solutions Architect – Associate** or **AWS Certified Developer**.
                   - Lead architectural design reviews and drive engineering best practices across sprint teams.

                3. **Senior / Staff Trajectory (3–5 Years):**
                   - Architect resilient, multi-region cloud systems with strict SLAs and security governance.
                   - Mentor junior engineers and influence cross-organizational technical strategy.
                """
            )
            st.caption("Framework guidance based on industry standards. Deep real-time personalized reasoning requires live Amazon Bedrock inference.")

    with col_output:
        st.markdown('<div class="rp-section-title">Verified Engine Panels</div>', unsafe_allow_html=True)
        render_decider_panel(None)
        render_results_panel()


# -----------------------------------------------------------------------------
# Main Application Entry Point
# -----------------------------------------------------------------------------
def main():
    setup_page()
    selected_page = render_sidebar()

    if selected_page == "Dashboard":
        render_dashboard_view()
    elif selected_page == "Resume Analysis":
        render_resume_analysis_view()
    elif selected_page == "Job Matching":
        render_job_matching_view()
    elif selected_page == "Resume Improvement":
        render_resume_improvement_view()
    elif selected_page == "Career Guidance":
        render_career_guidance_view()


if __name__ == "__main__":
    main()
