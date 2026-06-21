#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Virtual env not found. Run ./install.sh first."
  exit 1
fi

PORT=8501

if lsof -ti :"$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is already in use."
  echo ""
  echo "  Finance Hub may already be running → http://localhost:$PORT"
  echo ""
  echo "  To stop it:  kill \$(lsof -t -i :$PORT)"
  echo "  Other port:  .venv/bin/streamlit run app.py --server.port 8502"
  exit 1
fi

echo "Starting Finance Hub at http://localhost:$PORT"
echo "Press Ctrl+C to stop"
.venv/bin/streamlit run app.py --server.port "$PORT"