"""ResumePilot AI - Visual Design System & CSS Styles.

Provides a professional Navy/Indigo, Slate, and Cyan design language
with responsive layouts, accessible contrast, smooth transitions,
vector iconography, and reduced-motion compliance.
"""

NAVY_INDIGO_CSS = """
<style>
/* -------------------------------------------------------------------------
   ResumePilot AI Design Tokens
   ------------------------------------------------------------------------- */
:root {
    --rp-navy-950: #0a0f1d;
    --rp-navy-900: #0f172a;
    --rp-navy-800: #1e293b;
    --rp-navy-700: #334155;
    --rp-slate-600: #475569;
    --rp-slate-500: #64748b;
    --rp-slate-400: #94a3b8;
    --rp-slate-300: #cbd5e1;
    --rp-slate-200: #e2e8f0;
    --rp-slate-100: #f1f5f9;
    --rp-slate-50:  #f8fafc;
    
    --rp-indigo-700: #4338ca;
    --rp-indigo-600: #4f46e5;
    --rp-indigo-500: #6366f1;
    --rp-indigo-100: #e0e7ff;
    --rp-indigo-50:  #eef2ff;
    
    --rp-cyan-700:   #0e7490;
    --rp-cyan-600:   #0891b2;
    --rp-cyan-500:   #06b6d4;
    --rp-cyan-50:    #ecfeff;
    
    --rp-emerald-700:#047857;
    --rp-emerald-600:#059669;
    --rp-emerald-50: #ecfdf5;
    
    --rp-amber-700:  #b45309;
    --rp-amber-600:  #d97706;
    --rp-amber-50:   #fffbeb;
    
    --rp-rose-700:   #be123c;
    --rp-rose-600:   #e11d48;
    --rp-rose-50:    #fff1f2;

    --rp-radius-sm:  6px;
    --rp-radius-md:  10px;
    --rp-radius-lg:  14px;
    --rp-radius-xl:  18px;
    
    --rp-shadow-sm:  0 1px 2px 0 rgba(15, 23, 42, 0.05);
    --rp-shadow-md:  0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05);
    --rp-shadow-lg:  0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04);
}

/* Global Font & Spacing Normalization */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: var(--rp-navy-900);
}

.main .block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1360px;
}

/* -------------------------------------------------------------------------
   Brand Header & Hero Section
   ------------------------------------------------------------------------- */
.rp-brand-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #1e293b 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: var(--rp-radius-lg);
    padding: 1.35rem 1.6rem;
    margin-bottom: 1.25rem;
    color: #ffffff;
    box-shadow: var(--rp-shadow-md);
    position: relative;
    overflow: hidden;
    animation: fadeIn 0.35s ease-out;
}

.rp-brand-header::after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 260px;
    height: 100%;
    background: radial-gradient(circle at 80% 20%, rgba(6, 182, 212, 0.18) 0%, transparent 70%);
    pointer-events: none;
}

.rp-header-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(165, 180, 252, 0.35);
    color: #c7d2fe;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.22rem 0.6rem;
    border-radius: 9999px;
    margin-bottom: 0.5rem;
}

.rp-header-title {
    font-size: 1.65rem;
    font-weight: 750;
    letter-spacing: -0.02em;
    margin: 0;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 0.65rem;
}

.rp-header-logo-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 8px;
    color: #ffffff;
}

.rp-header-subtitle {
    font-size: 0.9rem;
    color: #94a3b8;
    margin: 0.35rem 0 0 0;
    line-height: 1.45;
    max-width: 860px;
}

/* -------------------------------------------------------------------------
   Integration Status Grid Cards (4 Status Cards)
   ------------------------------------------------------------------------- */
.rp-status-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.35rem;
    animation: fadeInUp 0.4s ease-out;
}

@media (max-width: 992px) {
    .rp-status-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 576px) {
    .rp-status-grid {
        grid-template-columns: 1fr;
    }
}

.rp-status-card {
    background: #ffffff;
    border: 1px solid var(--rp-slate-200);
    border-radius: var(--rp-radius-md);
    padding: 0.85rem 0.95rem;
    box-shadow: var(--rp-shadow-sm);
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s ease, border-color 0.2s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.rp-status-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--rp-shadow-md);
    border-color: #cbd5e1;
}

.rp-status-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.35rem;
}

.rp-status-card-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--rp-navy-800);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    display: flex;
    align-items: center;
    gap: 0.45rem;
}

.rp-status-card-desc {
    font-size: 0.78rem;
    color: var(--rp-slate-500);
    line-height: 1.35;
}

.rp-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.18rem 0.5rem;
    border-radius: 9999px;
    width: fit-content;
}

.rp-status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}

.rp-status-pill-ready {
    background-color: var(--rp-emerald-50);
    color: var(--rp-emerald-700);
    border: 1px solid #bbf7d0;
}
.rp-status-pill-ready .rp-status-dot {
    background-color: var(--rp-emerald-600);
}

.rp-status-pill-pending {
    background-color: var(--rp-cyan-50);
    color: var(--rp-cyan-700);
    border: 1px solid #a5f3fc;
}
.rp-status-pill-pending .rp-status-dot {
    background-color: var(--rp-cyan-600);
}

.rp-status-pill-setup {
    background-color: var(--rp-amber-50);
    color: var(--rp-amber-700);
    border: 1px solid #fde68a;
}
.rp-status-pill-setup .rp-status-dot {
    background-color: var(--rp-amber-600);
}

.rp-status-pill-disabled {
    background-color: var(--rp-slate-100);
    color: var(--rp-slate-600);
    border: 1px solid #cbd5e1;
}
.rp-status-pill-disabled .rp-status-dot {
    background-color: var(--rp-slate-500);
}

.rp-status-pill-error {
    background-color: var(--rp-rose-50);
    color: var(--rp-rose-700);
    border: 1px solid #fecdd3;
}
.rp-status-pill-error .rp-status-dot {
    background-color: var(--rp-rose-600);
}

/* -------------------------------------------------------------------------
   SaaS Action Cards (Horizontal & Vertical Unified Layout)
   ------------------------------------------------------------------------- */
/* -------------------------------------------------------------------------
   SaaS Action Tiles (Horizontal Alignment Layout)
   ------------------------------------------------------------------------- */
.rp-action-tile-pro {
    display: flex !important;
    flex-direction: row !important;
    align-items: flex-start !important;
    gap: 0.85rem !important;
    padding: 0.15rem 0 0.4rem 0 !important;
}

.rp-action-tile-title {
    font-size: 0.98rem;
    font-weight: 700;
    color: var(--rp-navy-900);
    letter-spacing: -0.01em;
    line-height: 1.25;
}

.rp-action-tile-desc {
    font-size: 0.80rem;
    color: var(--rp-slate-500);
    margin-top: 0.25rem;
    line-height: 1.4;
}

.rp-action-icon-wrap {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    border-radius: var(--rp-radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0 !important;
}

.rp-action-icon-blue {
    background: var(--rp-indigo-50);
    color: var(--rp-indigo-600);
    border: 1px solid #c7d2fe;
}

.rp-action-icon-cyan {
    background: var(--rp-cyan-50);
    color: var(--rp-cyan-700);
    border: 1px solid #a5f3fc;
}

.rp-action-icon-purple {
    background: #faf5ff;
    color: #9333ea;
    border: 1px solid #e9d5ff;
}

/* -------------------------------------------------------------------------
   File Summary Card
   ------------------------------------------------------------------------- */
.rp-file-summary-card {
    background: #ffffff;
    border: 1px solid var(--rp-slate-200);
    border-left: 4px solid var(--rp-emerald-600);
    border-radius: var(--rp-radius-md);
    padding: 0.8rem 1rem;
    margin-top: 0.65rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--rp-shadow-sm);
    display: flex;
    justify-content: space-between;
    align-items: center;
    animation: fadeIn 0.3s ease-out;
}

.rp-file-summary-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.rp-file-icon {
    width: 34px;
    height: 34px;
    border-radius: var(--rp-radius-sm);
    background: var(--rp-indigo-50);
    color: var(--rp-indigo-600);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    border: 1px solid var(--rp-indigo-100);
}

.rp-file-title {
    font-size: 0.86rem;
    font-weight: 650;
    color: var(--rp-navy-900);
    margin: 0;
}

.rp-file-meta {
    font-size: 0.76rem;
    color: var(--rp-slate-500);
    margin: 0.15rem 0 0 0;
}

/* -------------------------------------------------------------------------
   Before/After Resume Improvement Diff Card (Elevated SaaS Styling)
   ------------------------------------------------------------------------- */
.rp-compare-card {
    background: #ffffff;
    border: 1px solid var(--rp-slate-200);
    border-radius: var(--rp-radius-lg);
    padding: 1.25rem 1.4rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--rp-shadow-sm);
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.rp-compare-card:hover {
    box-shadow: var(--rp-shadow-md);
    border-color: #cbd5e1;
}

.rp-compare-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.95rem;
    padding-bottom: 0.65rem;
    border-bottom: 1px solid var(--rp-slate-100);
}

.rp-compare-category {
    font-size: 0.84rem;
    font-weight: 750;
    color: var(--rp-indigo-600);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.rp-diff-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
    margin-bottom: 0.85rem;
}

@media (max-width: 768px) {
    .rp-diff-row {
        grid-template-columns: 1fr;
    }
}

.rp-diff-box {
    border-radius: var(--rp-radius-md);
    padding: 1rem 1.15rem;
    font-size: 0.88rem;
    line-height: 1.55;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.rp-diff-original {
    background: #fff8f8;
    border: 1px solid #fed7d7;
    border-left: 4px solid #ef4444;
}

.rp-diff-improved {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #10b981;
}

.rp-diff-label {
    font-size: 0.72rem;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.45rem;
}

.rp-diff-label-original {
    color: #b91c1c;
}

.rp-diff-label-improved {
    color: #047857;
}

.rp-diff-text {
    font-size: 0.88rem;
    color: #1e293b;
    line-height: 1.55;
}

.rp-diff-rationale {
    background: #f8fafc;
    border: 1px solid var(--rp-slate-200);
    border-left: 3px solid var(--rp-indigo-500);
    border-radius: var(--rp-radius-sm);
    padding: 0.65rem 0.95rem;
    font-size: 0.82rem;
    color: #334155;
    line-height: 1.45;
}

/* -------------------------------------------------------------------------
   Section Titles & Headers
   ------------------------------------------------------------------------- */
.rp-section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--rp-navy-900);
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 0.45rem;
    margin-bottom: 0.25rem;
}

.rp-section-subtitle {
    font-size: 0.82rem;
    color: var(--rp-slate-500);
    margin-bottom: 0.85rem;
}

/* -------------------------------------------------------------------------
   Metric Badges & KPI Cards
   ------------------------------------------------------------------------- */
.rp-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}

@media (max-width: 768px) {
    .rp-kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.rp-kpi-card {
    background: #ffffff;
    border: 1px solid var(--rp-slate-200);
    border-radius: var(--rp-radius-md);
    padding: 0.8rem 0.95rem;
    box-shadow: var(--rp-shadow-sm);
    transition: transform 0.15s ease;
}

.rp-kpi-card:hover {
    transform: translateY(-1px);
    box-shadow: var(--rp-shadow-md);
}

.rp-kpi-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--rp-slate-500);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.2rem;
}

.rp-kpi-val {
    font-size: 1.35rem;
    font-weight: 750;
    color: var(--rp-navy-950);
    letter-spacing: -0.02em;
    line-height: 1.2;
}

.rp-kpi-sub {
    font-size: 0.72rem;
    color: var(--rp-slate-400);
    margin-top: 0.18rem;
}

/* -------------------------------------------------------------------------
   Skill Chips (Matched vs Missing)
   ------------------------------------------------------------------------- */
.rp-skills-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.4rem;
    margin-bottom: 0.85rem;
}

.rp-skill-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    line-height: 1.2;
}

.rp-skill-matched {
    background-color: var(--rp-emerald-50);
    color: var(--rp-emerald-700);
    border: 1px solid #a7f3d0;
}

.rp-skill-missing {
    background-color: var(--rp-rose-50);
    color: var(--rp-rose-700);
    border: 1px solid #fecdd3;
}

.rp-skill-neutral {
    background-color: var(--rp-slate-100);
    color: var(--rp-slate-700);
    border: 1px solid var(--rp-slate-200);
}

/* -------------------------------------------------------------------------
   Before/After Resume Improvement Card
   ------------------------------------------------------------------------- */
.rp-compare-card {
    background: #ffffff;
    border: 1px solid var(--rp-slate-200);
    border-radius: var(--rp-radius-md);
    padding: 1rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--rp-shadow-sm);
}

.rp-compare-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.65rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid var(--rp-slate-100);
}

.rp-compare-category {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--rp-indigo-600);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.rp-diff-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.85rem;
}

@media (max-width: 768px) {
    .rp-diff-row {
        grid-template-columns: 1fr;
    }
}

.rp-diff-box {
    border-radius: var(--rp-radius-sm);
    padding: 0.8rem;
    font-size: 0.83rem;
    line-height: 1.45;
}

.rp-diff-original {
    background: #fff8f8;
    border: 1px solid #fed7d7;
    color: #991b1b;
}

.rp-diff-improved {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #14532d;
}

/* -------------------------------------------------------------------------
   Sidebar Customization
   ------------------------------------------------------------------------- */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--rp-slate-200) !important;
}

.rp-sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.2rem 0 0.4rem 0;
}

.rp-sidebar-logo {
    width: 32px;
    height: 32px;
    border-radius: var(--rp-radius-sm);
    background: linear-gradient(135deg, #0f172a, #4f46e5);
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--rp-shadow-sm);
}

.rp-sidebar-title {
    font-size: 1.15rem;
    font-weight: 750;
    color: var(--rp-navy-950);
    letter-spacing: -0.01em;
    margin: 0;
}

.rp-sidebar-tagline {
    font-size: 0.78rem;
    color: var(--rp-slate-500);
    margin: 0.2rem 0 1rem 0;
    line-height: 1.35;
}

/* -------------------------------------------------------------------------
   CSS Animations & Micro-Interactions
   ------------------------------------------------------------------------- */
@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Smooth Streamlit Buttons - Full Letters, No Ellipsis */
button[kind="primary"],
button[kind="secondary"],
.stButton > button,
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"] {
    border-radius: var(--rp-radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.01em !important;
    padding: 0.48rem 1rem !important;
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    text-overflow: unset !important;
    min-height: 2.35rem !important;
    transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button[kind="primary"] *,
button[kind="secondary"] *,
.stButton > button *,
[data-testid="stBaseButton-primary"] *,
[data-testid="stBaseButton-secondary"] * {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    text-overflow: unset !important;
    margin: 0 !important;
}

button[kind="primary"]:hover,
.stButton > button:hover,
[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px);
    box-shadow: var(--rp-shadow-md);
}

/* Accessibility: Respect Reduced-Motion */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
    .rp-action-card:hover,
    .rp-action-tile:hover,
    .rp-status-card:hover,
    .rp-kpi-card:hover,
    button:hover {
        transform: none !important;
    }
}
</style>
"""
