"""Market tape — indices, VIX, yields, crypto."""

from __future__ import annotations

import streamlit as st

from lib.data import fetch_quote
from lib.ui import format_change_html, section_label

TAPE_GROUPS: list[tuple[str, dict[str, str]]] = [
    (
        "Indices",
        {
            "S&P 500": "SPY",
            "Nasdaq": "QQQ",
            "Dow": "DIA",
            "Russell": "IWM",
            "VIX": "^VIX",
        },
    ),
    (
        "Macro & commodities",
        {
            "10Y Yield": "^TNX",
            "Gold": "GLD",
            "Oil": "USO",
        },
    ),
    (
        "Crypto",
        {
            "Bitcoin": "BTC-USD",
            "Ethereum": "ETH-USD",
        },
    ),
]


def _format_price(sym: str, price: float | None) -> str:
    if price is None:
        return "—"
    if sym in ("^VIX", "^TNX"):
        return f"{price:.2f}"
    if sym.endswith("-USD"):
        return f"${price:,.0f}"
    return f"${price:.2f}"


def render_market_overview() -> None:
    section_label("Live market tape")
    for group_name, tickers in TAPE_GROUPS:
        cards = []
        for label, sym in tickers.items():
            try:
                q = fetch_quote(sym)
                ch = q["change_pct"] or 0
                price_html = _format_price(sym, q["price"])
                chg_html = format_change_html(ch)
            except Exception:
                price_html = "—"
                chg_html = '<span class="chg-dn">—</span>'
            cards.append(
                f'<div class="fh-tape-card">'
                f'<div class="label">{label}</div>'
                f'<div class="price">{price_html}</div>'
                f'{chg_html}</div>'
            )
        st.markdown(
            f'<p class="fh-section-label" style="margin-top:0.75rem">{group_name}</p>'
            f'<div class="fh-tape-row">{"".join(cards)}</div>',
            unsafe_allow_html=True,
        )