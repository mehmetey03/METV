import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from pathlib import Path

BASE = "https://www.hdfilmcehennemi.ws/filmler/sayfa/{}/"
MAX_PAGES = 1124
OUT_FILE = "hdceh.json"
SUMMARY_FILE = "hdceh_summary.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_page(page):
    url = BASE.format(page)
    logging.info(f"Fetching page {page}: {url}")

    try:
        r = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        logging.error(f"Request failed: {e}")
        return None

    if r.status_code == 404:
        logging.warning(f"Page {page} returned 404 → STOP")
        return None

    return r.text


def parse_films(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".item")
    films = []

    for item in items:
        try:
            a = item.select_one(".poster a")
            if not a:
                continue

            link = a.get("href")
            title = a.get("title") or item.select_one(".film-title").get_text(strip=True)

            img_el = a.select_one("img")
            image = (
                img_el.get("data-src")
                or img_el.get("data-original")
                or img_el.get("src")
            )

            films.append({
                "title": title,
                "url": link,
                "image": image
            })
        except Exception as e:
            logging.error(f"Parse error: {e}")
            continue

    return films


def main():
    all_films = []
    empty_count = 0

    logging.info("=== SCRAPING START ===")

    for page in range(1, MAX_PAGES + 1):
        html = fetch_page(page)
        if not html:
            empty_count += 1
            if empty_count >= 5:
                logging.warning("Too many empty pages — stopping")
                break
            continue

        films = parse_films(html)
        logging.info(f"Page {page}: found {len(films)} films")

        if len(films) == 0:
            empty_count += 1
            if empty_count >= 5:
                break
        else:
            empty_count = 0

        all_films.extend(films)
        time.sleep(1)

    Path(OUT_FILE).write_text(json.dumps(all_films, indent=2, ensure_ascii=False), encoding="utf8")

    summary = {
        "total_films": len(all_films),
        "pages_scanned": page,
        "output": OUT_FILE
    }

    Path(SUMMARY_FILE).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf8")

    logging.info(f"Saved: {OUT_FILE}")
    logging.info(f"Summary: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
