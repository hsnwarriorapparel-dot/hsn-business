#!/usr/bin/env python3
"""Fetch IG reel details via CDP in the logged-in browser (robust version)."""
import json, time, sys
from playwright.sync_api import sync_playwright

REEL = "https://www.instagram.com/reel/Det1pPiguyg/"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for c in browser.contexts:
        for pg in c.pages:
            if "instagram.com" in pg.url:
                page = pg
                break
        if page: break
    if page is None:
        page = browser.contexts[0].new_page()
    print("tab:", page.url[:70], flush=True)
    try:
        page.goto(REEL, wait_until="commit", timeout=30000)
    except Exception as e:
        print("goto warn:", str(e)[:120], flush=True)
    time.sleep(8)
    print("title:", page.title()[:100], flush=True)
    data = page.evaluate("""() => {
        const vid = document.querySelector('video');
        const sd = document.querySelector('script[type="application/json"]');
        return {
            videoSrc: vid ? (vid.src || vid.currentSrc) : null,
            firstJson: sd ? sd.textContent.slice(0, 600) : null,
            text: document.body ? document.body.innerText.slice(0, 300) : ''
        };
    }""")
    print("DATA:", json.dumps(data, indent=1)[:1500], flush=True)
    page.screenshot(path="/tmp/ig_reel.png")
    print("SCREENSHOT_OK", flush=True)
