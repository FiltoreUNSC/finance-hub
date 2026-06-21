"""Technical analysis — daily and intraday."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from lib.data import fetch_history


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist


def compute_bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = close.rolling(window).mean()
    std = close.rolling(window).std()
    return mid, mid + num_std * std, mid - num_std * std


def _plot_chart(df: pd.DataFrame, ticker: str, show_sma: list[int], show_bb: bool, show_volume: bool) -> go.Figure:
    close = df["Close"]
    rsi = compute_rsi(close)
    macd, signal, hist = compute_macd(close)
    rows = 4 if show_volume else 3
    heights = [0.45, 0.15, 0.18, 0.18] if show_volume else [0.55, 0.22, 0.23]

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=heights[:rows],
        subplot_titles=tuple(
            [f"{ticker} Price", "RSI (14)", "MACD"] + (["Volume"] if show_volume else [])
        ),
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="OHLC",
    ), row=1, col=1)

    colors = {20: "#58a6ff", 50: "#f0883e", 200: "#a371f7"}
    for window in show_sma:
        sma = close.rolling(window).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=sma, name=f"SMA {window}",
            line=dict(color=colors.get(window, "#aaa"), width=1),
        ), row=1, col=1)

    if show_bb:
        mid, upper, lower = compute_bollinger(close)
        fig.add_trace(go.Scatter(x=df.index, y=upper, name="BB Upper", line=dict(color="#666", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=lower, name="BB Lower", line=dict(color="#666", width=1, dash="dot"), fill="tonexty"), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI", line=dict(color="#7dd3a0")), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#ff6b6b", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#7dd3a0", row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=macd, name="MACD", line=dict(color="#58a6ff")), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=signal, name="Signal", line=dict(color="#f0883e")), row=3, col=1)
    fig.add_trace(go.Bar(
        x=df.index, y=hist, name="Histogram",
        marker_color=np.where(hist >= 0, "#7dd3a0", "#ff6b6b"),
    ), row=3, col=1)

    if show_volume and "Volume" in df.columns:
        vol_colors = np.where(close >= df["Open"], "#7dd3a0", "#ff6b6b")
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=vol_colors), row=4, col=1)

    h = 820 if show_volume else 720
    fig.update_layout(
        height=h, template="plotly_dark", xaxis_rangeslider_visible=False,
        margin=dict(l=40, r=20, t=40, b=20), showlegend=True,
        legend=dict(orientation="h", y=1.02),
    )
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    return fig


def render_technicals(default_ticker: str) -> None:
    tab_daily, tab_intra = st.tabs(["Daily", "Intraday"])

    with tab_daily:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            ticker = st.text_input("Ticker", value=default_ticker, key="ta_ticker").upper().strip()
        with col2:
            period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2, key="ta_period")
        with col3:
            show_sma = st.multiselect("SMA", [20, 50, 200], default=[20, 50], key="ta_sma")
        with col4:
            show_bb = st.checkbox("Bollinger", value=False, key="ta_bb")

        if not ticker:
            st.warning("Enter a ticker.")
            return

        with st.spinner(f"Loading {ticker}…"):
            df = fetch_history(ticker, period=period)

        if df.empty or len(df) < 30:
            st.error(f"Not enough data for {ticker}.")
            return

        st.plotly_chart(_plot_chart(df, ticker, show_sma, show_bb, False), width="stretch")
        _metrics(df)

    with tab_intra:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ticker_i = st.text_input("Ticker", value=default_ticker, key="ta_i_ticker").upper().strip()
        with col2:
            period_i = st.selectbox("Period", ["1d", "5d"], index=1, key="ta_i_period")
        with col3:
            interval = st.selectbox("Interval", ["1m", "5m", "15m", "30m", "1h"], index=1, key="ta_i_interval")
        with col4:
            show_vol = st.checkbox("Volume", value=True, key="ta_i_vol")

        if not ticker_i:
            return

        with st.spinner(f"Loading intraday {ticker_i}…"):
            df = fetch_history(ticker_i, period=period_i, interval=interval)

        if df.empty:
            st.error("No intraday data. Try 5d period with 5m/15m interval.")
            return

        st.plotly_chart(_plot_chart(df, ticker_i, [20], False, show_vol), width="stretch")

        if "Volume" in df.columns:
            v1, v2, v3 = st.columns(3)
            v1.metric("Bars", len(df))
            v2.metric("Last", f"${df['Close'].iloc[-1]:.2f}")
            v3.metric("Session volume", f"{df['Volume'].sum():,.0f}")
        _metrics(df)


def _metrics(df: pd.DataFrame) -> None:
    close = df["Close"]
    rsi = compute_rsi(close)
    macd, _, _ = compute_macd(close)
    last_rsi = rsi.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Last", f"${close.iloc[-1]:.2f}")
    c2.metric("RSI", f"{last_rsi:.1f}" if pd.notna(last_rsi) else "—")
    c3.metric("MACD", f"{macd.iloc[-1]:.2f}")
    if pd.notna(last_rsi):
        if last_rsi > 70:
            c4.metric("Signal", "Overbought")
        elif last_rsi < 30:
            c4.metric("Signal", "Oversold")
        else:
            c4.metric("Signal", "Neutral")