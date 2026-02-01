#!/usr/bin/env python3
"""
hdch_final_ultimate_FIXED.py
"""

import urllib.request
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.hdfilmcehennemi.nl/"
API_URL  = "https://www.hdfilmcehennemi.nl/wp-json/wp/v2/posts"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/json",
    "Referer": BASE_URL
}

# --------------------------------------------------
def get_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")

# --------------------------------------------------
def fetch_films_from_api(page=1, per_page=100):
    url = f"{API_URL}?page={page}&per_page={per_page}"
    data = json.loads(get_html(url))

    films = []
    for item in data:
        films.append({
            "url": item["link"],
            "title": html.unescape(item["title"]["rendered"]),
            "year": item["date"][:4],
            "imdb": "0.0",
            "image": "",
            "language": "",
            "type": "dizi" if "/dizi/" in item["link"] else "film",
            "token": str(item["id"]),
            "source": url,
            "scraped_at": datetime.now().isoformat()
        })
    return films

# --------------------------------------------------
def extract_embed_url_from_film_page(film_url, token):
    html_content = get_html(film_url)
    if not html_content:
        return None

    # iframe src / data-src
    patterns = [
        r'<iframe[^>]+data-src="([^"]+)"',
        r'<iframe[^>]+src="([^"]+)"'
    ]

    for p in patterns:
        m = re.search(p, html_content, re.IGNORECASE)
        if m:
            src = m.group(1)
            if src.startswith("//"):
                src = "https:" + src

            # rapidvid / rapidrame istemiyoruz
            if "rapidvid" in src or "rapidrame" in src:
                continue

            if "hdfilmcehennemi" in src:
                return src

    # token fallback
    if token:
        return f"{EMBED_BASE}{token}/"

    return None

# --------------------------------------------------
def scrape_discovery_pages():
    print("[*] Discovery (API based)")
    films = []
    page = 1

    while True:
        try:
            batch = fetch_films_from_api(page)
            if not batch:
                break
            films.extend(batch)
            print(f"  Page {page}: {len(batch)} film")
            page += 1
            time.sleep(0.3)
        except:
            break

    return films

# --------------------------------------------------
def main():
    print("Starting FIXED scraping...\n")

    all_films = scrape_discovery_pages()

    if not all_films:
        print("❌ No films found!")
        return

    # unique
    uniq = {}
    for f in all_films:
        uniq[f["url"]] = f
    films = list(uniq.values())

    print(f"\n✓ Found {len(films)} films\n")

    print("Fetching embed URLs...\n")
    for i, film in enumerate(films, 1):
        print(f"[{i}/{len(films)}] {film['title'][:40]}")
        film["embed_url"] = extract_embed_url_from_film_page(
            film["url"], film.get("token")
        )
        time.sleep(0.1)

    with open("hdfilms_complete.json", "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=2)

    print("\n✅ DONE")
    print(f"🎬 Embed bulunan: {sum(1 for f in films if f.get('embed_url'))}")

# --------------------------------------------------
if __name__ == "__main__":
    main()
