"""URL helpers for clickable links."""

from __future__ import annotations

YAHOO_QUOTE = "https://finance.yahoo.com/quote/{ticker}"
YAHOO_CHART = "https://finance.yahoo.com/chart/{ticker}"
PLAID_SIGNUP = "https://dashboard.plaid.com/signup"
GITHUB_REPO = "https://github.com/haydenjstump/finance-hub"
SUPPORT_EMAIL = "mailto:haydenjstump@gmail.com?subject=Finance%20Hub%20Support"


def yahoo_url(ticker: str) -> str:
    return YAHOO_QUOTE.format(ticker=ticker.replace("-", "%2D"))


def ticker_link_html(ticker: str, price: str, change_html: str) -> str:
    url = yahoo_url(ticker)
    return (
        f'<div class="watch-ticker">'
        f'<a href="{url}" target="_blank" rel="noopener" style="color:#7dd3a0;text-decoration:none;">'
        f'<b>{ticker}</b></a> {price} {change_html}</div>'
    )