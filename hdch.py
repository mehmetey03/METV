import requests
from bs4 import BeautifulSoup
import time

BASE = "https://hdfilmcehennemi.life"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": BASE,
}

def fetch_page(page):
    url = f"{BASE}/filmler/sayfa/{page}/"
    print(f"Fetching: {url}")

    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        print("[WARN] HTTP", r.status_code)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    items = soup.select(".moviefilm")     # Filmlerin olduğu class

    films = []
    for f in items:
        title = f.select_one("img")["alt"] if f.select_one("img") else "No title"
        img = f.select_one("img")["src"] if f.select_one("img") else ""
        link = f.select_one("a")["href"] if f.select_one("a") else ""

        if not link.startswith("http"):
            link = BASE + link

        films.append({
            "title": title,
            "image": img,
            "url": link
        })

    return films


all_films = []

for page in range(1, 50):  # 50 sayfa istersen artırılır
    films = fetch_page(page)
    if not films:
        print("No more films. Stopping.")
        break

    all_films.extend(films)
    print(f"Page {page}: {len(films)} films")
    time.sleep(1)

print("Total films:", len(all_films))
