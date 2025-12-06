import requests
import json
from bs4 import BeautifulSoup

# ----------------------------------------------------------
# AYARLAR
# ----------------------------------------------------------

START_DOMAIN = 30
END_DOMAIN = 100

BASE_URL = None
ALL_MOVIES = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ----------------------------------------------------------
# 1) ÇALIŞAN DOMAINİ BUL
# ----------------------------------------------------------

def find_active_domain():
    global BASE_URL

    print("🔍 Aktif domain aranıyor...\n")

    for i in range(START_DOMAIN, END_DOMAIN + 1):
        test = f"https://dizipall{i}.com"
        try:
            print(f"  Deneniyor: {test}")
            r = requests.get(test, timeout=6, headers=HEADERS)

            if r.status_code == 200 and "Film" in r.text and len(r.text) > 5000:
                BASE_URL = test
                print(f"  ✓ Aktif bulundu: {BASE_URL}\n")
                return BASE_URL

        except:
            pass

    print("❌ Aktif domain bulunamadı!")
    exit()


# ----------------------------------------------------------
# 2) TEK SAYFA FİLM ÇEKME
# ----------------------------------------------------------

def get_movies_from_page(page):
    url = f"{BASE_URL}/film?page={page}"
    print(f"  → Sayfa: {url}")

    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.select(".video-card")
    if not cards:
        return []

    movies = []

    for c in cards:
        title = c.select_one(".video-card-title")
        image = c.select_one("img")
        detail = c.select_one("a")
        embed_data = c.select_one("a[data-embed]")

        movies.append({
            "title": title.text.strip() if title else "",
            "image": image["src"] if image else "",
            "detail_url": BASE_URL + detail["href"] if detail else "",
            "embed_url": embed_data["data-embed"] if embed_data else ""
        })

    return movies


# ----------------------------------------------------------
# 3) TÜM SAYFALARI ÇEK
# ----------------------------------------------------------

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


# ----------------------------------------------------------
# 4) JSON KAYDET
# ----------------------------------------------------------

def save_json():
    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(ALL_MOVIES, f, ensure_ascii=False, indent=4)

    print("💾 film.json kaydedildi!\n")


# ----------------------------------------------------------
# ÇALIŞTIR
# ----------------------------------------------------------

if __name__ == "__main__":
    find_active_domain()
    scrape_all()
    save_json()
