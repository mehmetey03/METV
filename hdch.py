import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://www.hdfilmcehennemi.ws/wp-admin/admin-ajax.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.hdfilmcehennemi.ws/"
}

def fetch_page(page):
    data = {
        "action": "load_more_movies",
        "page": page
    }

    r = requests.post(BASE, headers=HEADERS, data=data)
    if r.status_code != 200:
        print(f"[WARN] Page {page} HTTP {r.status_code}")
        return None

    html = r.text.strip()
    if "404" in html.lower():
        print(f"[WARN] Page {page} returned 404 content")
        return None

    return html


def parse_films(html):
    soup = BeautifulSoup(html, "html.parser")
    films = []

    items = soup.select(".poster")  # film blokları

    for item in items:
        a = item.select_one("a")
        if not a:
            continue

        url = a["href"]
        title = a.get("title", "").strip()

        img = item.select_one("img")
        image = img["src"] if img else ""

        year = ""
        year_tag = item.select_one(".year span")
        if year_tag:
            year = year_tag.text.strip()

        films.append({
            "title": title,
            "url": url,
            "image": image,
            "year": year
        })

    return films


def main():
    all_films = []
    page = 1

    while True:
        print(f"Fetching page {page}...")

        html = fetch_page(page)
        if not html:
            break

        films = parse_films(html)
        if not films:
            print("No more films, stopping.")
            break

        all_films += films
        page += 1
        time.sleep(1)

    # JSON kaydet
    with open("films.json", "w", encoding="utf-8") as f:
        json.dump(all_films, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(all_films)} films.")


if __name__ == "__main__":
    main()
