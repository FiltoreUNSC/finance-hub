"""Shared market data helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

DEFAULT_WATCHLIST = ["SPY", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "META", "GOOGL"]

SCREENER_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "XOM", "JPM", "WMT", "MA", "PG", "HD", "CVX", "MRK", "ABBV",
    "KO", "PEP", "COST", "AVGO", "LLY", "TMO", "MCD", "CSCO", "ACN", "ABT",
    "DHR", "NEE", "VZ", "ADBE", "NKE", "TXN", "PM", "CRM", "ORCL", "AMD",
    "INTC", "QCOM", "IBM", "GE", "CAT", "BA", "DIS", "NFLX", "PYPL", "SQ",
    "UBER", "ABNB", "COIN", "PLTR", "SOFI", "RIVN", "LCID", "F", "GM", "DAL",
    "UAL", "AAL", "CCL", "RCL", "XLE", "XLF", "XLK", "ARKK", "SPY", "QQQ",
    "IWM", "GLD", "SLV", "USO", "TLT", "HYG", "EEM", "VTI", "VOO", "DIA",
]


@st.cache_data(ttl=60, show_spinner=False)
def fetch_history(ticker: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    data = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data.dropna()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=60, show_spinner=False)
def fetch_quote(ticker: str) -> dict:
    info = fetch_info(ticker)
    hist = fetch_history(ticker, period="5d")
    price = float(hist["Close"].iloc[-1]) if not hist.empty else info.get("currentPrice") or info.get("regularMarketPrice")
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
    change = price - prev if price and prev else 0
    change_pct = (change / prev * 100) if prev else 0
    return {
        "ticker": ticker.upper(),
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "sector": info.get("sector", "—"),
        "pe": info.get("trailingPE") or info.get("forwardPE"),
        "market_cap": info.get("marketCap"),
        "volume": info.get("volume") or info.get("regularMarketVolume"),
    }


def screen_stocks(
    tickers: list[str],
    min_pe: float | None = None,
    max_pe: float | None = None,
    min_volume: int | None = None,
    sector: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_market_cap: int | None = None,
    max_market_cap: int | None = None,
    min_div_yield: float | None = None,
    max_beta: float | None = None,
    min_52w_change: float | None = None,
    max_52w_change: float | None = None,
) -> pd.DataFrame:
    rows = []
    for symbol in tickers:
        try:
            q = fetch_quote(symbol)
            info = fetch_info(symbol)
            pe = q["pe"]
            vol = q["volume"] or 0
            sec = q["sector"]
            price = q["price"] or 0
            mcap = q["market_cap"] or 0
            beta = info.get("beta")
            div_y = (info.get("dividendYield") or 0) * 100
            w52_high = info.get("fiftyTwoWeekHigh")
            w52_low = info.get("fiftyTwoWeekLow")
            w52_chg = None
            if w52_high and w52_low and price:
                mid = (w52_high + w52_low) / 2
                w52_chg = ((price - mid) / mid * 100) if mid else None

            if min_pe is not None and (pe is None or pe < min_pe):
                continue
            if max_pe is not None and (pe is None or pe > max_pe):
                continue
            if min_volume is not None and vol < min_volume:
                continue
            if sector and sector != "All" and sec != sector:
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            if min_market_cap is not None and mcap < min_market_cap:
                continue
            if max_market_cap is not None and mcap > max_market_cap:
                continue
            if min_div_yield is not None and div_y < min_div_yield:
                continue
            if max_beta is not None and (beta is None or beta > max_beta):
                continue
            if min_52w_change is not None and (w52_chg is None or w52_chg < min_52w_change):
                continue
            if max_52w_change is not None and (w52_chg is None or w52_chg > max_52w_change):
                continue

            rows.append({
                "Ticker": symbol,
                "Name": q["name"],
                "Price": round(price, 2) if price else None,
                "Change %": round(q["change_pct"], 2) if q["change_pct"] else None,
                "P/E": round(pe, 2) if pe else None,
                "Beta": round(beta, 2) if beta else None,
                "Div %": round(div_y, 2) if div_y else None,
                "52w Pos %": round(w52_chg, 1) if w52_chg is not None else None,
                "Volume": vol,
                "Sector": sec,
                "Market Cap": mcap,
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("Volume", ascending=False).reset_index(drop=True)