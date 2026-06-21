"""Bank account connectivity — Plaid + manual + CSV import."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from lib.links import PLAID_SIGNUP, SUPPORT_EMAIL

BANKS_PATH = Path(__file__).resolve().parent.parent / "banks.json"


def _default_data() -> dict:
    return {"manual_accounts": [], "plaid_items": [], "transactions": []}


def load_banks() -> dict:
    if BANKS_PATH.exists():
        try:
            data = json.loads(BANKS_PATH.read_text())
            for k in ("manual_accounts", "plaid_items", "transactions"):
                data.setdefault(k, [])
            return data
        except Exception:
            pass
    return _default_data()


def save_banks(data: dict) -> None:
    BANKS_PATH.write_text(json.dumps(data, indent=2))


def _plaid_link_html(link_token: str) -> str:
    return f"""
    <div style="padding:1rem;background:#141414;border-radius:8px;border:1px solid #333;">
      <p style="color:#aaa;font-family:sans-serif;margin-bottom:1rem;">
        Connect your bank securely via Plaid (read-only).
      </p>
      <button id="plaid-link" style="background:#7dd3a0;color:#0a0a0a;border:none;padding:12px 24px;
        border-radius:8px;font-weight:700;cursor:pointer;font-size:14px;">
        Connect Bank Account
      </button>
      <p id="status" style="color:#888;font-size:12px;margin-top:1rem;font-family:sans-serif;"></p>
    </div>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <script>
      const handler = Plaid.create({{
        token: "{link_token}",
        onSuccess: (public_token, metadata) => {{
          document.getElementById('status').innerHTML =
            'Connected! Copy this public token into Finance Hub:<br><code style="color:#7dd3a0;">' +
            public_token + '</code>';
          window.parent.postMessage({{type: 'plaid_success', public_token}}, '*');
        }},
        onExit: (err) => {{
          if (err) document.getElementById('status').textContent = 'Cancelled or error.';
        }},
      }});
      document.getElementById('plaid-link').onclick = () => handler.open();
    </script>
    """


def render_banking() -> None:
    st.subheader("Banking")
    st.caption("Connect accounts via Plaid, add manually, or import CSV statements")

    if "banks" not in st.session_state:
        st.session_state.banks = load_banks()

    data = st.session_state.banks
    tab_plaid, tab_manual, tab_csv, tab_txn = st.tabs([
        "Plaid Connect", "Manual Accounts", "CSV Import", "Transactions",
    ])

    # ── Plaid ──
    with tab_plaid:
        try:
            from lib.plaid_client import (
                create_link_token,
                create_sandbox_connection,
                exchange_public_token,
                fetch_accounts,
                fetch_transactions,
                plaid_available,
            )
            plaid_ok = plaid_available()
        except ImportError:
            plaid_ok = False
            st.warning("Plaid SDK not installed. Run: `pip install plaid-python`")

        if not plaid_ok:
            st.info(
                "Plaid keys required for live bank connections. "
                "Free sandbox keys at dashboard.plaid.com (takes 5 min)."
            )
            st.link_button("Get free Plaid API keys →", PLAID_SIGNUP, type="primary")
            st.markdown("""
