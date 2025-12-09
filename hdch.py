import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://www.hdfilmcehennemi.ws"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",   # AJAX olduğumuzu belirtiyoruz
    "Referer": BASE + "/filmler",
    "Accept": "text/html, */*; q=0.01"
}

def fetch_ajax(page):
    """ AJAX sayfasını indir """
    url = f"{BASE}/load/page/{page}/categories/film-izle-2/"
    print(f"[FETCH] {url}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and len(r.text) > 50:
            return r.text
        else:
            print("[EMPTY] -> 404 veya boş içerik")
            return None
    except Exception as e:
        print("[ERROR]", e)
        return None


def parse_films(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".moviefilm, .moviesfilm, .flw-item")

    films = []
    for item in items:
        title = item.select_one("img")["alt"] if item.select_one("img") else "No title"
        img = item.select_one("img")["src"] if item.select_one("img") else ""
        link = item.select_one("a")["href"] if item.select_one("a") else ""

        films.append({
            "title": title,
            "img": img,
            "link": BASE + link if link.startswith("/") else link
        })

    return films


all_films = []
empty_count = 0

print("=== START ===")

for page in range(1, 500):
    html = fetch_ajax(page)

    if not html:
        empty_count += 1
        if empty_count >= 5:
            print("Too many empty pages → STOP")
            break
        continue

    films = parse_films(html)
    print(f"[PAGE {page}] Films found:", len(films))

    if len(films) == 0:
        empty_count += 1
    else:
        empty_count = 0

    all_films.extend(films)
    time.sleep(1)

print("\nTOTAL FILMS:", len(all_films))

with open("hdceh.json", "w", encoding="utf-8") as f:
    json.dump(all_films, f, ensure_ascii=False, indent=2)

print("Saved → hdceh.json")
