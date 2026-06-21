# Launch Checklist

## Phase 1: Verify (15 min)

- [ ] Run `./install.sh` — all smoke tests pass
- [ ] Run `./run.sh` — app loads at localhost:8501
- [ ] Click every tab — no errors
- [ ] Paper Trade — buy 1 stock, confirm it saves
- [ ] Reports — generate + download PDF
- [ ] Restart app — portfolio/paper trades persist

## Phase 2: Screenshots (30 min)

See `SCREENSHOTS.md` — take 5 required shots.

## Phase 3: Gumroad (20 min)

1. Create account at [gumroad.com](https://gumroad.com)
2. New Product → Digital Product
3. Upload `dist/finance-hub-v1.0.zip`
4. Paste copy from `GUMROAD.md`
5. Set price: **$29**
6. Add screenshots from Phase 2
7. Publish → copy product URL

## Phase 4: GitHub (10 min)

- [ ] Repo live at `github.com/haydenjstump/finance-hub`
- [ ] Enable **GitHub Pages** → Settings → Pages → Source: `main` branch → `/docs`
- [ ] Sales page live at `https://haydenjstump.github.io/finance-hub/`
- [ ] CI badge green (Actions tab)

## Phase 5: Landing page (5 min)

1. Update `docs/index.html` — replace mailto with Gumroad URL
2. `git push` — Pages auto-updates

## Phase 6: Promote

- [ ] Post on X/LinkedIn with screenshot + Gumroad link
- [ ] Reddit: r/algotrading, r/stocks, r/Python (follow sub rules)
- [ ] Tell friends who trade

## Your files

| File | Purpose |
|------|---------|
| `dist/finance-hub-v1.0.zip` | What buyers download |
| `marketing/GUMROAD.md` | Listing copy |
| `marketing/index.html` | Sales page |
| `marketing/SCREENSHOTS.md` | What to photograph |
| `README.md` | Buyer documentation |