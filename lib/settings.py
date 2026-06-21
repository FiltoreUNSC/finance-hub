"""User preferences — session defaults."""

from __future__ import annotations

import streamlit as st

DEFAULTS = {
    "risk_free_rate_pct": 4.5,
    "chart_period": "6mo",
    "show_module_guide": False,
}


def init_settings() -> None:
    if "fh_settings" not in st.session_state:
        st.session_state.fh_settings = DEFAULTS.copy()


def risk_free_rate() -> float:
    init_settings()
    return st.session_state.fh_settings["risk_free_rate_pct"] / 100.0


def chart_period() -> str:
    init_settings()
    return st.session_state.fh_settings["chart_period"]


def render_settings_sidebar() -> None:
    init_settings()
    s = st.session_state.fh_settings

    with st.expander("Settings", expanded=False):
        s["risk_free_rate_pct"] = st.number_input(
            "Risk-free rate (%)",
            min_value=0.0,
            max_value=15.0,
            value=float(s["risk_free_rate_pct"]),
            step=0.1,
            help="Used for Options Greeks and IV chain",
            key="set_rf",
        )
        s["chart_period"] = st.selectbox(
            "Default chart period",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=["1mo", "3mo", "6mo", "1y", "2y", "5y"].index(s["chart_period"]),
            key="set_period",
        )
        st.caption("Settings apply this session only.")

    with st.expander("Help & FAQ", expanded=False):
        st.markdown(
            """
**Is this free?**  
Yes — 100% free, open source. No subscription, no paywall.

**What stocks can I use?**  
Any ticker Yahoo Finance supports. Type symbols in the watchlist or tab inputs.

**Screener universe?**  
~80 built-in large caps + ETFs. Add your own tickers in Research → Custom Universe.

**Is data real-time?**  
Near real-time via Yahoo (some quotes delayed ~15 min).

**Where is my data stored?**  
Portfolio, paper trades, and alerts save locally as JSON files.

**Financial advice?**  
No — educational/research tool only.
            """
        )