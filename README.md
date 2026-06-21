# Finance Hub

Your personal Bloomberg terminal — runs locally on your Mac. No subscriptions, no API keys.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

| Module | What it does |
|--------|--------------|
| **Market Overview** | Live tape — SPY, QQQ, VIX, BTC, yields |
| **Research** | Stock screener (12 filters), watchlist filter, earnings calendar |
| **Deep Dive** | Fundamentals, analyst ratings, financials, holders |
| **Technicals** | Daily + intraday charts, RSI, MACD, Bollinger Bands |
| **Compare** | Multi-ticker overlay + correlation matrix |
| **Options** | P/L calculator, Black-Scholes Greeks, IV chain |
| **Crypto** | BTC/ETH/SOL charts, screener, compare |
| **Paper Trading** | $100k virtual portfolio with trade history |
| **Dividends** | Yield screener + payment history |
| **Backtest** | SMA crossover & RSI strategies |
| **Sectors** | Sector ETF performance heatmap |
| **Macro & News** | Fed calendar, indicators, news + sentiment |
| **Portfolio** | Track holdings, sector allocation, correlation |
| **Reports** | Export PDF reports |
| **Alerts** | Price alerts in sidebar |

## Quick Start

```bash
git clone https://github.com/haydenjstump/finance-hub.git
cd finance-hub
./install.sh
./run.sh
```

Or if you already have the folder:

```bash
./install.sh   # one time
./run.sh       # launch
```

Opens at **http://localhost:8501**

## Requirements

- macOS, Linux, or Windows
- Python 3.11 or newer
- Internet connection (live market data via Yahoo Finance)

## Manual Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Verify Install

```bash
.venv/bin/python scripts/smoke_test.py
```

## Data & Privacy

- All data fetched from **Yahoo Finance** (free, no API key)
- Portfolio, paper trades, and alerts saved **locally** on your machine
- Nothing is sent to external servers except market data requests
- **Not financial advice** — for research and education only

## File Structure

```
finance-hub/
├── app.py              # Main dashboard
├── install.sh          # One-command setup
├── run.sh              # One-command launch
├── lib/                # Feature modules
├── scripts/            # Smoke test + packaging
├── marketing/          # Landing page + sales copy
└── .streamlit/         # Dark theme config
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python3` | Install Python from python.org |
| Charts empty | Check internet; try a different ticker |
| `ModuleNotFoundError` | Run `./install.sh` again |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |

## License

MIT — use personally or modify freely. Not for redistribution as-is without permission.

## Support

haydenjstump@gmail.com