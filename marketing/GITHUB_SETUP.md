# Deploy to GitHub

Repo is committed locally. One login, one script.

## Step 1: Log into GitHub

```bash
gh auth login
```

Choose:
- GitHub.com
- HTTPS (easiest) or SSH
- Login via browser

## Step 2: Push

```bash
cd ~/finance-hub
./scripts/github_push.sh
```

Creates `github.com/YOUR_USERNAME/finance-hub` and pushes `main`.

## Step 3: Enable GitHub Pages (free sales page)

1. Open your repo on GitHub
2. **Settings** → **Pages**
3. **Source:** Deploy from a branch
4. **Branch:** `main` → folder **`/docs`**
5. **Save**

Live at: `https://YOUR_USERNAME.github.io/finance-hub/`

## Step 4: Verify CI

- Go to **Actions** tab — smoke test should pass on push
- Add badge to README (optional) — auto-works after first CI run

## Manual alternative (no gh CLI)

1. Create empty repo at [github.com/new](https://github.com/new) named `finance-hub`
2. Then:

```bash
cd ~/finance-hub
git remote add origin https://github.com/YOUR_USERNAME/finance-hub.git
git push -u origin main
```

## What's on GitHub vs Gumroad

| GitHub (public) | Gumroad (paid zip) |
|-----------------|-------------------|
| Full source code | Same source + install scripts |
| README + docs | Packaged `finance-hub-v1.0.zip` |
| Free clone | $29 convenience + support |

MIT license allows public repo while selling the packaged version.