#!/usr/bin/env python3
"""Full Finance Hub diagnostics — run before release."""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0
WARN = 0


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✓ {msg}")


def fail(msg: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"  ✗ {msg}" + (f" — {detail}" if detail else ""))


def warn(msg: str, detail: str = "") -> None:
    global WARN
    WARN += 1
    print(f"  ! {msg}" + (f" — {detail}" if detail else ""))


def check_imports() -> None:
    print("\n[1] Module imports")
    modules = [
        "lib.data", "lib.technicals", "lib.options_calc", "lib.greeks",
        "lib.links", "lib.sentiment",
        "lib.reports", "lib.paper_trading", "lib.portfolio", "lib.alerts",
        "lib.crypto", "lib.backtest", "lib.compare", "lib.deep_dive",
        "lib.dividends", "lib.heatmap", "lib.macro", "lib.market_overview",
        "lib.screener",
    ]
    for mod in modules:
        try:
            importlib.import_module(mod)
            ok(mod)
        except Exception as e:
            fail(mod, str(e))


def check_smoke() -> None:
    print("\n[2] Smoke tests")
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "smoke_test.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        if r.returncode == 0:
            ok("smoke_test.py passed")
        else:
            fail("smoke_test.py", r.stderr[-200:] if r.stderr else r.stdout[-200:])
    except Exception as e:
        fail("smoke_test.py", str(e))


def check_files() -> None:
    print("\n[3] Required files")
    required = [
        "app.py", "install.sh", "run.sh", "requirements.txt", "README.md",
        "LICENSE", "docs/index.html", "marketing/index.html",
        ".github/workflows/ci.yml", ".streamlit/config.toml",
    ]
    for f in required:
        if (ROOT / f).exists():
            ok(f)
        else:
            fail(f, "missing")


def check_scripts_executable() -> None:
    print("\n[4] Script permissions")
    for f in ["install.sh", "run.sh", "scripts/smoke_test.py", "scripts/diagnostics.py", "scripts/package.sh"]:
        p = ROOT / f
        if p.exists() and p.stat().st_mode & 0o111:
            ok(f"{f} executable")
        elif p.exists():
            warn(f"{f} not executable")
        else:
            fail(f, "missing")


def extract_urls(path: Path) -> list[str]:
    text = path.read_text(errors="ignore")
    urls = re.findall(r'href=["\']([^"\']+)["\']', text)
    urls += re.findall(r'https?://[^\s\)\]"\'<>\*]+', text)
    clean = []
    for u in urls:
        u = u.rstrip(".,)*")
        if u.startswith(("http://", "https://", "mailto:")):
            clean.append(u)
    return list(dict.fromkeys(clean))


def check_links() -> None:
    print("\n[5] Link validation")
    try:
        import requests
    except ImportError:
        warn("requests not installed — skipping HTTP link checks")
        return

    files = list((ROOT / "docs").glob("*.html")) + list((ROOT / "marketing").glob("*.html"))
    files.append(ROOT / "README.md")

    checked = set()
    for fp in files:
        for url in extract_urls(fp):
            if url in checked or url.startswith("mailto:"):
                if url.startswith("mailto:"):
                    ok(f"mailto link in {fp.name}")
                continue
            checked.add(url)
            if "YOUR_USERNAME" in url or "example.com" in url:
                warn(f"placeholder URL: {url}")
                continue
            parsed = urlparse(url)
            if parsed.hostname in ("localhost", "127.0.0.1"):
                ok(f"{url[:60]} (local dev URL — skipped)")
                continue
            try:
                r = requests.head(url, timeout=10, allow_redirects=True,
                                  headers={"User-Agent": "FinanceHub-Diagnostics/1.0"})
                if r.status_code < 400:
                    ok(f"{url[:60]} → {r.status_code}")
                elif r.status_code == 404 and "github.com/Haydenjstump" in url:
                    warn(f"{url[:60]} → 404 (push repo to GitHub)")
                else:
                    r2 = requests.get(url, timeout=10, allow_redirects=True,
                                       headers={"User-Agent": "FinanceHub-Diagnostics/1.0"}, stream=True)
                    if r2.status_code < 400:
                        ok(f"{url[:60]} → {r2.status_code} (GET)")
                    elif r2.status_code == 404 and "github.com/Haydenjstump" in url:
                        warn(f"{url[:60]} → 404 (push repo to GitHub)")
                    else:
                        fail(f"{url[:60]}", f"HTTP {r2.status_code}")
            except Exception as e:
                if "github.com/Haydenjstump" in url:
                    warn(url[:60], "repo not on GitHub yet")
                else:
                    fail(url[:60], str(e)[:80])


def check_feeds() -> None:
    print("\n[6] News RSS feeds")
    from lib.feeds import NEWS_FEEDS, fetch_feed
    working = 0
    for name, url in NEWS_FEEDS:
        feed = fetch_feed(url)
        if feed.entries:
            ok(f"{name} ({len(feed.entries)} articles)")
            working += 1
        else:
            warn(name, "no entries (may be network)")
    if working == 0:
        fail("news feeds", "none reachable")
    elif working < 2:
        warn("news feeds", f"only {working}/{len(NEWS_FEEDS)} reachable")


def check_ticker_links() -> None:
    print("\n[7] Ticker link helpers")
    from lib.links import yahoo_url, ticker_link_html
    url = yahoo_url("AAPL")
    assert "finance.yahoo.com" in url
    html = ticker_link_html("AAPL", "$200", "<span>+1%</span>")
    assert "href=" in html and 'target="_blank"' in html
    ok("Yahoo Finance ticker links")


def main() -> int:
    print("=" * 50)
    print("Finance Hub Diagnostics")
    print("=" * 50)

    check_imports()
    check_files()
    check_scripts_executable()
    check_smoke()
    check_ticker_links()
    check_feeds()
    check_links()

    print("\n" + "=" * 50)
    print(f"Results: {PASS} passed, {WARN} warnings, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        print("\nFAILED — fix errors before release.")
        return 1
    if WARN > 0:
        print("\nPASSED with warnings.")
    else:
        print("\nALL DIAGNOSTICS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())