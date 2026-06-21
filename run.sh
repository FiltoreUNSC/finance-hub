#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Virtual env not found. Run ./install.sh first."
  exit 1
fi

echo "Starting Finance Hub at http://localhost:8501"
echo "Press Ctrl+C to stop"
.venv/bin/streamlit run app.py --server.port 8501