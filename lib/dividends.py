"""Dividend tracker for watchlist."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from lib.data import fetch_info


def render_dividends(watchlist: list[str]) -> None:
    st.subheader("Dividend Screener")
    st.caption("Yield and payout data for your watchlist")

    rows = []
    for sym in watchlist:
        try:
            info = fetch_info(sym)
            dy = info.get("dividendYield")
            if not dy and dy != 0:
                continue
            rows.append({
                "Ticker": sym,
                "Yield %": round(dy * 100, 2) if dy else 0,
                "Annual div": info.get("dividendRate"),
                "Payout ratio": round(info.get("payoutRatio", 0) * 100, 1) if info.get("payoutRatio") else None,
                "Ex-div date": str(info.get("exDividendDate", ""))[:10] or "—",
                "Sector": info.get("sector", "—"),
            })
        except Exception:
            continue

    if rows:
        df = pd.DataFrame(rows).sort_values("Yield %", ascending=False)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No dividend data for current watchlist tickers.")

    st.divider()
    st.subheader("Dividend history")

    ticker = st.selectbox("Ticker", watchlist or ["SPY"], key="div_ticker")
    period = st.selectbox("History", ["1y", "2y", "5y", "max"], index=2, key="div_period")

    try:
        t = yf.Ticker(ticker)
        divs = t.dividends
        if divs is not None and not divs.empty:
            if period != "max":
                years = int(period.replace("y", ""))
                cutoff = divs.index.max() - pd.DateOffset(years=years)
                divs = divs[divs.index >= cutoff]
            fig = go.Figure(go.Bar(x=divs.index, y=divs.values, marker_color="#7dd3a0"))
            fig.update_layout(
                template="plotly_dark", height=300,
                title=f"{ticker} dividend payments",
                xaxis_title="Date", yaxis_title="$/share",
                margin=dict(l=40, r=20, t=40, b=40),
            )
            st.plotly_chart(fig, width="stretch")

            annual = divs.resample("YE").sum()
            st.markdown("**Annual dividends**")
            st.dataframe(annual.to_frame("Total $/share").reset_index(), hide_index=True)
        else:
            st.info(f"{ticker} has no dividend history or doesn't pay dividends.")
    except Exception as e:
        st.warning(f"Could not load dividend history: {e}")