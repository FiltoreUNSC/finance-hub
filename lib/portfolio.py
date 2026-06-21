"""Portfolio tracker with local persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import plotly.graph_objects as go

from lib.data import fetch_history, fetch_info, fetch_quote

PORTFOLIO_PATH = Path(__file__).resolve().parent.parent / "portfolio.json"


def load_portfolio() -> list[dict]:
    if PORTFOLIO_PATH.exists():
        try:
            return json.loads(PORTFOLIO_PATH.read_text())
        except Exception:
            return []
    return []


def save_portfolio(positions: list[dict]) -> None:
    PORTFOLIO_PATH.write_text(json.dumps(positions, indent=2))


def render_portfolio() -> None:
    st.subheader("Portfolio")

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = load_portfolio()

    with st.form("add_position", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ticker = st.text_input("Ticker", placeholder="AAPL").upper()
        with c2:
            shares = st.number_input("Shares", min_value=0.01, value=10.0, step=1.0)
        with c3:
            cost = st.number_input("Avg cost ($)", min_value=0.01, value=100.0, step=1.0)
        with c4:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Add position", type="primary")

    if submitted and ticker:
        st.session_state.portfolio.append({
            "ticker": ticker,
            "shares": float(shares),
            "cost": float(cost),
        })
        save_portfolio(st.session_state.portfolio)
        st.success(f"Added {shares} shares of {ticker}")
        st.rerun()

    positions = st.session_state.portfolio
    if not positions:
        st.info("No positions yet. Add your first holding above.")
        return

    rows = []
    total_cost = 0.0
    total_value = 0.0

    for i, pos in enumerate(positions):
        sym = pos["ticker"]
        sh = pos["shares"]
        cb = pos["cost"]
        try:
            q = fetch_quote(sym)
            price = q["price"] or cb
        except Exception:
            price = cb

        cost_basis = sh * cb
        market_val = sh * price
        pnl = market_val - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0
        total_cost += cost_basis
        total_value += market_val

        rows.append({
            "Ticker": sym,
            "Shares": sh,
            "Avg Cost": cb,
            "Price": round(price, 2),
            "Market Value": round(market_val, 2),
            "P/L $": round(pnl, 2),
            "P/L %": round(pnl_pct, 2),
            "_idx": i,
        })

    df = pd.DataFrame(rows)

    m1, m2, m3 = st.columns(3)
    total_pnl = total_value - total_cost
    m1.metric("Portfolio value", f"${total_value:,.2f}")
    m2.metric("Total cost", f"${total_cost:,.2f}")
    m3.metric("Total P/L", f"${total_pnl:,.2f}", delta=f"{(total_pnl/total_cost*100):.1f}%" if total_cost else None)

    st.dataframe(
        df.drop(columns=["_idx"]),
        width="stretch",
        hide_index=True,
    )

    chart1, chart2 = st.columns(2)
    with chart1:
        if len(df) > 0:
            fig = px.pie(
                df, values="Market Value", names="Ticker", hole=0.45,
                color_discrete_sequence=px.colors.sequential.Teal,
                title="By ticker",
            )
            fig.update_layout(template="plotly_dark", height=320, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig, width="stretch")

    with chart2:
        sectors: dict[str, float] = {}
        for pos in positions:
            try:
                info = fetch_info(pos["ticker"])
                sec = info.get("sector") or "Unknown"
                q = fetch_quote(pos["ticker"])
                val = pos["shares"] * (q["price"] or pos["cost"])
                sectors[sec] = sectors.get(sec, 0) + val
            except Exception:
                pass
        if sectors:
            sdf = pd.DataFrame({"Sector": list(sectors.keys()), "Value": list(sectors.values())})
            fig2 = px.pie(sdf, values="Value", names="Sector", hole=0.45, color_discrete_sequence=px.colors.sequential.Blues_r, title="By sector")
            fig2.update_layout(template="plotly_dark", height=320, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig2, width="stretch")

    if len(df) > 1:
        st.subheader("Portfolio correlation (6mo daily returns)")
        with st.spinner("Computing…"):
            rets = {}
            for pos in positions:
                sym = pos["ticker"]
                hist = fetch_history(sym, period="6mo")
                if not hist.empty:
                    rets[sym] = hist["Close"].pct_change()
            combined = pd.DataFrame(rets).dropna()
            if len(combined.columns) > 1:
                corr = combined.corr()
                fig3 = go.Figure(data=go.Heatmap(
                    z=corr.values, x=corr.columns, y=corr.columns,
                    colorscale="Teal", zmin=-1, zmax=1,
                    text=corr.round(2).values, texttemplate="%{text}",
                ))
                fig3.update_layout(template="plotly_dark", height=280, margin=dict(t=20, b=20))
                st.plotly_chart(fig3, width="stretch")

    st.divider()
    st.caption("Remove a position")
    to_remove = st.selectbox(
        "Position",
        options=range(len(positions)),
        format_func=lambda i: f"{positions[i]['ticker']} — {positions[i]['shares']} shares",
        key="rm_pos",
    )
    if st.button("Remove selected", key="rm_btn"):
        st.session_state.portfolio.pop(to_remove)
        save_portfolio(st.session_state.portfolio)
        st.rerun()