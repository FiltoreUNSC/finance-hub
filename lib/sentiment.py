"""Finance news sentiment analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass

import feedparser
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

BULLISH = {
    "surge", "soar", "rally", "gain", "gains", "jump", "jumps", "rise", "rises", "rising",
    "beat", "beats", "upgrade", "upgraded", "bullish", "record", "high", "profit", "profits",
    "growth", "boom", "strong", "outperform", "buy", "breakout", "recovery", "optimistic",
    "exceeds", "tops", "wins", "positive", "momentum", "upside",
}

BEARISH = {
    "fall", "falls", "drop", "drops", "plunge", "plunges", "decline", "declines", "sink",
    "miss", "misses", "downgrade", "downgraded", "bearish", "recession", "layoff", "layoffs",
    "crash", "warning", "weak", "underperform", "sell", "selloff", "fear", "loss", "losses",
    "cut", "cuts", "tumble", "slump", "negative", "downside", "bankruptcy", "default",
}


@dataclass
class SentimentResult:
    score: float       # -1 to 1
    label: str         # Bullish / Neutral / Bearish
    bullish_hits: int
    bearish_hits: int
    text: str


def analyze_text(text: str) -> SentimentResult:
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    bull = len(words & BULLISH)
    bear = len(words & BEARISH)
    total = bull + bear
    if total == 0:
        score, label = 0.0, "Neutral"
    else:
        score = (bull - bear) / total
        if score > 0.25:
            label = "Bullish"
        elif score < -0.25:
            label = "Bearish"
        else:
            label = "Neutral"
    return SentimentResult(score, label, bull, bear, text[:300])


def fetch_feed_headlines(url: str, limit: int = 20) -> list[dict]:
    feed = feedparser.parse(url)
    rows = []
    for entry in feed.entries[:limit]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        rows.append({
            "title": title,
            "summary": summary,
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "text": f"{title} {summary}",
        })
    return rows


def fetch_ticker_news(ticker: str, limit: int = 15) -> list[dict]:
    try:
        news = yf.Ticker(ticker).news or []
        rows = []
        for item in news[:limit]:
            title = item.get("title", "")
            pub = item.get("publisher", "")
            rows.append({
                "title": title,
                "summary": pub,
                "link": item.get("link", ""),
                "published": "",
                "text": title,
            })
        return rows
    except Exception:
        return []


def render_sentiment(watchlist: list[str]) -> None:
    st.subheader("News Sentiment")
    st.caption("Lexicon-based scoring — bullish vs bearish keywords in headlines")

    mode = st.radio("Source", ["Watchlist tickers", "News feed", "Single ticker"], horizontal=True, key="sent_mode")

    articles: list[dict] = []
    if mode == "Watchlist tickers":
        limit = st.slider("Articles per ticker", 3, 10, 5, key="sent_wl_lim")
        with st.spinner("Fetching watchlist news…"):
            for sym in watchlist[:8]:
                for a in fetch_ticker_news(sym, limit):
                    a["ticker"] = sym
                    articles.append(a)
    elif mode == "Single ticker":
        sym = st.text_input("Ticker", value=watchlist[0] if watchlist else "SPY", key="sent_sym").upper()
        limit = st.slider("Articles", 5, 25, 15, key="sent_single_lim")
        with st.spinner("Fetching…"):
            for a in fetch_ticker_news(sym, limit):
                a["ticker"] = sym
                articles.append(a)
    else:
        from lib.macro import NEWS_FEEDS
        source = st.selectbox("Feed", [n for n, _ in NEWS_FEEDS], key="sent_feed")
        limit = st.slider("Articles", 5, 30, 20, key="sent_feed_lim")
        url = dict(NEWS_FEEDS)[source]
        with st.spinner("Fetching feed…"):
            articles = fetch_feed_headlines(url, limit)

    if not articles:
        st.warning("No articles found.")
        return

    results = []
    for a in articles:
        s = analyze_text(a["text"])
        results.append({
            "Ticker": a.get("ticker", "—"),
            "Headline": a["title"][:80],
            "Sentiment": s.label,
            "Score": round(s.score, 2),
            "Bull words": s.bullish_hits,
            "Bear words": s.bearish_hits,
            "Link": a.get("link", ""),
        })

    df = pd.DataFrame(results)

    # Aggregate
    bull_n = (df["Sentiment"] == "Bullish").sum()
    bear_n = (df["Sentiment"] == "Bearish").sum()
    neut_n = (df["Sentiment"] == "Neutral").sum()
    avg_score = df["Score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg score", f"{avg_score:+.2f}", delta="Bullish" if avg_score > 0.15 else ("Bearish" if avg_score < -0.15 else "Neutral"))
    c2.metric("Bullish", bull_n)
    c3.metric("Bearish", bear_n)
    c4.metric("Neutral", neut_n)

    # Pie chart
    fig = go.Figure(go.Pie(
        labels=["Bullish", "Bearish", "Neutral"],
        values=[bull_n, bear_n, neut_n],
        marker_colors=["#7dd3a0", "#ff6b6b", "#666"],
        hole=0.4,
    ))
    fig.update_layout(template="plotly_dark", height=280, margin=dict(t=20, b=20), showlegend=True)
    st.plotly_chart(fig, width="stretch")

    # Per-ticker breakdown
    if "Ticker" in df.columns and df["Ticker"].nunique() > 1:
        st.subheader("By ticker")
        agg = df.groupby("Ticker").agg(avg_score=("Score", "mean"), articles=("Score", "count")).reset_index()
        agg["Sentiment"] = agg["avg_score"].apply(
            lambda x: "Bullish" if x > 0.25 else ("Bearish" if x < -0.25 else "Neutral")
        )
        st.dataframe(agg, width="stretch", hide_index=True)

    st.subheader("Articles")
    for _, row in df.iterrows():
        color = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "⚪"}[row["Sentiment"]]
        link = row["Link"]
        title = row["Headline"]
        if link:
            st.markdown(f"{color} **[{title}]({link})** — {row['Sentiment']} ({row['Score']:+.2f})")
        else:
            st.markdown(f"{color} **{title}** — {row['Sentiment']} ({row['Score']:+.2f})")
        if row["Ticker"] != "—":
            st.caption(f"{row['Ticker']}")