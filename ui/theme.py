"""Centralized visual configuration for the NHL Prediction App."""

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------

BG_DARK = "#0d1117"
BG_CARD = "#161b22"
BG_CARD_GRADIENT = "#1c2333"
BORDER = "#21262d"
TEXT = "#c9d1d9"
TEXT_BRIGHT = "#f0f6fc"
TEXT_MUTED = "#8b949e"
TEXT_FOOTER = "#484f58"
PRIMARY = "#1f6feb"
PRIMARY_HOVER = "#388bfd"
PRIMARY_LIGHT = "#58a6ff"

# ---------------------------------------------------------------------------
# Full CSS stylesheet
# ---------------------------------------------------------------------------

CSS = f"""
<style>
/* --- Global --- */
[data-testid="stAppViewContainer"] {{
    background: linear-gradient(180deg, {BG_DARK} 0%, {BG_CARD} 100%);
}}
section[data-testid="stSidebar"] {{
    background: {BG_DARK};
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] .stRadio label {{
    color: {TEXT} !important;
}}

/* --- Typography --- */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
    color: {TEXT_BRIGHT} !important;
    font-weight: 700 !important;
}}

/* --- Metric cards --- */
[data-testid="stMetric"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 16px 20px;
}}
[data-testid="stMetric"] label {{
    color: {TEXT_MUTED} !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {TEXT_BRIGHT} !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}}

/* --- Dataframes --- */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    overflow: hidden;
}}

/* --- Tabs --- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    border-bottom: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 6px 6px 0 0;
    padding: 8px 20px;
    color: {TEXT_MUTED};
    font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    background: {BG_CARD};
    color: {TEXT_BRIGHT} !important;
    border-bottom: 2px solid {PRIMARY};
}}

/* --- Buttons --- */
.stButton > button {{
    background: {PRIMARY};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-weight: 600;
    transition: background 0.2s;
}}
.stButton > button:hover {{
    background: {PRIMARY_HOVER};
    color: #ffffff;
    border: none;
}}

/* --- Sidebar brand --- */
.sidebar-brand {{
    text-align: center;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1rem;
}}
.sidebar-brand h2 {{
    font-size: 1.3rem !important;
    margin: 0 !important;
    letter-spacing: 0.04em;
}}
.sidebar-brand p {{
    color: {TEXT_MUTED};
    font-size: 0.8rem;
    margin: 4px 0 0;
}}

/* --- Page header --- */
.page-header {{
    padding: 0.5rem 0 1.5rem;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1.5rem;
}}
.page-header h1 {{
    margin: 0 !important;
    font-size: 1.8rem !important;
}}
.page-header p {{
    color: {TEXT_MUTED};
    margin: 4px 0 0;
    font-size: 0.95rem;
}}

/* --- Stat card --- */
.stat-card {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 1rem;
}}
.stat-card h4 {{
    color: {TEXT_MUTED} !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 6px !important;
    font-weight: 600 !important;
}}
.stat-card .value {{
    color: {TEXT_BRIGHT};
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.2;
}}
.stat-card .sub {{
    color: {TEXT_MUTED};
    font-size: 0.8rem;
    margin-top: 4px;
}}

/* --- Divider --- */
.section-divider {{
    border: none;
    border-top: 1px solid {BORDER};
    margin: 2rem 0;
}}

/* --- Footer --- */
.sidebar-footer {{
    position: fixed;
    bottom: 0;
    padding: 12px 16px;
    font-size: 0.75rem;
    color: {TEXT_FOOTER};
    border-top: 1px solid {BORDER};
}}
</style>
"""

# ---------------------------------------------------------------------------
# Plotly theme
# ---------------------------------------------------------------------------

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT, family="Inter, system-ui, sans-serif"),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
)

NHL_COLORS = [
    PRIMARY, PRIMARY_HOVER, PRIMARY_LIGHT, "#79c0ff",
    "#3fb950", "#56d364", "#f0883e", "#d29922",
    "#f85149", "#da3633", "#bc8cff", TEXT_MUTED,
]
