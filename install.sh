#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Finance Hub Installer ==="

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found. Install Python 3.11+ first."
  exit 1
fi

PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python $PYVER detected"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

echo "Installing dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo "Running smoke test..."
.venv/bin/python scripts/smoke_test.py

echo ""
echo "=== Install complete ==="
echo "Start Finance Hub:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  .venv/bin/streamlit run app.py"