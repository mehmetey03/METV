#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HDFilmCehennemi FIXED Scraper
- Film listesi: WordPress JSON API
- Embed: iframe src (player)
"""

import urllib.request
import json
import re
import html
import time
from datetime import datetime

API_URL = "https://www.hdfilmcehennemi.nl/wp-json/wp/v2/posts"
EMBED_DOMAIN = "hdfilmcehennemi.mobi"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "text/html,application/json",
    "Referer": "https://www.hdfilmcehennemi.nl/"
}


# -------------------------------------------------
def get_url(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


# -------------------------------------------------
def fetch_films(page=1, per_page=50):
    url = f"{API_URL}?per_page={per_page}&page={page}"
    data = json.loads(get_url(url))
    films = []

    for item in data:
        films.append({
            "title": html.unescape(item["title"]["rendered"]),
            "url": item["link"],
            "id": item["id"],
            "date": item["date"]
        })

    return films


# -------------------------------------------------
def extract_embed(film_url):
    html_content = get_url(film_url)

    # iframe src veya data-src
    patterns = [
        r'<iframe[^>]+src="([^"]+)"',
        r'<iframe[^>]+data-src="([^"]+)"'
    ]

    for p in patterns:
        m = re.search(p, html_content, re.IGNORECASE)
        if m:
            src = m.group(1)

            # // ile başlıyorsa
            if src.startswith("//"):
                src = "https:" + src

            # rapidvid / rapidrame ise geç
            if "rapidvid" in src or "rapidrame" in src:
                continue

            # player domain zorla
            if EMBED_DOMAIN in src:
                return src

    return None


# -------------------------------------------------
def main():
    print("=== HDFilmCehennemi FIXED Scraper ===\n")

    all_films = []
    page = 1

    while True:
        try:
            films = fetch_films(page)
            if not films:
                break

            print(f"[+] Page {page}: {len(films)} film")
            all_films.extend(films)
            page += 1
            time.sleep(0.3)

        except Exception:
            break

    print(f"\n[✓] Toplam film: {len(all_films)}\n")

    results = []

    for i, film in enumerate(all_films, 1):
        print(f"[{i}/{len(all_films)}] {film['title'][:50]}")

        embed = extract_embed(film["url"])

        results.append({
            "title": film["title"],
            "url": film["url"],
            "embed_url": embed,
            "scraped_at": datetime.now().isoformat()
        })

        time.sleep(0.1)

    # KAYDET
    with open("hdceh_embeds.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n✅ Bitti")
    print("📁 Dosya: hdceh_embeds.json")
    print(f"🎬 Embed bulunan: {sum(1 for x in results if x['embed_url'])}")


# -------------------------------------------------
if __name__ == "__main__":
    main()
