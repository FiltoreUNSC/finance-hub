"""Simple strategy backtester."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import fetch_history
from lib.ui import section_header


def run_sma_crossover(df: pd.DataFrame, fast: int, slow: int) -> pd.DataFrame:
    close = df["Close"].copy()
    df = df.copy()
    df["fast_sma"] = close.rolling(fast).mean()
    df["slow_sma"] = close.rolling(slow).mean()
    df["signal"] = 0
    df.loc[df["fast_sma"] > df["slow_sma"], "signal"] = 1
    df["position"] = df["signal"].shift(1).fillna(0)
    df["returns"] = close.pct_change()
    df["strategy"] = df["position"] * df["returns"]
    df["buy_hold"] = df["returns"]
    df["equity_strategy"] = (1 + df["strategy"]).cumprod()
    df["equity_bh"] = (1 + df["buy_hold"]).cumprod()
    return df.dropna()


def run_rsi_reversal(df: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.DataFrame:
    close = df["Close"].copy()
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    df = df.copy()
    df["rsi"] = rsi
    df["signal"] = 0
    df.loc[df["rsi"] < oversold, "signal"] = 1
    df.loc[df["rsi"] > overbought, "signal"] = 0
    df["position"] = df["signal"].ffill().shift(1).fillna(0)
    df["returns"] = close.pct_change()
    df["strategy"] = df["position"] * df["returns"]
    df["buy_hold"] = df["returns"]
    df["equity_strategy"] = (1 + df["strategy"]).cumprod()
    df["equity_bh"] = (1 + df["buy_hold"]).cumprod()
    return df.dropna()


def render_backtest(default_ticker: str) -> None:
    section_header("Strategy Backtester", "Educational only — no fees, simplified Sharpe, past ≠ future")

    c1, c2, c3 = st.columns(3)
    with c1:
        ticker = st.text_input("Ticker", value=default_ticker, key="bt_ticker").upper()
    with c2:
        period = st.selectbox("Period", ["1y", "2y", "5y", "10y"], index=2, key="bt_period")
    with c3:
        strategy = st.selectbox("Strategy", ["SMA Crossover", "RSI Reversal"], key="bt_strat")

    if strategy == "SMA Crossover":
        c4, c5 = st.columns(2)
        with c4:
            fast = st.number_input("Fast SMA", min_value=5, value=20, step=1, key="bt_fast")
        with c5:
            slow = st.number_input("Slow SMA", min_value=10, value=50, step=1, key="bt_slow")
    else:
        c4, c5, c6 = st.columns(3)
        with c4:
            rsi_period = st.number_input("RSI period", min_value=5, value=14, key="bt_rsi_p")
        with c5:
            oversold = st.number_input("Oversold", min_value=10, value=30, key="bt_os")
        with c6:
            overbought = st.number_input("Overbought", min_value=50, value=70, key="bt_ob")

    if st.button("Run backtest", type="primary", key="bt_run"):
        with st.spinner("Backtesting…"):
            raw = fetch_history(ticker, period=period)
            if raw.empty or len(raw) < 60:
                st.error("Not enough data.")
                return

            if strategy == "SMA Crossover":
                if fast >= slow:
                    st.error("Fast SMA must be less than slow SMA.")
                    return
                bt = run_sma_crossover(raw, fast, slow)
            else:
                bt = run_rsi_reversal(raw, rsi_period, oversold, overbought)

        strat_ret = (bt["equity_strategy"].iloc[-1] - 1) * 100
        bh_ret = (bt["equity_bh"].iloc[-1] - 1) * 100
        sharpe = bt["strategy"].mean() / bt["strategy"].std() * np.sqrt(252) if bt["strategy"].std() else 0
        max_dd = ((bt["equity_strategy"] / bt["equity_strategy"].cummax()) - 1).min() * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Strategy return", f"{strat_ret:+.1f}%")
        m2.metric("Buy & hold", f"{bh_ret:+.1f}%")
        m3.metric("Sharpe (approx)", f"{sharpe:.2f}")
        m4.metric("Max drawdown", f"{max_dd:.1f}%")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bt.index, y=bt["equity_strategy"], name="Strategy", line=dict(color="#7dd3a0", width=2)))
        fig.add_trace(go.Scatter(x=bt.index, y=bt["equity_bh"], name="Buy & hold", line=dict(color="#58a6ff", width=2, dash="dot")))
        fig.update_layout(
            template="plotly_dark", height=400,
            title=f"{ticker} — {strategy}",
            xaxis_title="Date", yaxis_title="Growth of $1",
            margin=dict(l=40, r=20, t=50, b=40),
        )
        st.plotly_chart(fig, width="stretch")

        trades = bt["position"].diff().fillna(0)
        buy_dates = bt.index[trades > 0]
        sell_dates = bt.index[trades < 0]
        st.caption(f"Signals: {len(buy_dates)} buys, {len(sell_dates)} sells over period")