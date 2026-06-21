# Finance Hub — Claude Review Packet

## What this is

Personal finance dashboard (Streamlit + Python). Stocks, options, crypto, paper trading, sentiment, PDF reports.

## How to run

```bash
./install.sh
./run.sh
# → http://localhost:8501
```

## Diagnostics

```bash
.venv/bin/python scripts/diagnostics.py
```

## File map

```
app.py                 # Main Streamlit app (entry point)
install.sh / run.sh    # Setup & launch
requirements.txt       # Dependencies

lib/
  data.py              # Yahoo Finance data
  technicals.py        # Charts, RSI, MACD
  options_calc.py      # Options P/L + Greeks
  greeks.py            # Black-Scholes
  paper_trading.py     # $100k virtual portfolio
  portfolio.py         # Real holdings tracker
  sentiment.py         # News sentiment
  reports.py           # PDF export
  screener.py          # Stock screener
  macro.py             # Fed calendar + news
  crypto.py            # Crypto dashboard
  backtest.py          # Strategy backtester
  compare.py           # Multi-ticker compare
  deep_dive.py         # Fundamentals
  dividends.py         # Dividend tracker
  heatmap.py           # Sector performance
  market_overview.py   # Market tape
  alerts.py            # Price alerts
  feeds.py             # RSS news feeds
  links.py             # URL helpers

scripts/
  diagnostics.py       # Full test suite
  smoke_test.py        # Quick smoke test
  package.sh           # Build release zip
  github_push.sh       # Deploy to GitHub

docs/index.html        # GitHub Pages landing page
marketing/             # Gumroad copy, launch checklist
.github/workflows/ci.yml

.streamlit/config.toml
```

## GitHub

- Repo: https://github.com/Haydenjstump/finance-hub
- Pages: https://haydenjstump.github.io/finance-hub/

## Review focus areas

1. Security (local JSON storage for portfolio/paper trades)
2. Code quality / bugs in lib/
3. Marketing copy accuracy
4. Missing tests or edge cases
5. UX improvements for Streamlit app