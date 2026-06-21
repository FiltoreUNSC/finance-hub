"""Price alerts — local persistence."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from lib.data import fetch_quote

ALERTS_PATH = Path(__file__).resolve().parent.parent / "alerts.json"


def load_alerts() -> list[dict]:
    if ALERTS_PATH.exists():
        try:
            return json.loads(ALERTS_PATH.read_text())
        except Exception:
            return []
    return []


def save_alerts(alerts: list[dict]) -> None:
    ALERTS_PATH.write_text(json.dumps(alerts, indent=2))


def render_alerts_sidebar() -> None:
    if "alerts" not in st.session_state:
        st.session_state.alerts = load_alerts()

    st.subheader("Price alerts")

    with st.form("add_alert", clear_on_submit=True):
        sym = st.text_input("Ticker", placeholder="NVDA").upper()
        c1, c2 = st.columns(2)
        with c1:
            direction = st.selectbox("When price", ["rises above", "falls below"])
        with c2:
            target = st.number_input("Target ($)", min_value=0.01, value=100.0, step=1.0)
        if st.form_submit_button("Add alert"):
            if sym:
                st.session_state.alerts.append({
                    "ticker": sym,
                    "direction": direction,
                    "target": float(target),
                    "triggered": False,
                })
                save_alerts(st.session_state.alerts)
                st.rerun()

    triggered_msgs = []
    active = []
    for alert in st.session_state.alerts:
        if alert.get("triggered"):
            continue
        try:
            q = fetch_quote(alert["ticker"])
            price = q["price"]
            if price is None:
                active.append(alert)
                continue
            hit = (
                (alert["direction"] == "rises above" and price >= alert["target"])
                or (alert["direction"] == "falls below" and price <= alert["target"])
            )
            if hit:
                alert["triggered"] = True
                triggered_msgs.append(
                    f"🔔 **{alert['ticker']}** hit ${price:.2f} ({alert['direction']} ${alert['target']:.2f})"
                )
            else:
                diff = alert["target"] - price
                active.append({**alert, "_price": price, "_diff": diff})
        except Exception:
            active.append(alert)

    save_alerts(st.session_state.alerts)

    for msg in triggered_msgs:
        st.success(msg)

    if not active and not triggered_msgs:
        st.caption("No active alerts")

    for i, a in enumerate(active):
        price = a.get("_price")
        extra = f" · now ${price:.2f}" if price else ""
        st.markdown(f"**{a['ticker']}** {a['direction']} ${a['target']:.2f}{extra}")

    if st.session_state.alerts:
        if st.button("Clear triggered", key="clr_alerts"):
            st.session_state.alerts = [a for a in st.session_state.alerts if not a.get("triggered")]
            save_alerts(st.session_state.alerts)
            st.rerun()