"""Finance Hub — research, technicals, options, macro, portfolio."""

__version__ = "1.1.0"

import streamlit as st

from lib.alerts import render_alerts_sidebar
from lib.banking import render_banking
from lib.backtest import render_backtest
from lib.compare import render_compare
from lib.crypto import render_crypto
from lib.data import DEFAULT_WATCHLIST, fetch_quote
from lib.links import GITHUB_REPO, SUPPORT_EMAIL, yahoo_url
from lib.deep_dive import render_deep_dive
from lib.dividends import render_dividends
from lib.heatmap import render_sector_heatmap
from lib.macro import render_macro
from lib.market_overview import render_market_overview
from lib.options_calc import render_options
from lib.paper_trading import render_paper_trading
from lib.portfolio import render_portfolio
from lib.reports import render_reports
from lib.screener import render_research
from lib.technicals import render_technicals

st.set_page_config(
    page_title="Finance Hub",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .watch-ticker { font-size: 0.85rem; padding: 0.35rem 0; border-bottom: 1px solid #222; }
    .green { color: #7dd3a0; }
    .red { color: #ff6b6b; }
    h1 { letter-spacing: -0.03em; }
    div[data-testid="stMetric"] { background: #141414; padding: 0.65rem; border-radius: 8px; border: 1px solid #222; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Finance Hub")
    st.caption(f"v{__version__} · Your personal Bloomberg")

    watchlist_text = st.text_area(
        "Watchlist (comma-separated)",
        value=", ".join(DEFAULT_WATCHLIST),
        height=80,
    )
    watchlist = [t.strip().upper() for t in watchlist_text.split(",") if t.strip()]

    st.divider()
    st.subheader("Live quotes")
    for sym in watchlist[:10]:
        try:
            q = fetch_quote(sym)
            ch = q["change_pct"] or 0
            color = "green" if ch >= 0 else "red"
            sign = "+" if ch >= 0 else ""
            ch_html = f'<span class="{color}">{sign}{ch:.2f}%</span>'
            st.markdown(
                f'<div class="watch-ticker">'
                f'<a href="{yahoo_url(sym)}" target="_blank" rel="noopener" '
                f'style="color:#7dd3a0;text-decoration:none;"><b>{sym}</b></a> '
                f'${q["price"]:.2f} {ch_html}</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown(f'<div class="watch-ticker"><b>{sym}</b> —</div>', unsafe_allow_html=True)

    st.divider()
    render_alerts_sidebar()

    st.divider()
    st.link_button("GitHub", GITHUB_REPO, use_container_width=True)
    st.link_button("Support", SUPPORT_EMAIL, use_container_width=True)

    st.markdown(
        f'<p style="font-size:0.75rem;color:#555;margin-top:0.5rem">'
        f'v{__version__} · Yahoo Finance · Not financial advice</p>',
        unsafe_allow_html=True,
    )

st.title("Finance Hub")
st.caption("Research · Trade · Analyze · Report — all in one dashboard")

render_market_overview()
st.divider()

default = watchlist[0] if watchlist else "SPY"

tabs = st.tabs([
    "Research",
    "Deep Dive",
    "Technicals",
    "Compare",
    "Options",
    "Crypto",
    "Banking",
    "Paper Trade",
    "Dividends",
    "Backtest",
    "Sectors",
    "Macro & News",
    "Portfolio",
    "Reports",
])

with tabs[0]:
    render_research(watchlist)
with tabs[1]:
    render_deep_dive(default)
with tabs[2]:
    render_technicals(default)
with tabs[3]:
    render_compare(watchlist)
with tabs[4]:
    render_options(default)
with tabs[5]:
    render_crypto()
with tabs[6]:
    render_banking()
with tabs[7]:
    render_paper_trading()
with tabs[8]:
    render_dividends(watchlist)
with tabs[9]:
    render_backtest(default)
with tabs[10]:
    render_sector_heatmap()
with tabs[11]:
    render_macro(watchlist)
with tabs[12]:
    render_portfolio()
with tabs[13]:
    render_reports(watchlist)