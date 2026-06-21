"""Options P/L calculator, Greeks, and option chain."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from lib.greeks import black_scholes


def payoff_at_expiry(
    prices: np.ndarray,
    strike: float,
    premium: float,
    contracts: int,
    option_type: str,
    position: str,
) -> np.ndarray:
    mult = 100 * contracts
    intrinsic_call = np.maximum(prices - strike, 0)
    intrinsic_put = np.maximum(strike - prices, 0)
    intrinsic = intrinsic_call if option_type == "Call" else intrinsic_put
    if position == "Long":
        return (intrinsic - premium) * mult
    return (premium - intrinsic) * mult


def _days_to_expiry(expiry_str: str) -> float:
    try:
        exp = datetime.strptime(expiry_str, "%Y-%m-%d")
        return max((exp - datetime.now()).days / 365.0, 1 / 365)
    except Exception:
        return 30 / 365


def render_options(default_ticker: str) -> None:
    tab_pl, tab_greeks, tab_chain = st.tabs(["P/L Calculator", "Greeks", "Chain + IV"])

    with tab_pl:
        _render_payoff(default_ticker)

    with tab_greeks:
        _render_greeks(default_ticker)

    with tab_chain:
        _render_chain_iv(default_ticker)


def _render_payoff(default_ticker: str) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Underlying", value=default_ticker, key="opt_ticker").upper().strip()
    with col2:
        option_type = st.selectbox("Type", ["Call", "Put"], key="opt_type")
    with col3:
        position = st.selectbox("Position", ["Long", "Short"], key="opt_pos")

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        strike = st.number_input("Strike ($)", min_value=0.01, value=100.0, step=1.0, key="opt_strike")
    with col5:
        premium = st.number_input("Premium ($/contract)", min_value=0.01, value=5.0, step=0.5, key="opt_prem")
    with col6:
        contracts = st.number_input("Contracts", min_value=1, value=1, step=1, key="opt_contracts")
    with col7:
        spot_override = st.number_input("Spot (0=live)", min_value=0.0, value=0.0, step=1.0, key="opt_spot")

    spot = _get_spot(ticker, spot_override, strike)
    lo, hi = max(0.01, spot * 0.7), spot * 1.3
    prices = np.linspace(lo, hi, 200)
    pnl = payoff_at_expiry(prices, strike, premium, contracts, option_type, position)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices, y=pnl, mode="lines", line=dict(color="#7dd3a0", width=2)))
    fig.add_hline(y=0, line_dash="dash", line_color="#666")
    fig.add_vline(x=spot, line_dash="dot", line_color="#58a6ff", annotation_text=f"Spot ${spot:.2f}")
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=40, r=20, t=50, b=40),
                      xaxis_title="Price at expiry", yaxis_title="P/L ($)")
    st.plotly_chart(fig, width="stretch")

    mult = 100 * contracts
    breakeven = strike + premium if option_type == "Call" else strike - premium
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spot", f"${spot:.2f}")
    m2.metric("Breakeven", f"${breakeven:.2f}")
    if position == "Long":
        m3.metric("Max loss", f"-${premium * mult:,.0f}")
        m4.metric("Max gain", "∞" if option_type == "Call" else f"${(strike - premium) * mult:,.0f}")
    else:
        m3.metric("Max gain", f"${premium * mult:,.0f}")
        m4.metric("Max loss", "∞" if option_type == "Call" else f"${(strike - premium) * mult:,.0f}")


def _render_greeks(default_ticker: str) -> None:
    st.caption("Black-Scholes model — educational estimates")

    c1, c2, c3 = st.columns(3)
    with c1:
        ticker = st.text_input("Ticker", value=default_ticker, key="gk_ticker").upper()
    with c2:
        option_type = st.selectbox("Type", ["call", "put"], key="gk_type")
    with c3:
        expiry = st.text_input("Expiry (YYYY-MM-DD)", value="2026-07-17", key="gk_exp")

    c4, c5, c6, c7 = st.columns(4)
    with c4:
        strike = st.number_input("Strike", min_value=0.01, value=100.0, key="gk_strike")
    with c5:
        iv = st.number_input("IV (%)", min_value=1.0, value=30.0, step=1.0, key="gk_iv") / 100
    with c6:
        rate = st.number_input("Risk-free rate (%)", min_value=0.0, value=4.5, step=0.1, key="gk_rate") / 100
    with c7:
        spot = st.number_input("Spot (0=live)", min_value=0.0, value=0.0, key="gk_spot")

    spot = _get_spot(ticker, spot, strike)
    t = _days_to_expiry(expiry)
    g = black_scholes(spot, strike, t, rate, iv, option_type)

    st.subheader("Greeks")
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    g1.metric("Theoretical price", f"${g.price:.2f}")
    g2.metric("Delta", f"{g.delta:.4f}")
    g3.metric("Gamma", f"{g.gamma:.4f}")
    g4.metric("Theta", f"${g.theta:.2f}/day")
    g5.metric("Vega", f"${g.vega:.2f}")
    g6.metric("Rho", f"${g.rho:.2f}")

    st.markdown("""
