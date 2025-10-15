#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
from datetime import datetime
import os, json

urls_env = os.getenv("SHOT_URLS")
if urls_env:
    URLS = [u.strip() for u in urls_env.split(",") if u.strip()]
else:
    with open("urls.json") as f:
        URLS = json.load(f)

OUT_DIR = "shots"
os.makedirs(OUT_DIR, exist_ok=True)
ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S-UTC")

def safe(u):
    return u.replace("https://","").replace("http://","").replace("/","_")

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width":1440, "height":900})
    page = context.new_page()
    for u in URLS:
        try:
            page.goto(u, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(1000)
            fname = f"{OUT_DIR}/{safe(u)}__{ts}.jpg"
            page.screenshot(path=fname, type="jpeg", quality=75, full_page=False)
            print("Saved", fname)
        except Exception as e:
            print("ERROR:", u, e)
    browser.close()
