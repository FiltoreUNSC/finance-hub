"""Shared UI styles and layout helpers."""

from __future__ import annotations

import streamlit as st

WATCHLIST_PRESETS: dict[str, list[str]] = {
    "Mag 7": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"],
    "Index ETFs": ["SPY", "QQQ", "IWM", "DIA", "VTI", "VOO"],
    "Growth / Tech": ["NVDA", "AMD", "PLTR", "COIN", "SOFI", "META", "NFLX"],
    "Dividend": ["JNJ", "KO", "PEP", "PG", "VZ", "T", "XOM"],
}

TAB_GUIDE: list[tuple[str, str]] = [
    ("Research", "Screen ~80 large caps or filter your watchlist"),
    ("Deep Dive", "Fundamentals, ratings, holders"),
    ("Technicals", "Charts, RSI, MACD, Bollinger"),
    ("Compare", "Overlay up to 6 tickers"),
    ("Options", "P/L, Black-Scholes Greeks, IV chain"),
    ("Crypto", "BTC, ETH, SOL and more"),
    ("Paper Trade", "$100k virtual portfolio"),
    ("Dividends", "Yield screener + history"),
    ("Backtest", "SMA & RSI vs buy-and-hold"),
    ("Sectors", "Sector ETF heatmap"),
    ("Macro & News", "Fed calendar, RSS, sentiment"),
    ("Portfolio", "Track holdings locally"),
    ("Reports", "Export PDF summaries"),
]


def inject_styles() -> None:
    st.markdown(
        """
<style>
    .block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1400px; }
    h1, h2, h3 { letter-spacing: -0.02em; }
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #161616 0%, #121212 100%);
        padding: 0.7rem 0.85rem;
        border-radius: 10px;
        border: 1px solid #2a2a2a;
        box-shadow: 0 1px 0 rgba(125, 211, 160, 0.04);
    }
    div[data-testid="stMetric"]:hover { border-color: #3a4a3a; }
    div[data-testid="stMetricLabel"] { font-size: 0.72rem !important; color: #888 !important; }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0c0c 0%, #0a0a0a 100%);
        border-right: 1px solid #1e1e1e;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background: #141414;
        border-radius: 8px 8px 0 0;
        border: 1px solid #222;
        border-bottom: none;
        padding: 0.45rem 0.85rem;
        font-size: 0.88rem;
    }
    .stTabs [aria-selected="true"] {
        background: #1a2420 !important;
        border-color: #2a4a35 !important;
        color: #7dd3a0 !important;
    }
    .fh-hero {
        background: linear-gradient(135deg, #0f1a14 0%, #0a0a0a 55%, #101820 100%);
        border: 1px solid #2a4a35;
        border-radius: 14px;
        padding: 1.35rem 1.5rem 1.1rem;
        margin-bottom: 1rem;
    }
    .fh-hero h1 {
        margin: 0 0 0.35rem 0;
        font-size: 1.85rem;
        font-weight: 800;
        color: #f0f0f0;
        letter-spacing: -0.04em;
    }
    .fh-hero .tagline { color: #8a8a8a; font-size: 0.95rem; margin: 0 0 0.75rem 0; }
    .fh-hero .chips { display: flex; flex-wrap: wrap; gap: 0.45rem; }
    .fh-chip {
        font-size: 0.72rem;
        font-weight: 600;
        color: #7dd3a0;
        background: #0f1f14;
        border: 1px solid #2a4a35;
        border-radius: 999px;
        padding: 0.28rem 0.65rem;
    }
    .fh-sidebar-brand {
        background: linear-gradient(135deg, #0f1a14, #121212);
        border: 1px solid #2a4a35;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.75rem;
    }
    .fh-sidebar-brand .title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #7dd3a0;
        margin: 0;
        letter-spacing: -0.03em;
    }
    .fh-sidebar-brand .sub { font-size: 0.75rem; color: #666; margin: 0.2rem 0 0 0; }
    .fh-section-label {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #555;
        margin: 0.5rem 0 0.35rem 0;
    }
    .fh-tape-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.55rem;
        margin-bottom: 0.55rem;
    }
    .fh-tape-card {
        background: #141414;
        border: 1px solid #222;
        border-radius: 10px;
        padding: 0.65rem 0.75rem;
        min-width: 0;
    }
    .fh-tape-card:hover { border-color: #333; }
    .fh-tape-card .label { font-size: 0.68rem; color: #777; margin-bottom: 0.15rem; }
    .fh-tape-card .price { font-size: 1rem; font-weight: 700; color: #eee; }
    .fh-tape-card .chg-up { font-size: 0.75rem; color: #7dd3a0; font-weight: 600; }
    .fh-tape-card .chg-dn { font-size: 0.75rem; color: #ff6b6b; font-weight: 600; }
    .watch-ticker {
        font-size: 0.84rem;
        padding: 0.4rem 0.5rem;
        margin: 0.15rem 0;
        border-radius: 6px;
        border: 1px solid transparent;
    }
    .watch-ticker:hover { background: #141414; border-color: #222; }
    .green { color: #7dd3a0; }
    .red { color: #ff6b6b; }
    .fh-footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #1e1e1e;
        font-size: 0.78rem;
        color: #555;
        text-align: center;
    }
    .fh-module-guide {
        background: #101010;
        border: 1px solid #1e1e1e;
        border-radius: 10px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.75rem;
    }
    .fh-guide-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 0.35rem 1rem;
        font-size: 0.82rem;
        color: #aaa;
    }
    .fh-guide-grid b { color: #7dd3a0; font-size: 0.78rem; }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(version: str) -> None:
    st.markdown(
        f"""
<div class="fh-hero">
  <h1>Finance Hub</h1>
  <p class="tagline">Personal finance dashboard — screener, charts, paper trading, backtests</p>
  <div class="chips">
    <span class="fh-chip">v{version}</span>
    <span class="fh-chip">Yahoo Finance</span>
    <span class="fh-chip">Runs locally</span>
    <span class="fh-chip">Not financial advice</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand(version: str) -> None:
    st.markdown(
        f"""
<div class="fh-sidebar-brand">
  <p class="title">Finance Hub</p>
  <p class="sub">v{version} · Personal finance dashboard</p>
</div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f'<p class="fh-section-label">{text}</p>', unsafe_allow_html=True)


def section_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"#### {title}")
    if subtitle:
        st.caption(subtitle)


def render_module_guide() -> None:
    with st.expander("Module guide — what each tab does", expanded=False):
        rows = "".join(
            f'<div><b>{name}</b> — {desc}</div>'
            for name, desc in TAB_GUIDE
        )
        st.markdown(f'<div class="fh-module-guide"><div class="fh-guide-grid">{rows}</div></div>', unsafe_allow_html=True)


def render_footer(version: str, github_url: str) -> None:
    st.markdown(
        f"""
<div class="fh-footer">
  Finance Hub v{version} · Data from Yahoo Finance ·
  <a href="{github_url}" target="_blank" rel="noopener" style="color:#7dd3a0">GitHub</a>
  · Not financial advice
</div>
        """,
        unsafe_allow_html=True,
    )


def format_change_html(change_pct: float) -> str:
    color = "chg-up" if change_pct >= 0 else "chg-dn"
    sign = "+" if change_pct >= 0 else ""
    return f'<span class="{color}">{sign}{change_pct:.2f}%</span>'