import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://dizipall30.com"
HEADERS = { "User-Agent": "Mozilla/5.0" }


# -------------------------------------------------
# Embed çözücü
# -------------------------------------------------
def get_embed(detail_url):
    try:
        r = requests.get(detail_url, headers=HEADERS, timeout=10)
    except:
        return ""

    if r.status_code != 200:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")

    iframe = soup.select_one("iframe")
    if iframe:
        src = iframe.get("src", "")
        if src.startswith("//"):
            src = "https:" + src
        return src

    return ""


# -------------------------------------------------
# Tüm filmleri tarayan ana fonksiyon
# -------------------------------------------------
def scrape_all_movies():
    all_movies = []
    page = 1

    while True:
        url = f"{BASE}/filmler/{page}"
        print(f"→ Tarama: {url}", flush=True)

        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
        except:
            print("❌ İstek hatası, durduruldu.")
            break

        if r.status_code != 200:
            print("❌ Status kodu:", r.status_code)
            break

        soup = BeautifulSoup(r.text, "html.parser")

        movies = soup.select(".movie-card")
        if not movies:
            print("❌ Film bulunamadı, tarama bitti.")
            break

        print(f"  • Bulunan film sayısı: {len(movies)}")

        for m in movies:
            title = m.select_one(".movie-name")
            title = title.get_text(strip=True) if title else ""

            year = m.select_one(".movie-year")
            year = year.get_text(strip=True) if year else ""

            genre = m.select_one(".movie-type")
            genre = genre.get_text(strip=True) if genre else ""

            img = m.select_one("img")
            img = img["src"] if img and "src" in img.attrs else ""

            link = m.select_one("a")
            if link:
                detail_url = BASE + link["href"]
            else:
                detail_url = ""

            embed_url = get_embed(detail_url) if detail_url else ""

            all_movies.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": embed_url
            })

        page += 1
        time.sleep(0.5)

    return all_movies


# -------------------------------------------------
# JSON KAYIT
# -------------------------------------------------
if __name__ == "__main__":
    print("🔍 Film taraması başlıyor...\n")
    movies = scrape_all_movies()

    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Toplam film: {len(movies)}")
    print("💾 film.json kaydedildi!\n")
