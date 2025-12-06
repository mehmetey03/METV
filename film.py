import requests
import json
from bs4 import BeautifulSoup

START_DOMAIN = 30
END_DOMAIN = 100

BASE_URL = None
ALL_MOVIES = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def find_active_domain():
    global BASE_URL

    print("🔍 Aktif domain aranıyor...\n")

    for i in range(START_DOMAIN, END_DOMAIN + 1):
        test = f"https://dizipall{i}.com"
        try:
            print(f"  Deneniyor: {test}")
            r = requests.get(test, timeout=6, headers=HEADERS)

            if r.status_code == 200 and "Film" in r.text:
                BASE_URL = test
                print(f"  ✓ Aktif bulundu: {BASE_URL}\n")
                return BASE_URL

        except:
            pass

    print("❌ Domain bulunamadı!")
    exit()


# ---------------- EMBED ALMA ----------------

def get_embed(detail_url):
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")

        player = soup.select_one("iframe[data-player], iframe[src*='dizipal']")
        if player:
            if player.has_attr("data-player"):
                return player["data-player"]
            if player.has_attr("src"):
                return player["src"]

    except Exception:
        return ""

    return ""


# --------------- TEK SAYFA OKUMA --------------

def get_movies_from_page(page):
    url = f"{BASE_URL}/film?page={page}"
    print(f"  → Sayfa: {url}")

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.select("div.col-xl-2.col-lg-3.col-md-4.col-sm-4.col-6.mb-3")

    if not cards:
        return []

    movies = []

    for c in cards:
        a = c.select_one("a")
        img = c.select_one("img")
        title = c.select_one(".video-card-title")

        if not a:
            continue

        detail_url = BASE_URL + a["href"]

        embed_url = get_embed(detail_url)

        movies.append({
            "title": title.text.strip() if title else "",
            "image": img["src"] if img else "",
            "detail_url": detail_url,
            "embed_url": embed_url
        })

    return movies


# ---------------- TÜM SAYFALARI OKU ----------------

def scrape_all():
    print("📄 Film sayfaları taranıyor...\n")
    page = 1

    while True:
        movies = get_movies_from_page(page)

        if not movies:
            break

        ALL_MOVIES.extend(movies)

        print(f"  ✓ {len(movies)} film bulundu (Sayfa {page})\n")

        page += 1

    print(f"🎉 Toplam film: {len(ALL_MOVIES)}\n")


def save_json():
    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(ALL_MOVIES, f, ensure_ascii=False, indent=4)

    print("💾 film.json kaydedildi!\n")


if __name__ == "__main__":
    find_active_domain()
    scrape_all()
    save_json()
