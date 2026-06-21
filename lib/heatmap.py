"""Sector performance heatmap."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import fetch_history

SECTOR_ETFS = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Consumer Disc.": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication": "XLC",
}


def render_sector_heatmap() -> None:
    st.subheader("Sector Performance")
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "YTD"], index=2, key="heat_period")

    rows = []
    with st.spinner("Loading sectors…"):
        for sector, etf in SECTOR_ETFS.items():
            try:
                if period == "YTD":
                    hist = fetch_history(etf, period="ytd")
                else:
                    hist = fetch_history(etf, period=period)
                if hist.empty or len(hist) < 2:
                    continue
                ret = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
                rows.append({"Sector": sector, "ETF": etf, "Return %": round(ret, 2)})
            except Exception:
                continue

    if not rows:
        st.warning("Could not load sector data.")
        return

    df = pd.DataFrame(rows).sort_values("Return %", ascending=True)
    colors = ["#ff6b6b" if r < 0 else "#7dd3a0" for r in df["Return %"]]

    fig = go.Figure(go.Bar(
        x=df["Return %"], y=df["Sector"], orientation="h",
        marker_color=colors,
        text=[f"{r:+.1f}%" for r in df["Return %"]],
        textposition="outside",
    ))
    fig.update_layout(
        template="plotly_dark", height=400,
        title=f"Sector ETF returns — {period}",
        xaxis_title="Return %", margin=dict(l=20, r=60, t=40, b=20),
    )
    st.plotly_chart(fig, width="stretch")