| Greek | Meaning |
|-------|---------|
| **Delta** | $ change in option per $1 move in stock |
| **Gamma** | How fast delta changes |
| **Theta** | Time decay per day |
| **Vega** | $ change per 1% IV move |
| **Rho** | Sensitivity to interest rates |
""")

    # Delta exposure chart
    spots = np.linspace(spot * 0.85, spot * 1.15, 50)
    deltas = [black_scholes(s, strike, t, rate, iv, option_type).delta for s in spots]
    fig = go.Figure(go.Scatter(x=spots, y=deltas, line=dict(color="#7dd3a0", width=2)))
    fig.add_vline(x=spot, line_dash="dot", line_color="#58a6ff")
    fig.update_layout(template="plotly_dark", height=280, title="Delta across spot prices", margin=dict(t=40, b=20))
    st.plotly_chart(fig, width="stretch")


def _render_chain_iv(default_ticker: str) -> None:
    ticker = st.text_input("Ticker", value=default_ticker, key="ch_ticker").upper()
    if not ticker:
        return

    try:
        t = yf.Ticker(ticker)
        expiries = t.options
        if not expiries:
            st.info("No options for this ticker.")
            return

        expiry = st.selectbox("Expiry", expiries[:12], key="ch_exp")
        side = st.radio("Side", ["Calls", "Puts"], horizontal=True, key="ch_side")
        chain = t.option_chain(expiry)
        table = chain.calls if side == "Calls" else chain.puts

        spot = _get_spot(ticker, 0, 100)
        t_years = _days_to_expiry(expiry)

        enriched = table.copy()
        opt_type = "call" if side == "Calls" else "put"
        deltas, gammas, thetas = [], [], []
        for _, row in enriched.iterrows():
            iv = row.get("impliedVolatility") or 0.3
            if iv <= 0:
                iv = 0.3
            g = black_scholes(spot, row["strike"], t_years, 0.045, iv, opt_type)
            deltas.append(round(g.delta, 3))
            gammas.append(round(g.gamma, 4))
            thetas.append(round(g.theta, 2))

        enriched["delta"] = deltas
        enriched["gamma"] = gammas
        enriched["theta"] = thetas
        enriched["IV %"] = (enriched["impliedVolatility"] * 100).round(1)

        # IV rank proxy using HV
        hist = yf.download(ticker, period="1y", progress=False, auto_adjust=True)
        if not hist.empty:
            hv = hist["Close"].pct_change().rolling(30).std().iloc[-1] * np.sqrt(252) * 100
            avg_iv = enriched["IV %"].mean()
            st.metric("30d HV (annualized)", f"{hv:.1f}%", delta=f"Avg chain IV {avg_iv:.1f}%")

        show = enriched[["strike", "lastPrice", "bid", "ask", "IV %", "delta", "gamma", "theta", "volume", "openInterest"]]
        st.dataframe(show, width="stretch", hide_index=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=enriched["strike"], y=enriched["IV %"], mode="lines+markers", name="IV"))
        fig.add_vline(x=spot, line_dash="dot", annotation_text="Spot")
        fig.update_layout(template="plotly_dark", height=300, title="IV smile/skew by strike", margin=dict(t=40, b=20))
        st.plotly_chart(fig, width="stretch")

    except Exception as e:
        st.warning(f"Chain unavailable: {e}")


def _get_spot(ticker: str, override: float, fallback: float) -> float:
    if override > 0:
        return override
    if not ticker:
        return fallback
    try:
        hist = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
        if not hist.empty:
            col = hist["Close"]
            if isinstance(col, pd.DataFrame):
                col = col.iloc[:, 0]
            return float(col.iloc[-1])
    except Exception:
        pass
    return fallback