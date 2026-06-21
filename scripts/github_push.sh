#!/usr/bin/env bash
# Create GitHub repo and push. Run after: gh auth login
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_NAME="${1:-finance-hub}"
VISIBILITY="${2:-public}"

if ! gh auth status &>/dev/null; then
  echo "Not logged into GitHub. Run this first:"
  echo "  gh auth login"
  echo ""
  echo "Then run this script again:"
  echo "  ./scripts/github_push.sh"
  exit 1
fi

USER=$(gh api user -q .login)
echo "GitHub user: $USER"

if git remote get-url origin &>/dev/null; then
  echo "Remote already set. Pushing..."
  git push -u origin main
else
  echo "Creating github.com/$USER/$REPO_NAME ($VISIBILITY)..."
  gh repo create "$REPO_NAME" \
    --"$VISIBILITY" \
    --source=. \
    --remote=origin \
    --description "Personal Bloomberg terminal — stocks, options, crypto, paper trading" \
    --push
fi

echo ""
echo "=== Done ==="
echo "Repo:    https://github.com/$USER/$REPO_NAME"
echo "Pages:   https://$USER.github.io/$REPO_NAME/"
echo ""
echo "Enable GitHub Pages:"
echo "  1. Go to repo → Settings → Pages"
echo "  2. Source: Deploy from branch"
echo "  3. Branch: main  /  Folder: /docs"
echo "  4. Save — site live in ~2 min"