"""Home dashboard — at-a-glance summary for consumers."""

from __future__ import annotations

import streamlit as st

from lib.alerts import load_alerts
from lib.data import fetch_quote
from lib.feeds import NEWS_FEEDS, fetch_feed
from lib.links import GITHUB_REPO, yahoo_url
from lib.paper_trading import account_value, load_paper
from lib.portfolio import load_portfolio
from lib.ui import section_header


def _portfolio_summary() -> tuple[float, float, int]:
    positions = load_portfolio()
    if not positions:
        return 0.0, 0.0, 0
    total_cost = 0.0
    total_value = 0.0
    for pos in positions:
        sh = pos["shares"]
        cb = pos["cost"]
        total_cost += sh * cb
        try:
            price = fetch_quote(pos["ticker"])["price"] or cb
        except Exception:
            price = cb
        total_value += sh * price
    pnl = total_value - total_cost
    return total_value, pnl, len(positions)


def render_dashboard(watchlist: list[str]) -> None:
    section_header(
        "Dashboard",
        "Your at-a-glance hub — watchlist movers, accounts, headlines",
    )

    st.info(
        "**Free & open source** — no subscription, no paywall. "
        f"[View on GitHub]({GITHUB_REPO})"
    )

    # Accounts
    section_header("Your accounts", None)
    c1, c2, c3 = st.columns(3)

    port_val, port_pnl, port_n = _portfolio_summary()
    with c1:
        if port_n:
            st.metric("Portfolio", f"${port_val:,.0f}", delta=f"${port_pnl:+,.0f}")
            st.caption(f"{port_n} position{'s' if port_n != 1 else ''}")
        else:
            st.metric("Portfolio", "—")
            st.caption("Add holdings in Portfolio tab")

    paper = load_paper()
    total, _, pos_rows = account_value(paper)
    paper_pnl = total - paper["starting_cash"]
    with c2:
        st.metric("Paper trading", f"${total:,.0f}", delta=f"${paper_pnl:+,.0f}")
        st.caption(f"{len(pos_rows)} open position{'s' if len(pos_rows) != 1 else ''}")

    alerts = load_alerts()
    with c3:
        st.metric("Price alerts", str(len(alerts)))
        st.caption("Manage in sidebar")

    st.divider()

    # Watchlist movers
    section_header("Watchlist movers", None)
    if not watchlist:
        st.caption("Add tickers in the sidebar watchlist.")
    else:
        rows = []
        for sym in watchlist[:15]:
            try:
                q = fetch_quote(sym)
                rows.append({
                    "Ticker": sym,
                    "Price": q["price"],
                    "Change %": q["change_pct"] or 0,
                    "Sector": q.get("sector", "—"),
                })
            except Exception:
                continue

        if rows:
            import pandas as pd

            df = pd.DataFrame(rows).sort_values("Change %", ascending=False)
            top, bottom = st.columns(2)
            with top:
                st.markdown("**Top gainers**")
                st.dataframe(
                    df.head(5)[["Ticker", "Price", "Change %"]],
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="$%.2f"),
                        "Change %": st.column_config.NumberColumn(format="%.2f%%"),
                    },
                )
            with bottom:
                st.markdown("**Top losers**")
                st.dataframe(
                    df.tail(5).iloc[::-1][["Ticker", "Price", "Change %"]],
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Price": st.column_config.NumberColumn(format="$%.2f"),
                        "Change %": st.column_config.NumberColumn(format="%.2f%%"),
                    },
                )

            links = " · ".join(
                f'[{r["Ticker"]}]({yahoo_url(r["Ticker"])})' for r in rows[:8]
            )
            st.caption(f"Quick links: {links}")
        else:
            st.warning("Could not load watchlist quotes. Check your connection.")

    st.divider()

    # News
    section_header("Latest headlines", None)
    headlines: list[tuple[str, str, str]] = []
    for name, url in NEWS_FEEDS[:3]:
        feed = fetch_feed(url)
        for entry in feed.entries[:3]:
            headlines.append((name, entry.get("title", "—"), entry.get("link", "")))
        if len(headlines) >= 8:
            break

    if headlines:
        for source, title, link in headlines[:8]:
            if link:
                st.markdown(f"- **{source}** — [{title}]({link})")
            else:
                st.markdown(f"- **{source}** — {title}")
    else:
        st.caption("News feeds unavailable right now.")

    st.divider()

    # Quick start
    section_header("Quick start", None)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.markdown("**Research**")
        st.caption("Screen stocks or filter your watchlist")
    with q2:
        st.markdown("**Technicals**")
        st.caption("Charts + RSI, MACD, Bollinger")
    with q3:
        st.markdown("**Paper Trade**")
        st.caption("$100k virtual portfolio")
    with q4:
        st.markdown("**Options**")
        st.caption("Greeks + P/L calculator")