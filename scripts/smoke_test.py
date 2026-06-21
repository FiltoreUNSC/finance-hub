#!/usr/bin/env python3
"""Smoke test all Finance Hub modules."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def ok(name: str) -> None:
    print(f"  OK  {name}")


def fail(name: str, err: Exception) -> None:
    print(f"  FAIL {name}: {err}")
    raise err


def main() -> None:
    print("Finance Hub smoke test\n")

    from lib.data import fetch_quote, fetch_history, screen_stocks, DEFAULT_WATCHLIST
    q = fetch_quote("AAPL")
    assert q["price"] > 0
    ok("fetch_quote")

    hist = fetch_history("SPY", period="1mo")
    assert len(hist) > 5
    ok("fetch_history")

    df = screen_stocks(["AAPL", "MSFT"], max_pe=50)
    assert len(df) >= 1
    ok("screen_stocks")

    from lib.greeks import black_scholes
    g = black_scholes(100, 100, 30 / 365, 0.045, 0.3, "call")
    assert 0 < g.delta < 1
    ok("greeks")

    from lib.technicals import compute_rsi, compute_macd
    rsi = compute_rsi(hist["Close"])
    assert len(rsi) == len(hist)
    ok("technicals")

    from lib.backtest import run_sma_crossover
    bt = run_sma_crossover(hist, 5, 20)
    assert "equity_strategy" in bt.columns
    ok("backtest")

    from lib.sentiment import analyze_text
    s = analyze_text("Stocks rally on strong earnings beat")
    assert s.label == "Bullish"
    ok("sentiment")

    from lib.paper_trading import load_paper, buy, account_value
    acct = load_paper()
    assert "cash" in acct
    ok("paper_trading load")

    from lib.reports import build_pdf_report
    pdf = build_pdf_report(DEFAULT_WATCHLIST[:3], "market")
    assert len(pdf) > 500
    ok("pdf_report")

    from lib.portfolio import load_portfolio
    load_portfolio()
    ok("portfolio")

    from lib.alerts import load_alerts
    load_alerts()
    ok("alerts")

    intra = fetch_history("SPY", period="5d", interval="5m")
    assert len(intra) > 10
    ok("intraday data")

    from lib.links import yahoo_url
    assert "yahoo.com" in yahoo_url("AAPL")
    ok("ticker links")

    print("\nAll tests passed.")


if __name__ == "__main__":
    main()