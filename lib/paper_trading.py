"""Paper trading simulator."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.data import fetch_quote

PAPER_PATH = Path(__file__).resolve().parent.parent / "paper_trading.json"
DEFAULT_CASH = 100_000.0


def _default_account() -> dict:
    return {
        "cash": DEFAULT_CASH,
        "starting_cash": DEFAULT_CASH,
        "positions": {},
        "history": [],
    }


def load_paper() -> dict:
    if PAPER_PATH.exists():
        try:
            data = json.loads(PAPER_PATH.read_text())
            data.setdefault("positions", {})
            data.setdefault("history", [])
            return data
        except Exception:
            pass
    return _default_account()


def save_paper(account: dict) -> None:
    PAPER_PATH.write_text(json.dumps(account, indent=2))


def _log_trade(account: dict, action: str, ticker: str, shares: float, price: float) -> None:
    account["history"].append({
        "time": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "ticker": ticker,
        "shares": shares,
        "price": price,
        "total": round(shares * price, 2),
    })


def buy(account: dict, ticker: str, shares: float, price: float) -> str | None:
    cost = shares * price
    if cost > account["cash"]:
        return f"Insufficient cash. Need ${cost:,.2f}, have ${account['cash']:,.2f}"
    account["cash"] -= cost
    pos = account["positions"].get(ticker, {"shares": 0, "avg_cost": 0})
    total_shares = pos["shares"] + shares
    pos["avg_cost"] = (pos["avg_cost"] * pos["shares"] + price * shares) / total_shares
    pos["shares"] = total_shares
    account["positions"][ticker] = pos
    _log_trade(account, "BUY", ticker, shares, price)
    return None


def sell(account: dict, ticker: str, shares: float, price: float) -> str | None:
    pos = account["positions"].get(ticker)
    if not pos or pos["shares"] < shares:
        held = pos["shares"] if pos else 0
        return f"Insufficient shares. Have {held}, tried to sell {shares}"
    proceeds = shares * price
    account["cash"] += proceeds
    pos["shares"] -= shares
    if pos["shares"] <= 0:
        del account["positions"][ticker]
    else:
        account["positions"][ticker] = pos
    _log_trade(account, "SELL", ticker, shares, price)
    return None


def account_value(account: dict) -> tuple[float, float, list[dict]]:
    positions_rows = []
    holdings_value = 0.0
    for ticker, pos in account["positions"].items():
        try:
            q = fetch_quote(ticker)
            price = q["price"] or pos["avg_cost"]
        except Exception:
            price = pos["avg_cost"]
        mv = pos["shares"] * price
        cost = pos["shares"] * pos["avg_cost"]
        pnl = mv - cost
        holdings_value += mv
        positions_rows.append({
            "Ticker": ticker,
            "Shares": pos["shares"],
            "Avg cost": round(pos["avg_cost"], 2),
            "Price": round(price, 2),
            "Market value": round(mv, 2),
            "P/L": round(pnl, 2),
            "P/L %": round(pnl / cost * 100, 2) if cost else 0,
        })
    total = account["cash"] + holdings_value
    return total, holdings_value, positions_rows


def render_paper_trading() -> None:
    st.subheader("Paper Trading")
    st.caption("Practice with $100k virtual cash — no real money")

    if "paper" not in st.session_state:
        st.session_state.paper = load_paper()

    acct = st.session_state.paper
    total, holdings_val, positions = account_value(acct)
    pnl = total - acct["starting_cash"]
    pnl_pct = pnl / acct["starting_cash"] * 100

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total equity", f"${total:,.2f}")
    m2.metric("Cash", f"${acct['cash']:,.2f}")
    m3.metric("Holdings", f"${holdings_val:,.2f}")
    m4.metric("Total P/L", f"${pnl:,.2f}", delta=f"{pnl_pct:+.1f}%")

    tab_trade, tab_pos, tab_hist = st.tabs(["Trade", "Positions", "History"])

    with tab_trade:
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        with c1:
            ticker = st.text_input("Ticker", placeholder="AAPL", key="pt_ticker").upper()
        with c2:
            side = st.selectbox("Side", ["BUY", "SELL"], key="pt_side")
        with c3:
            shares = st.number_input("Shares", min_value=0.01, value=10.0, step=1.0, key="pt_shares")
        with c4:
            use_live = st.checkbox("Live price", value=True, key="pt_live")
        with c5:
            manual_price = st.number_input("Limit ($)", min_value=0.01, value=100.0, key="pt_price")

        if ticker:
            try:
                live = fetch_quote(ticker)["price"]
                if live:
                    st.caption(f"Live: **${live:.2f}**")
            except Exception:
                live = manual_price
        else:
            live = manual_price

        price = live if use_live and live else manual_price

        if st.button(f"{side} {shares} {ticker or '…'} @ ${price:.2f}", type="primary", key="pt_exec"):
            if not ticker:
                st.error("Enter a ticker.")
            elif side == "BUY":
                err = buy(acct, ticker, shares, price)
                if err:
                    st.error(err)
                else:
                    save_paper(acct)
                    st.success(f"Bought {shares} {ticker} @ ${price:.2f}")
                    st.rerun()
            else:
                err = sell(acct, ticker, shares, price)
                if err:
                    st.error(err)
                else:
                    save_paper(acct)
                    st.success(f"Sold {shares} {ticker} @ ${price:.2f}")
                    st.rerun()

    with tab_pos:
        if positions:
            df = pd.DataFrame(positions)
            st.dataframe(df, width="stretch", hide_index=True)
            if len(df) > 1:
                fig = px.pie(df, values="Market value", names="Ticker", hole=0.4,
                             color_discrete_sequence=px.colors.sequential.Teal)
                fig.update_layout(template="plotly_dark", height=300, margin=dict(t=20, b=20))
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("No open positions. Place a trade to get started.")

    with tab_hist:
        hist = acct.get("history", [])
        if hist:
            hdf = pd.DataFrame(hist).iloc[::-1]
            st.dataframe(hdf, width="stretch", hide_index=True)
        else:
            st.info("No trades yet.")

    if st.button("Reset account ($100k)", key="pt_reset"):
        st.session_state.paper = _default_account()
        save_paper(st.session_state.paper)
        st.rerun()