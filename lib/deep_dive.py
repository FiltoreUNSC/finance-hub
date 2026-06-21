"""Stock fundamentals and analyst data."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from lib.data import fetch_info, fetch_quote


def _fmt_large(n) -> str:
    if n is None:
        return "—"
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"


def render_deep_dive(default_ticker: str) -> None:
    ticker = st.text_input("Ticker", value=default_ticker, key="dd_ticker").upper().strip()
    if not ticker:
        return

    with st.spinner(f"Loading {ticker}…"):
        info = fetch_info(ticker)
        q = fetch_quote(ticker)

    if not info:
        st.error(f"No data for {ticker}")
        return

    st.subheader(info.get("longName") or info.get("shortName") or ticker)
    st.caption(f"{info.get('sector', '—')} · {info.get('industry', '—')} · {info.get('exchange', '')}")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Price", f"${q['price']:.2f}" if q["price"] else "—", delta=f"{q['change_pct']:+.2f}%" if q["change_pct"] else None)
    c2.metric("Market cap", _fmt_large(info.get("marketCap")))
    c3.metric("P/E (TTM)", f"{info.get('trailingPE', 0):.1f}" if info.get("trailingPE") else "—")
    c4.metric("Fwd P/E", f"{info.get('forwardPE', 0):.1f}" if info.get("forwardPE") else "—")
    c5.metric("Div yield", f"{(info.get('dividendYield') or 0)*100:.2f}%" if info.get("dividendYield") else "—")
    c6.metric("Beta", f"{info.get('beta', 0):.2f}" if info.get("beta") else "—")

    tab_a, tab_b, tab_c, tab_d = st.tabs(["Fundamentals", "Analysts", "Financials", "Holders"])

    with tab_a:
        left, right = st.columns(2)
        fundamentals = {
            "Valuation": {
                "EPS (TTM)": info.get("trailingEps"),
                "PEG Ratio": info.get("pegRatio"),
                "P/B": info.get("priceToBook"),
                "P/S": info.get("priceToSalesTrailing12Months"),
                "EV/EBITDA": info.get("enterpriseToEbitda"),
            },
            "Profitability": {
                "Profit margin": info.get("profitMargins"),
                "Operating margin": info.get("operatingMargins"),
                "ROE": info.get("returnOnEquity"),
                "ROA": info.get("returnOnAssets"),
            },
            "Growth": {
                "Revenue growth": info.get("revenueGrowth"),
                "Earnings growth": info.get("earningsGrowth"),
                "52w high": info.get("fiftyTwoWeekHigh"),
                "52w low": info.get("fiftyTwoWeekLow"),
            },
            "Trading": {
                "Avg volume": info.get("averageVolume"),
                "Short ratio": info.get("shortRatio"),
                "Short % float": info.get("shortPercentOfFloat"),
                "Insider %": info.get("heldPercentInsiders"),
                "Institutional %": info.get("heldPercentInstitutions"),
            },
        }
        for i, (section, data) in enumerate(fundamentals.items()):
            target = left if i % 2 == 0 else right
            with target:
                st.markdown(f"**{section}**")
                for k, v in data.items():
                    if v is None:
                        disp = "—"
                    elif isinstance(v, float) and (
                        "margin" in k.lower() or "growth" in k.lower() or "%" in k
                        or k.startswith("RO") or "Short" in k or "Insider" in k or "Institutional" in k
                    ):
                        disp = f"{v*100:.2f}%"
                    elif isinstance(v, float):
                        disp = f"{v:,.2f}"
                    else:
                        disp = str(v)
                    st.markdown(f"- {k}: `{disp}`")

    with tab_b:
        rec = info.get("recommendationKey", "—")
        target = info.get("targetMeanPrice")
        st.metric("Consensus", rec.replace("_", " ").title() if rec else "—")
        if target:
            upside = ((target - q["price"]) / q["price"] * 100) if q["price"] else 0
            st.metric("Mean price target", f"${target:.2f}", delta=f"{upside:+.1f}% vs current")

        try:
            t = yf.Ticker(ticker)
            recs = t.recommendations
            if recs is not None and not recs.empty:
                st.markdown("**Recent analyst actions**")
                show = recs.tail(15).reset_index()
                st.dataframe(show, width="stretch", hide_index=True)
            else:
                st.info("No recent analyst actions on file.")
        except Exception:
            st.info("Analyst history unavailable.")

    with tab_c:
        try:
            t = yf.Ticker(ticker)
            fin = t.financials
            if fin is not None and not fin.empty:
                st.markdown("**Annual financials** (recent years)")
                st.dataframe(fin.head(8), width="stretch")
            else:
                st.info("Financial statements unavailable.")
        except Exception:
            st.info("Financial statements unavailable.")

    with tab_d:
        try:
            t = yf.Ticker(ticker)
            inst = t.institutional_holders
            major = t.major_holders
            if major is not None and not major.empty:
                st.markdown("**Ownership breakdown**")
                st.dataframe(major, width="stretch", hide_index=True)
            if inst is not None and not inst.empty:
                st.markdown("**Top institutional holders**")
                st.dataframe(inst.head(15), width="stretch", hide_index=True)
            if (major is None or major.empty) and (inst is None or inst.empty):
                st.info("Holder data unavailable.")
        except Exception:
            st.info("Holder data unavailable.")