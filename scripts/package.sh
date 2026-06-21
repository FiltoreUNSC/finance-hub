#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="finance-hub-v1.0"
OUT="dist/${NAME}"

rm -rf dist
mkdir -p "$OUT"

rsync -a \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude 'dist' \
  --exclude 'portfolio.json' \
  --exclude 'paper_trading.json' \
  --exclude 'alerts.json' \
  . "$OUT/"

chmod +x "$OUT/install.sh" "$OUT/run.sh"

cd dist
zip -rq "${NAME}.zip" "$NAME"
echo "Created dist/${NAME}.zip ($(du -h "${NAME}.zip" | cut -f1))"