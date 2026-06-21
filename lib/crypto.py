"""Cryptocurrency dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from lib.data import fetch_history, fetch_info, fetch_quote
from lib.technicals import compute_macd, compute_rsi

CRYPTO_WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
    "ADA-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "DOT-USD",
]


def render_crypto() -> None:
    st.subheader("Crypto Markets")

    # Live tape
    cols = st.columns(5)
    for col, sym in zip(cols, CRYPTO_WATCHLIST[:5]):
        try:
            q = fetch_quote(sym)
            name = sym.replace("-USD", "")
            col.metric(name, f"${q['price']:,.0f}", delta=f"{q['change_pct']:+.2f}%")
        except Exception:
            col.metric(sym.replace("-USD", ""), "—")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Chart", "Screener", "Compare"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            coin = st.selectbox("Coin", CRYPTO_WATCHLIST, format_func=lambda x: x.replace("-USD", ""), key="cr_coin")
        with c2:
            period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=4, key="cr_period")
        with c3:
            interval = st.selectbox("Interval", ["1h", "1d"], index=1 if period not in ("1d", "5d") else 0, key="cr_interval")

        with st.spinner("Loading…"):
            df = fetch_history(coin, period=period, interval=interval)

        if df.empty:
            st.error("No data.")
            return

        close = df["Close"]
        rsi = compute_rsi(close)
        macd, signal, hist = compute_macd(close)

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.55, 0.22, 0.23])
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Price",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=close.rolling(20).mean(), name="SMA 20", line=dict(color="#58a6ff")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI", line=dict(color="#7dd3a0")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#ff6b6b", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#7dd3a0", row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=macd, name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=signal, name="Signal"), row=3, col=1)
        fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False, margin=dict(t=30, b=20))

        st.plotly_chart(fig, width="stretch")

        info = fetch_info(coin)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Market cap", f"${info.get('marketCap', 0)/1e9:.1f}B" if info.get("marketCap") else "—")
        m2.metric("24h volume", f"${info.get('volume24Hr', 0)/1e9:.2f}B" if info.get("volume24Hr") else "—")
        m3.metric("52w high", f"${info.get('fiftyTwoWeekHigh', 0):,.0f}" if info.get("fiftyTwoWeekHigh") else "—")
        m4.metric("52w low", f"${info.get('fiftyTwoWeekLow', 0):,.0f}" if info.get("fiftyTwoWeekLow") else "—")

    with tab2:
        st.caption("Top coins by 24h change")
        rows = []
        for sym in CRYPTO_WATCHLIST:
            try:
                q = fetch_quote(sym)
                info = fetch_info(sym)
                rows.append({
                    "Coin": sym.replace("-USD", ""),
                    "Price": q["price"],
                    "Change %": q["change_pct"],
                    "Market Cap": info.get("marketCap"),
                    "Volume": info.get("volume24Hr") or info.get("volume"),
                })
            except Exception:
                continue
        if rows:
            cdf = pd.DataFrame(rows).sort_values("Change %", ascending=False)
            st.dataframe(cdf, width="stretch", hide_index=True,
                column_config={"Market Cap": st.column_config.NumberColumn(format="$%d"),
                               "Price": st.column_config.NumberColumn(format="$%.2f")})

    with tab3:
        raw = st.text_input("Coins", value="BTC-USD, ETH-USD, SOL-USD", key="cr_cmp")
        coins = [c.strip().upper() if "-USD" in c.upper() else f"{c.strip().upper()}-USD" for c in raw.split(",") if c.strip()]
        period = st.selectbox("Compare period", ["1mo", "3mo", "6mo", "1y"], index=2, key="cr_cmp_period")
        series = {}
        for sym in coins[:6]:
            hist = fetch_history(sym, period=period)
            if not hist.empty:
                series[sym.replace("-USD", "")] = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
        if series:
            fig = go.Figure()
            for sym, s in series.items():
                fig.add_trace(go.Scatter(x=s.index, y=s.values, name=sym))
            fig.update_layout(template="plotly_dark", height=400, title="Normalized crypto returns %", margin=dict(t=40, b=20))
            st.plotly_chart(fig, width="stretch")