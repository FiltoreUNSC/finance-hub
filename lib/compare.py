"""Multi-ticker comparison."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import fetch_history, fetch_quote


def render_compare(watchlist: list[str]) -> None:
    st.subheader("Compare tickers")

    default = ", ".join(watchlist[:4]) if watchlist else "SPY, QQQ, AAPL, NVDA"
    raw = st.text_input("Tickers (comma-separated)", value=default, key="cmp_tickers")
    tickers = [t.strip().upper() for t in raw.split(",") if t.strip()][:6]

    if len(tickers) < 2:
        st.warning("Enter at least 2 tickers.")
        return

    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3, key="cmp_period")

    with st.spinner("Loading…"):
        # Normalized performance chart
        series = {}
        rows = []
        for sym in tickers:
            hist = fetch_history(sym, period=period)
            if hist.empty:
                continue
            norm = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
            series[sym] = norm
            q = fetch_quote(sym)
            rows.append({
                "Ticker": sym,
                "Price": q["price"],
                "Change %": q["change_pct"],
                "P/E": q["pe"],
                "Sector": q["sector"],
                "Market Cap": q["market_cap"],
            })

    if not series:
        st.error("No data loaded.")
        return

    fig = go.Figure()
    colors = ["#7dd3a0", "#58a6ff", "#f0883e", "#a371f7", "#ff6b6b", "#ffd700"]
    for i, (sym, s) in enumerate(series.items()):
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=sym,
            line=dict(color=colors[i % len(colors)], width=2),
        ))

    fig.update_layout(
        template="plotly_dark", height=420,
        title="Normalized return (%) — start = 0%",
        xaxis_title="Date", yaxis_title="Return %",
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", y=1.08),
    )
    st.plotly_chart(fig, width="stretch")

    df = pd.DataFrame(rows)
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={"Market Cap": st.column_config.NumberColumn(format="$%d")},
    )

    # Correlation matrix
    if len(series) >= 2:
        st.subheader("Correlation")
        combined = pd.DataFrame(series).dropna()
        corr = combined.corr()
        fig2 = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.columns,
            colorscale="Teal",
            zmin=-1, zmax=1,
            text=corr.round(2).values,
            texttemplate="%{text}",
        ))
        fig2.update_layout(template="plotly_dark", height=320, margin=dict(t=30, b=20))
        st.plotly_chart(fig2, width="stretch")