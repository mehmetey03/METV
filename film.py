import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://dizipall30.com"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
})

def get_html(url):
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200 and len(r.text) > 200:
            return r.text
        else:
            print("⚠ Boş/korumalı HTML:", url)
    except:
        pass
    return ""


def get_embed(detail_url):
    html = get_html(detail_url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")
    iframe = soup.select_one("iframe")

    if iframe:
        src = iframe.get("src", "")
        if src.startswith("//"):
            src = "https:" + src
        return src

    return ""


def scrape():
    all_movies = []
    page = 1

    while True:
        url = f"{BASE}/filmler/{page}"
        print(f"→ Tarama: {url}")

        html = get_html(url)
        if not html:
            print("❌ Film bulunamadı (HTML boş) → Durdu.")
            break

        soup = BeautifulSoup(html, "html.parser")

        blocks = soup.select("div.group")
        if not blocks:
            print("❌ Film kutusu yok → Durdu.")
            break

        print(f"  • {len(blocks)} film bulundu")

        for m in blocks:

            # Başlık
            title = (m.select_one("div.font-semibold") or "").get_text(strip=True)

            # Tür + yıl
            info = (m.select_one("div.text-xs") or "").get_text(strip=True)
            year = ""
            genre = ""

            if "•" in info:
                parts = [x.strip() for x in info.split("•")]
                if parts[-1].isdigit():
                    year = parts[-1]
                    genre = " | ".join(parts[:-1])

            # Resim
            img = ""
            imgtag = m.find("img")
            if imgtag:
                img = imgtag.get("src", "")

            # Detay URL
            a = m.find("a")
            detail = BASE + a["href"] if a else ""

            # Embed
            embed = get_embed(detail) if detail else ""

            all_movies.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail,
                "embed_url": embed
            })

        page += 1
        time.sleep(0.2)

    return all_movies


if __name__ == "__main__":
    print("🔍 Film taraması başlıyor...\n")

    movies = scrape()

    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Toplam film: {len(movies)}")
    print("💾 film.json kaydedildi!\n")
