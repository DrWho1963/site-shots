#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
from datetime import datetime
import os, json, sys, re, time

# One URL from env (matrix), or urls.json fallback
urls_env = os.getenv("SHOT_URLS")
if urls_env:
    URLS = [u.strip() for u in urls_env.split(",") if u.strip()]
else:
    with open("urls.json") as f:
        URLS = json.load(f)

OUT_DIR = "shots"
os.makedirs(OUT_DIR, exist_ok=True)
ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S-UTC")

_SANITIZE = re.compile(r"[^A-Za-z0-9._-]+")
def safe(u: str) -> str:
    u = re.sub(r"^https?://", "", u, flags=re.I).strip().strip("/")
    return _SANITIZE.sub("_", u)[:180] or "page"

def shoot(page, url, name):
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    try:
        page.wait_for_load_state("networkidle", timeout=5_000)
    except Exception:
        pass
    # Trigger lazy loads
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(0.6)
    page.evaluate("window.scrollTo(0, 0)")
    path = os.path.join(OUT_DIR, f"{name}__{ts}.jpg")
    page.screenshot(path=path, type="jpeg", quality=75, full_page=False)
    print("Saved", path)
    return path

made_any = False

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=1,
        user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    )
    page = context.new_page()

    for u in URLS:
        try:
            shoot(page, u, safe(u))
            made_any = True
        except Exception as e:
            print(f"ERROR for {u}: {e!r}", file=sys.stderr)

    try:
        context.close()
    finally:
        browser.close()

if not made_any:
    print("No screenshots created.", file=sys.stderr)
    # exit 0 here so the email step can SKIP cleanly instead of failing the job
    # sys.exit(1)

