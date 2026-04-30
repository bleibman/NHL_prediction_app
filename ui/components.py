"""Reusable Streamlit UI helpers for the NHL Prediction App."""

import streamlit as st

from ui.theme import (
    BG_CARD,
    BG_CARD_GRADIENT,
    BORDER,
    CSS,
    PRIMARY,
    TEXT,
    TEXT_BRIGHT,
    TEXT_MUTED,
)


def inject_css():
    """Inject the global CSS stylesheet."""
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str):
    """Render the standard page header."""
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def stat_card(label: str, value, sub: str = ""):
    """Render a styled metric card."""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="stat-card">'
        f"<h4>{label}</h4>"
        f'<div class="value">{value}</div>'
        f"{sub_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def section_divider():
    """Render a horizontal section divider."""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


def highlight_card(label: str, icon: str, title: str, subtitle: str = ""):
    """Render a centered highlight card (champion, predicted favorite, etc.)."""
    subtitle_html = (
        f'<div style="font-size:1rem; color:{PRIMARY}; margin-top:0.3rem;">'
        f"{subtitle}</div>"
        if subtitle
        else ""
    )
    st.markdown(
        f'<div style="text-align:center; padding:1.5rem; margin-top:1rem; '
        f"background:linear-gradient(135deg, {BG_CARD} 0%, {BG_CARD_GRADIENT} 100%); "
        f'border:1px solid {BORDER}; border-radius:12px;">'
        f'<div style="font-size:0.85rem; color:{TEXT_MUTED}; text-transform:uppercase; '
        f'letter-spacing:0.05em;">{label}</div>'
        f'<div style="font-size:2.5rem; margin-top:0.3rem;">{icon}</div>'
        f'<div style="font-size:1.5rem; font-weight:700; color:{TEXT_BRIGHT}; '
        f'margin-top:0.3rem;">{title}</div>'
        f"{subtitle_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def info_box(text: str):
    """Render a styled info panel."""
    st.markdown(
        f'<div style="background:{BG_CARD}; border:1px solid {BORDER}; '
        f'border-radius:10px; padding:1.2rem; margin-bottom:1.5rem;">'
        f'<p style="color:{TEXT}; margin:0;">{text}</p></div>',
        unsafe_allow_html=True,
    )


def format_season(s: int) -> str:
    """Convert a season ID like 20242025 to '2024\u201325'."""
    return f"{s // 10000}\u2013{str(s // 10000 + 1)[-2:]}"
