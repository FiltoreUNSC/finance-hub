"""Research tab: screener + earnings + watchlist filters."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import yfinance as yf

from lib.data import SCREENER_UNIVERSE, screen_stocks
from lib.ui import section_header


def _screener_filters(key_prefix: str) -> dict:
    st.markdown("**Filters**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sector = st.selectbox(
            "Sector",
            ["All", "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
             "Consumer Defensive", "Energy", "Industrials", "Communication Services",
             "Utilities", "Real Estate", "Basic Materials"],
            key=f"{key_prefix}_sector",
        )
        min_price = st.number_input("Min price ($)", min_value=0.0, value=0.0, step=1.0, key=f"{key_prefix}_min_p")
    with c2:
        min_pe = st.number_input("Min P/E", min_value=0.0, value=0.0, step=1.0, key=f"{key_prefix}_min_pe")
        max_price = st.number_input("Max price ($)", min_value=0.0, value=0.0, step=10.0, key=f"{key_prefix}_max_p")
    with c3:
        max_pe = st.number_input("Max P/E", min_value=0.0, value=80.0, step=1.0, key=f"{key_prefix}_max_pe")
        min_mcap = st.number_input("Min mcap ($B)", min_value=0.0, value=0.0, step=1.0, key=f"{key_prefix}_min_mc")
    with c4:
        min_vol = st.number_input("Min volume", min_value=0, value=500_000, step=100_000, key=f"{key_prefix}_min_vol")
        max_beta = st.number_input("Max beta", min_value=0.0, value=0.0, step=0.1, key=f"{key_prefix}_max_beta")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        min_div = st.number_input("Min div yield %", min_value=0.0, value=0.0, step=0.5, key=f"{key_prefix}_min_div")
    with c6:
        min_52w = st.number_input("Min 52w pos %", value=0.0, step=5.0, key=f"{key_prefix}_min_52")
    with c7:
        max_52w = st.number_input("Max 52w pos %", value=0.0, step=5.0, key=f"{key_prefix}_max_52")
    with c8:
        max_mcap = st.number_input("Max mcap ($B)", min_value=0.0, value=0.0, step=10.0, key=f"{key_prefix}_max_mc")

    return {
        "sector": sector,
        "min_pe": min_pe if min_pe > 0 else None,
        "max_pe": max_pe if max_pe > 0 else None,
        "min_volume": min_vol if min_vol > 0 else None,
        "min_price": min_price if min_price > 0 else None,
        "max_price": max_price if max_price > 0 else None,
        "min_market_cap": int(min_mcap * 1e9) if min_mcap > 0 else None,
        "max_market_cap": int(max_mcap * 1e9) if max_mcap > 0 else None,
        "min_div_yield": min_div if min_div > 0 else None,
        "max_beta": max_beta if max_beta > 0 else None,
        "min_52w_change": min_52w if min_52w != 0 else None,
        "max_52w_change": max_52w if max_52w != 0 else None,
    }


def _show_results(df: pd.DataFrame, source_label: str) -> None:
    if df.empty:
        st.warning("No stocks matched. Loosen your filters.")
        return
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Market Cap": st.column_config.NumberColumn(format="$%d"),
            "Volume": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.caption(f"{len(df)} matches · {source_label}")
    st.download_button(
        "Download CSV",
        df.to_csv(index=False),
        file_name="screener_results.csv",
        mime="text/csv",
        key=f"dl_{source_label}",
    )


def _parse_ticker_list(raw: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for part in raw.replace("\n", ",").split(","):
        sym = part.strip().upper()
        if sym and sym not in seen:
            seen.add(sym)
            out.append(sym)
    return out


def render_research(watchlist: list[str]) -> None:
    sub1, sub2, sub3, sub4 = st.tabs([
        "Full Screener", "Custom Universe", "Watchlist Filter", "Earnings",
    ])

    with sub1:
        section_header("Stock Screener", "~80 large caps & ETFs")
        filters = _screener_filters("full")
        if st.button("Run screener", type="primary", key="run_screener"):
            with st.spinner("Scanning tickers…"):
                df = screen_stocks(SCREENER_UNIVERSE, **filters)
            _show_results(df, f"{len(SCREENER_UNIVERSE)} universe")

    with sub2:
        section_header("Custom Universe", "Screen any tickers you type — one per line or comma-separated")
        custom_raw = st.text_area(
            "Your tickers",
            value="SOFI, PLTR, AMD, COIN, HOOD",
            height=100,
            key="custom_universe",
            placeholder="AAPL, TSLA, SOFI…",
        )
        extra = _parse_ticker_list(custom_raw)
        merge = st.checkbox("Include built-in ~80 universe", value=False, key="merge_universe")
        universe = list(dict.fromkeys((SCREENER_UNIVERSE if merge else []) + extra))
        st.caption(f"{len(universe)} tickers ready")
        filters = _screener_filters("custom")
        if st.button("Run custom screener", type="primary", key="run_custom_screener"):
            if not universe:
                st.error("Add at least one ticker.")
            else:
                with st.spinner("Scanning…"):
                    df = screen_stocks(universe, **filters)
                _show_results(df, f"{len(universe)} custom")

    with sub3:
        st.subheader("Filter your watchlist")
        st.caption("Apply screener filters to tickers you already track")
        filters = _screener_filters("wl")
        if st.button("Filter watchlist", type="primary", key="run_wl_screener"):
            with st.spinner("Filtering…"):
                df = screen_stocks(watchlist, **filters)
            _show_results(df, "watchlist")

    with sub4:
        st.subheader("Earnings Calendar")
        earnings_rows = []
        for symbol in watchlist:
            try:
                t = yf.Ticker(symbol)
                cal = t.calendar
                if cal is None:
                    continue
                if isinstance(cal, dict):
                    raw = cal.get("Earnings Date") or cal.get("earningsDate")
                    if raw:
                        dates = raw if isinstance(raw, list) else [raw]
                        for d in dates:
                            earnings_rows.append({"Ticker": symbol, "Earnings Date": str(d)[:10]})
                elif hasattr(cal, "empty") and not cal.empty:
                    for idx in cal.index:
                        val = cal.loc[idx]
                        if "Earnings" in str(idx) or "earnings" in str(idx).lower():
                            earnings_rows.append({"Ticker": symbol, "Earnings Date": str(val)[:10]})
            except Exception:
                continue

        if earnings_rows:
            edf = pd.DataFrame(earnings_rows).drop_duplicates().sort_values("Earnings Date")
            st.dataframe(edf, width="stretch", hide_index=True)
        else:
            st.info("No upcoming earnings found for watchlist.")