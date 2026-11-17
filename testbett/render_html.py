#!/usr/bin/env python3
"""Render the local HTML test pages with headless Chromium at 1920x1080.

Each page has states ?s=1..3. Ground truth comes from the page itself: gt.js writes element
types, boxes, texts and states into <pre id="gt">, read here from Chromium's page dump.

Usage: python render_html.py
"""
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(ROOT, "html_pages")
OUT = os.path.join(ROOT, "data", "html")
# development pages and held-out pages
DEV_PAGES = ("login", "settings", "files", "editor")
HOLDOUT_PAGES = ("mail", "checkout")
JOBS = [(p, s) for p in DEV_PAGES for s in (1, 2, 3)] + [(p, s) for p in HOLDOUT_PAGES for s in (1, 2)]


def browser():
    for b in ("chromium", "google-chrome", "google-chrome-stable", "chromium-browser"):
        if shutil.which(b):
            return b
    raise SystemExit("no Chromium found (firefox --screenshot has no page dump; not supported here)")


def render(job):
    page, s = job
    exe = browser()
    url = f"file://{PAGES}/{page}.html?s={s}"
    png = os.path.join(OUT, f"{page}_s{s}.png")
    with tempfile.TemporaryDirectory() as prof:
        common = [exe, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                  "--window-size=1920,1080", "--virtual-time-budget=1500", f"--user-data-dir={prof}",
                  "--font-render-hinting=none"]
        subprocess.run(common + [f"--screenshot={png}", url], capture_output=True, timeout=120)
        page_html = subprocess.run(common + ["--dump-dom", url], capture_output=True, timeout=120, text=True).stdout
    m = re.search(r'<pre id="gt"[^>]*>(.*?)</pre>', page_html, re.S)
    if not m:
        raise RuntimeError(f"no ground truth in page dump for {page} s={s}")
    gt = json.loads(html.unescape(m.group(1)))
    gt["meta"] = dict(page=page, state=s)
    with open(png[:-4] + ".json", "w") as f:
        json.dump(gt, f, ensure_ascii=False)
    return page, s, len(gt["elements"]), len(gt["spans"])


def main():
    os.makedirs(OUT, exist_ok=True)
    with ThreadPoolExecutor(4) as ex:
        for page, s, ne, ns in ex.map(render, JOBS):
            print(f"{page} s={s}: {ne} elements, {ns} text spans")


if __name__ == "__main__":
    main()
