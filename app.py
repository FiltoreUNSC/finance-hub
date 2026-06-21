"""Finance Hub — research, technicals, options, macro, portfolio."""

__version__ = "1.3.0"

import streamlit as st

from lib.alerts import render_alerts_sidebar
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
from lib.ui import (
    WATCHLIST_PRESETS,
    inject_styles,
    render_footer,
    render_hero,
    render_module_guide,
    render_sidebar_brand,
    section_label,
)

st.set_page_config(
    page_title="Finance Hub",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()

with st.sidebar:
    render_sidebar_brand(__version__)

    section_label("Watchlist")
    if "watchlist_text" not in st.session_state:
        st.session_state.watchlist_text = ", ".join(DEFAULT_WATCHLIST)

    preset = st.selectbox(
        "Quick load",
        ["Custom"] + list(WATCHLIST_PRESETS.keys()),
        key="wl_preset",
        label_visibility="collapsed",
    )
    last_preset = st.session_state.get("wl_preset_last", "Custom")
    if preset != "Custom" and preset != last_preset:
        st.session_state.watchlist_text = ", ".join(WATCHLIST_PRESETS[preset])
    st.session_state.wl_preset_last = preset

    watchlist_text = st.text_area(
        "Tickers (comma-separated)",
        height=72,
        key="watchlist_text",
        placeholder="SPY, AAPL, NVDA…",
    )
    watchlist = [t.strip().upper() for t in watchlist_text.split(",") if t.strip()]

    st.caption(f"{len(watchlist)} ticker{'s' if len(watchlist) != 1 else ''} · any symbol Yahoo supports")

    section_label("Live quotes")
    for sym in watchlist[:10]:
        try:
            q = fetch_quote(sym)
            price = q["price"]
            ch = q["change_pct"] or 0
            color = "green" if ch >= 0 else "red"
            sign = "+" if ch >= 0 else ""
            price_str = f"${price:.2f}" if price else "—"
            ch_html = f'<span class="{color}">{sign}{ch:.2f}%</span>' if price else ""
            st.markdown(
                f'<div class="watch-ticker">'
                f'<a href="{yahoo_url(sym)}" target="_blank" rel="noopener" '
                f'style="color:#7dd3a0;text-decoration:none;"><b>{sym}</b></a> '
                f'{price_str} {ch_html}</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown(f'<div class="watch-ticker"><b>{sym}</b> —</div>', unsafe_allow_html=True)

    if len(watchlist) > 10:
        st.caption(f"+ {len(watchlist) - 10} more (showing first 10)")

    st.divider()
    render_alerts_sidebar()

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button("GitHub", GITHUB_REPO, use_container_width=True)
    with col_b:
        st.link_button("Support", SUPPORT_EMAIL, use_container_width=True)

render_hero(__version__)
render_market_overview()
st.divider()
render_module_guide()

default = watchlist[0] if watchlist else "SPY"

tabs = st.tabs([
    "📊 Research",
    "🔍 Deep Dive",
    "📈 Technicals",
    "⚖️ Compare",
    "🎯 Options",
    "₿ Crypto",
    "📝 Paper Trade",
    "💰 Dividends",
    "⏪ Backtest",
    "🗺️ Sectors",
    "🌐 Macro",
    "💼 Portfolio",
    "📄 Reports",
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
    render_paper_trading()
with tabs[7]:
    render_dividends(watchlist)
with tabs[8]:
    render_backtest(default)
with tabs[9]:
    render_sector_heatmap()
with tabs[10]:
    render_macro(watchlist)
with tabs[11]:
    render_portfolio()
with tabs[12]:
    render_reports(watchlist)

render_footer(__version__, GITHUB_REPO)