"""News feed fetching with reliable sources."""

from __future__ import annotations

import feedparser
import requests

USER_AGENT = "Mozilla/5.0 (compatible; FinanceHub/1.0; +https://github.com/FiltoreUNSC/finance-hub)"

NEWS_FEEDS = [
    ("Google News — Markets", "https://news.google.com/rss/search?q=stock+market&hl=en-US&gl=US&ceid=US:en"),
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("CNBC Top News", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
]


def fetch_feed(url: str, timeout: int = 15) -> feedparser.FeedParserDict:
    """Fetch and parse RSS with browser User-Agent."""
    feedparser.USER_AGENT = USER_AGENT
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception:
        return feedparser.parse(url)