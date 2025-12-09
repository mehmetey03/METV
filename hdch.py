import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from pathlib import Path

BASE = "https://www.hdfilmcehennemi.ws/load/page/{}/categories/film-izle-2/"
MAX_PAGES = 2000  # maksimum denenecek, boş gelince durur
OUT_FILE = "hdceh.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def fetch_page(page):
    url = BASE.format(page)
    logging.info(f"Fetching: {url}")

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            logging.warning(f"[WARN] HTTP {r.status_code}")
            return ""
        return r.text
    except Exception as e:
        logging.error(f"Request error: {e}")
        return ""


def parse_films(html):
    soup = BeautifulSoup(html, "html.parser")

    items = soup.select("div.item")
    films = []

    for item in items:
        try:
            a = item.select_one("a")
            if not a:
                continue

            url = a.get("href")

            img = a.select_one("img")
            image = (
                img.get("data-src")
                or img.get("src")
                if img else None
            )

            title_el = item.select_one(".poster span")
            title = title_el.get_text(strip=True) if title_el else "NoTitle"

            films.append({
                "title": title,
                "url": url,
                "image": image
            })
        except Exception as e:
            logging.error(f"Parse Error: {e}")
            continue

    return films


def main():
    all_films = []
    empty_count = 0

    for page in range(1, MAX_PAGES + 1):
        html = fetch_page(page)

        if not html or html.strip() == "":
            empty_count += 1
            logging.warning(f"[EMPTY] Page {page}")
            if empty_count >= 5:
                logging.warning("Too many empty pages → STOPPING")
                break
            continue

        films = parse_films(html)
        logging.info(f"Page {page}: Found {len(films)} films")

        if len(films) == 0:
            empty_count += 1
            if empty_count >= 5:
                break
            continue
        else:
            empty_count = 0

        all_films.extend(films)

        time.sleep(1)

    Path(OUT_FILE).write_text(json.dumps(all_films, indent=2, ensure_ascii=False), encoding="utf8")

    logging.info(f"SAVED: {OUT_FILE}")
    logging.info(f"Total films: {len(all_films)}")


if __name__ == "__main__":
    main()