**Setup** — create `.streamlit/secrets.toml`:
```toml
[plaid]
client_id = "your_client_id"
secret = "your_sandbox_secret"
```
Then restart the app.
            """)
            st.link_button("Need help?", SUPPORT_EMAIL)
        else:
            st.success("Plaid configured ✓")

            if st.button("Connect sandbox test bank (demo)", type="primary", key="plaid_sandbox"):
                with st.spinner("Connecting First Platypus Bank (sandbox)…"):
                    try:
                        conn = create_sandbox_connection()
                        data["plaid_items"].append({
                            "item_id": conn["item_id"],
                            "access_token": conn["access_token"],
                            "institution": "Sandbox — First Platypus Bank",
                        })
                        save_banks(data)
                        st.success("Sandbox bank connected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

            try:
                link_token = create_link_token()
                components.html(_plaid_link_html(link_token), height=200)
            except Exception as e:
                st.caption(f"Plaid Link unavailable: {e}")

            st.divider()
            st.markdown("**Or paste public token** (from Plaid Link above)")
            pub = st.text_input("Public token", key="plaid_pub_token", type="password")
            if st.button("Exchange token", key="plaid_exchange") and pub:
                try:
                    conn = exchange_public_token(pub.strip())
                    data["plaid_items"].append({
                        "item_id": conn["item_id"],
                        "access_token": conn["access_token"],
                        "institution": "Plaid connected",
                    })
                    save_banks(data)
                    st.success("Bank connected!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Exchange failed: {e}")

            for i, item in enumerate(data.get("plaid_items", [])):
                st.markdown(f"**{item.get('institution', 'Bank')}** — `{item['item_id'][:12]}…`")
                if st.button("Sync accounts", key=f"sync_{i}"):
                    try:
                        accts = fetch_accounts(item["access_token"])
                        for a in accts:
                            data["manual_accounts"] = [
                                x for x in data["manual_accounts"]
                                if x.get("plaid_account_id") != a["account_id"]
                            ]
                            data["manual_accounts"].append({
                                "institution": item.get("institution", "Plaid"),
                                "name": a["official_name"],
                                "type": a["subtype"] or a["type"],
                                "balance": a["balance"],
                                "plaid_account_id": a["account_id"],
                                "source": "plaid",
                            })
                        txns = fetch_transactions(item["access_token"], days=30)
                        for t in txns:
                            t["source"] = "plaid"
                            t["account"] = item.get("institution", "Plaid")
                        data["transactions"] = txns + [
                            x for x in data.get("transactions", []) if x.get("source") != "plaid"
                        ]
                        save_banks(data)
                        st.success(f"Synced {len(accts)} accounts, {len(txns)} transactions")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sync failed: {e}")
                if st.button("Remove connection", key=f"rm_plaid_{i}"):
                    data["plaid_items"].pop(i)
                    save_banks(data)
                    st.rerun()

    # ── Manual ──
    with tab_manual:
        with st.form("manual_bank", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                inst = st.text_input("Institution", placeholder="Chase")
            with c2:
                name = st.text_input("Account name", placeholder="Checking")
            with c3:
                acct_type = st.selectbox("Type", ["Checking", "Savings", "Credit", "Investment", "Other"])
            with c4:
                balance = st.number_input("Balance ($)", value=0.0, step=100.0)
            if st.form_submit_button("Add account", type="primary") and inst:
                data["manual_accounts"].append({
                    "institution": inst,
                    "name": name or acct_type,
                    "type": acct_type,
                    "balance": balance,
                    "source": "manual",
                })
                save_banks(data)
                st.success(f"Added {inst}")
                st.rerun()

        if data["manual_accounts"]:
            rows = [{
                "Institution": a["institution"],
                "Account": a["name"],
                "Type": a["type"],
                "Balance": f"${a['balance']:,.2f}",
                "Source": a.get("source", "manual"),
            } for a in data["manual_accounts"]]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            total = sum(a["balance"] for a in data["manual_accounts"])
            st.metric("Total balance", f"${total:,.2f}")
            if st.button("Clear manual accounts", key="clr_manual"):
                data["manual_accounts"] = [a for a in data["manual_accounts"] if a.get("source") == "plaid"]
                save_banks(data)
                st.rerun()
        else:
            st.info("No accounts yet. Connect via Plaid or add manually.")

    # ── CSV ──
    with tab_csv:
        st.caption("Import bank CSV exports (Date, Description, Amount columns)")
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="bank_csv")
        if uploaded:
            try:
                raw = pd.read_csv(uploaded)
                cols = {c.lower(): c for c in raw.columns}
                date_col = next((cols[k] for k in cols if "date" in k), raw.columns[0])
                desc_col = next((cols[k] for k in cols if "desc" in k or "memo" in k or "name" in k), raw.columns[1])
                amt_col = next((cols[k] for k in cols if "amount" in k or "debit" in k), raw.columns[-1])

                imported = []
                for _, row in raw.iterrows():
                    imported.append({
                        "date": str(row[date_col])[:10],
                        "name": str(row[desc_col]),
                        "amount": float(str(row[amt_col]).replace(",", "").replace("$", "") or 0),
                        "category": "CSV import",
                        "source": "csv",
                        "account": "Imported",
                    })
                data["transactions"].extend(imported)
                save_banks(data)
                st.success(f"Imported {len(imported)} transactions")
                st.dataframe(pd.DataFrame(imported).head(20), width="stretch", hide_index=True)
            except Exception as e:
                st.error(f"CSV parse error: {e}")

    # ── Transactions ──
    with tab_txn:
        txns = data.get("transactions", [])
        if txns:
            tdf = pd.DataFrame(txns).sort_values("date", ascending=False)
            st.dataframe(tdf.head(100), width="stretch", hide_index=True)
            st.metric("Total transactions", len(txns))
            if st.button("Clear transactions", key="clr_txn"):
                data["transactions"] = []
                save_banks(data)
                st.rerun()
        else:
            st.info("No transactions. Connect a bank or import CSV.")