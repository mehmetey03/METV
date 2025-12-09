#!/usr/bin/env python3
# hdch_fixed.py - HDFilmCehennemi Scraper (Fixed)

import requests
import json
import re
import time
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from bs4 import BeautifulSoup

# ======================
# CONFIG
# ======================
BASE_URL = "https://www.hdfilmcehennemi.ws/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Referer': BASE_URL,
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update(HEADERS)

# ======================
# HELPERS
# ======================

def get_page_html(url):
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            return None
        return response.text
    except Exception as e:
        logger.error(f"Request error: {url} -> {e}")
        return None


# ==========================
# FILM EXTRACTION
# ==========================

def extract_films_modern(html, page_num):
    films = []
    if not html:
        return films

    soup = BeautifulSoup(html, "html.parser")

    containers = soup.select(".ml-item, article, .movie, .film-item, div[class*=movie]")

    logger.info(f"Page {page_num}: Found containers = {len(containers)}")

    for i, item in enumerate(containers, 1):

        link_tag = item.find("a", href=True)
        if not link_tag:
            continue

        url = link_tag["href"]
        if not url.startswith("http"):
            url = urljoin(BASE_URL, url)

        # title
        title = link_tag.get("title") or link_tag.get_text(strip=True)
        if not title:
            continue
        title = title.replace(" izle", "").strip()

        # image
        img_tag = item.find("img")
        img = ""
        if img_tag:
            img = img_tag.get("data-src") or img_tag.get("src") or ""

        # year detection
        text = item.get_text()
        year = ""
        m = re.search(r"(19|20)\d{2}", text)
        if m:
            year = m.group(0)

        imdb = "0.0"
        m = re.search(r"IMDB[: ]*([0-9.]+)", text, re.I)
        if m:
            imdb = m.group(1)

        film_type = "dizi" if "/dizi/" in url else "film"

        films.append({
            "page": page_num,
            "position": i,
            "url": url,
            "title": title,
            "image": img,
            "year": year,
            "imdb": imdb,
            "type": film_type,
            "embed_url": ""
        })

    return films


# ======================
# SUMMARY
# ======================

def generate_summary(films, output_file):
    summary = {
        "total_films": len(films),
        "by_type": {"film": 0, "dizi": 0},
        "by_year": {},
        "top_imdb": []
    }

    for f in films:
        summary["by_type"][f["type"]] += 1
        year = f["year"] or "Unknown"
        summary["by_year"][year] = summary["by_year"].get(year, 0) + 1

    # IMDB sort
    imdb_list = []
    for f in films:
        try:
            score = float(f["imdb"])
            if 0 < score <= 10:
                imdb_list.append(f)
        except:
            pass

    imdb_list.sort(key=lambda x: float(x["imdb"]), reverse=True)
    summary["top_imdb"] = imdb_list[:10]

    sfile = output_file.replace(".json", "_summary.json")
    with open(sfile, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"SUMMARY SAVED → {sfile}")


# ======================
# MANUAL SCRAPE
# ======================

def manual_scrape(output_file):
    print("\n=== SCRAPING START ===")

    films_all = []

    html = get_page_html(BASE_URL)
    if html:
        f = extract_films_modern(html, 1)
        films_all.extend(f)
        print(f"Home page films: {len(f)}")

    # category pages
    categories = ["film", "dizi", "film-izle"]

    for c in categories:
        url = BASE_URL + "kategori/" + c + "/"
        html = get_page_html(url)
        if html:
            f = extract_films_modern(html, 2)
            films_all.extend(f)
            print(f"Category {c}: {len(f)} found")
            time.sleep(1)

    # remove duplicates
    uniq = []
    seen = set()
    for f in films_all:
        if f["url"] not in seen:
            uniq.append(f)
            seen.add(f["url"])

    result = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_films": len(uniq)
        },
        "films": uniq
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nSaved → {output_file}")
    generate_summary(uniq, output_file)
    return True


# ======================
# TEST SINGLE PAGE
# ======================

def test_single_page():
    """Scrape a single movie page and show embed iframe."""
    test_url = "https://www.hdfilmcehennemi.ws/film/joker-folie-a-deux-izle/"
    html = get_page_html(test_url)
    if not html:
        print("Page load failed")
        return

    soup = BeautifulSoup(html, "html.parser")

    iframe = soup.find("iframe")
    if iframe:
        print("\nFOUND EMBED URL:")
        print(iframe.get("src"))
    else:
        print("\nNo iframe found")


# ======================
# MAIN
# ======================

if __name__ == "__main__":
    manual_scrape("hdceh.json")
