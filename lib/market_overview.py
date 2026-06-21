"""Market tape — indices, VIX, yields, crypto."""

from __future__ import annotations

import streamlit as st

from lib.data import fetch_quote

MARKET_TICKERS = {
    "S&P 500": "SPY",
    "Nasdaq": "QQQ",
    "Dow": "DIA",
    "Russell": "IWM",
    "VIX": "^VIX",
    "10Y Yield": "^TNX",
    "Gold": "GLD",
    "Oil": "USO",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
}


def render_market_overview() -> None:
    cols = st.columns(len(MARKET_TICKERS))
    for col, (label, sym) in zip(cols, MARKET_TICKERS.items()):
        with col:
            try:
                q = fetch_quote(sym)
                ch = q["change_pct"] or 0
                price = q["price"]
                if sym in ("^VIX", "^TNX"):
                    disp = f"{price:.2f}"
                elif sym.endswith("-USD"):
                    disp = f"${price:,.0f}"
                else:
                    disp = f"${price:.2f}"
                col.metric(label, disp, delta=f"{ch:+.2f}%")
            except Exception:
                col.metric(label, "—")