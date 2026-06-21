"""Macro calendar and finance news."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from lib.feeds import NEWS_FEEDS, fetch_feed
from lib.sentiment import render_sentiment

FOMC_2026 = [
    ("Jan 28–29", date(2026, 1, 28)),
    ("Mar 18–19", date(2026, 3, 18)),
    ("May 6–7", date(2026, 5, 6)),
    ("Jun 17–18", date(2026, 6, 17)),
    ("Jul 29–30", date(2026, 7, 29)),
    ("Sep 16–17", date(2026, 9, 16)),
    ("Nov 4–5", date(2026, 11, 4)),
    ("Dec 16–17", date(2026, 12, 16)),
]

def _render_indicators_and_fed() -> None:
    from lib.data import fetch_quote

    today = date.today()

    st.subheader("Market indicators")
    ind_cols = st.columns(5)
    for col, (label, sym) in zip(ind_cols, [
        ("VIX", "^VIX"), ("10Y Yield", "^TNX"), ("DXY", "DX-Y.NYB"),
        ("Crude", "CL=F"), ("USD/JPY", "JPY=X"),
    ]):
        try:
            q = fetch_quote(sym)
            col.metric(label, f"{q['price']:.2f}", delta=f"{q['change_pct']:+.2f}%")
        except Exception:
            col.metric(label, "—")

    st.divider()
    st.subheader("Fed / FOMC Calendar 2026")
    rows = []
    for label, d in FOMC_2026:
        days_away = (d - today).days
        if days_away < 0:
            status = "Past"
        elif days_away == 0:
            status = "Today"
        else:
            status = f"In {days_away}d"
        rows.append({"Meeting": label, "Start date": d.isoformat(), "Countdown": status})

    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    upcoming = [r for r in rows if r["Countdown"] != "Past"]
    if upcoming:
        nxt = upcoming[0]
        st.info(f"Next FOMC: **{nxt['Meeting']}** ({nxt['Start date']}) — {nxt['Countdown']}")


def _render_news() -> None:
    st.subheader("Finance News")
    source = st.selectbox("Source", [name for name, _ in NEWS_FEEDS], key="news_source")
    limit = st.slider("Articles", 5, 25, 12, key="news_limit")

    url = dict(NEWS_FEEDS)[source]
    with st.spinner("Fetching headlines…"):
        feed = fetch_feed(url)

    if not feed.entries:
        st.warning("Could not load feed. Try another source.")
        return

    for entry in feed.entries[:limit]:
        title = entry.get("title", "No title")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", ""))
        summary = entry.get("summary", "")
        if len(summary) > 200:
            summary = summary[:200] + "…"

        col_t, col_l = st.columns([5, 1])
        with col_t:
            if link:
                st.markdown(f"**[{title}]({link})**")
            else:
                st.markdown(f"**{title}**")
            if published:
                st.caption(published)
            if summary:
                st.write(summary)
        with col_l:
            if link:
                st.link_button("Open →", link, use_container_width=True)
        st.divider()


def render_macro(watchlist: list[str] | None = None) -> None:
    watchlist = watchlist or ["SPY"]
    tab_macro, tab_news, tab_sent = st.tabs(["Macro & Fed", "News", "Sentiment"])

    with tab_macro:
        _render_indicators_and_fed()
    with tab_news:
        _render_news()
    with tab_sent:
        render_sentiment(watchlist)