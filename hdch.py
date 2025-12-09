import requests
import json
import re
from bs4 import BeautifulSoup

BASE = "https://www.hdfilmcehennemi.ws"
CAT = "film-izle-2"
OUT = "film_izle_2.json"

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/category/{CAT}/",
})

def get_page(page):
    url = f"{BASE}/load/page/{page}/categories/{CAT}/"
    r = session.get(url)

    if r.status_code != 200:
        print(f"[WARN] Page {page} Status {r.status_code}")
        return None

    if not r.text.strip():
        print(f"[EMPTY] Page {page}")
        return None

    return r.text


def extract_films(html):
    soup = BeautifulSoup(html, "html.parser")
    films = []

    for a in soup.select("a"):
        href = a.get("href", "")
        if "/film/" in href:
            films.append(BASE + href)

    return list(set(films))


def get_embed_links(film_url):
    r = session.get(film_url)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    embeds = []

    # iframe embed
    for f in soup.select("iframe"):
        src = f.get("src", "")
        if "http" in src:
            embeds.append(src)

    # JS içinde player?id=
    m = re.findall(r'player/\?id=\w+', r.text)
    for x in m:
        embeds.append(BASE + "/" + x)

    return list(set(embeds))


all_films = []
seen = set()
empty_streak = 0

print("\n=== START SCRAPING film-izle-2 ===\n")

for page in range(1, 999):
    html = get_page(page)
    if not html:
        empty_streak += 1
        if empty_streak >= 5:
            print("[STOP] Too many empty pages")
            break
        continue

    empty_streak = 0
    film_urls = extract_films(html)
    print(f"[PAGE {page}] Found {len(film_urls)} films")

    for film in film_urls:
        if film in seen:
            continue
        seen.add(film)

        embeds = get_embed_links(film)
        print(f" -> {film} | {len(embeds)} embed")

        all_films.append({
            "url": film,
            "embeds": embeds
        })

print("\nSaving JSON...")
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(all_films, f, ensure_ascii=False, indent=2)

print(f"Saved → {OUT}")
print(f"Total films: {len(all_films)}")
