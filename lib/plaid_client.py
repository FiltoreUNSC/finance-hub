"""Plaid API wrapper (optional — requires keys in .streamlit/secrets.toml)."""

from __future__ import annotations

import os
from typing import Any


def get_plaid_credentials() -> tuple[str, str] | None:
    """Read Plaid keys from Streamlit secrets or environment."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "plaid" in st.secrets:
            cid = st.secrets["plaid"].get("client_id", "")
            sec = st.secrets["plaid"].get("secret", "")
            if cid and sec:
                return str(cid), str(sec)
    except Exception:
        pass
    cid = os.environ.get("PLAID_CLIENT_ID", "")
    sec = os.environ.get("PLAID_SECRET", "")
    if cid and sec:
        return cid, sec
    return None


def plaid_available() -> bool:
    return get_plaid_credentials() is not None


def _client():
    import plaid
    from plaid.api import plaid_api

    cid, sec = get_plaid_credentials()
    if not cid:
        raise RuntimeError("Plaid credentials not configured")

    env = os.environ.get("PLAID_ENV", "sandbox")
    host = plaid.Environment.Sandbox
    if env == "production":
        host = plaid.Environment.Production
    elif env == "development":
        host = plaid.Environment.Development

    config = plaid.Configuration(
        host=host,
        api_key={"clientId": cid, "secret": sec},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(config))


def create_sandbox_connection(institution_id: str = "ins_109508") -> dict[str, Any]:
    """Create a sandbox bank connection (First Platypus Bank). No UI required."""
    from plaid.model.products import Products
    from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

    client = _client()
    pt_req = SandboxPublicTokenCreateRequest(
        institution_id=institution_id,
        initial_products=[Products("transactions"), Products("auth")],
    )
    pt_resp = client.sandbox_public_token_create(pt_req)
    public_token = pt_resp["public_token"]

    ex_req = ItemPublicTokenExchangeRequest(public_token=public_token)
    ex_resp = client.item_public_token_exchange(ex_req)
    return {
        "access_token": ex_resp["access_token"],
        "item_id": ex_resp["item_id"],
        "institution_id": institution_id,
    }


def fetch_accounts(access_token: str) -> list[dict]:
    from plaid.model.accounts_get_request import AccountsGetRequest

    client = _client()
    resp = client.accounts_get(AccountsGetRequest(access_token=access_token))
    accounts = []
    for acct in resp["accounts"]:
        bal = acct["balances"]
        accounts.append({
            "account_id": acct["account_id"],
            "name": acct["name"],
            "official_name": acct.get("official_name") or acct["name"],
            "type": str(acct["type"]),
            "subtype": str(acct.get("subtype", "")),
            "balance": bal.get("current") or 0,
            "available": bal.get("available"),
            "currency": bal.get("iso_currency_code") or "USD",
        })
    return accounts


def fetch_transactions(access_token: str, days: int = 30) -> list[dict]:
    from datetime import date, timedelta

    from plaid.model.transactions_get_request import TransactionsGetRequest

    client = _client()
    end = date.today()
    start = end - timedelta(days=days)
    resp = client.transactions_get(TransactionsGetRequest(
        access_token=access_token,
        start_date=start,
        end_date=end,
    ))
    txns = []
    for t in resp["transactions"]:
        txns.append({
            "date": str(t["date"]),
            "name": t["name"],
            "amount": t["amount"],
            "category": ", ".join(t.get("category") or []) or "—",
            "pending": t.get("pending", False),
        })
    return txns


def create_link_token() -> str:
    from plaid.model.country_code import CountryCode
    from plaid.model.link_token_create_request import LinkTokenCreateRequest
    from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
    from plaid.model.products import Products

    cid, _ = get_plaid_credentials()
    client = _client()
    req = LinkTokenCreateRequest(
        client_name="Finance Hub",
        language="en",
        country_codes=[CountryCode("US")],
        user=LinkTokenCreateRequestUser(client_user_id="finance-hub-user"),
        products=[Products("transactions"), Products("auth")],
    )
    resp = client.link_token_create(req)
    return resp["link_token"]


def exchange_public_token(public_token: str) -> dict[str, Any]:
    from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

    client = _client()
    resp = client.item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=public_token)
    )
    return {"access_token": resp["access_token"], "item_id": resp["item_id"]}