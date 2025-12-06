import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://dizipall30.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

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

        # GERÇEK film kutusu seçicisi
        blocks = soup.select("div.group")
        if not blocks:
            print("❌ Film bulunamadı, tarama bitti.")
            break

        print(f"  • Bulunan film kutusu: {len(blocks)}")

        for m in blocks:

            # başlık
            title_el = m.select_one("div.font-semibold")
            title = title_el.get_text(strip=True) if title_el else ""

            # tür + yıl birlikte geliyor: "Aksiyon • Gerilim • 2023"
            info_el = m.select_one("div.text-xs")
            info_text = info_el.get_text(strip=True) if info_el else ""
            year = ""
            genre = ""

            if "•" in info_text:
                parts = [x.strip() for x in info_text.split("•")]
                if parts[-1].isdigit():
                    year = parts[-1]
                    genre = " | ".join(parts[:-1])
                else:
                    genre = info_text

            # resim
            img_el = m.find("img")
            image = img_el["src"] if img_el else ""

            # detay linki
            a = m.find("a")
            detail_url = BASE + a["href"] if a and a.has_attr("href") else ""

            # embed
            embed = get_embed(detail_url) if detail_url else ""

            all_movies.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": image,
                "detail_url": detail_url,
                "embed_url": embed
            })

        page += 1
        time.sleep(0.3)

    return all_movies


if __name__ == "__main__":
    print("🔍 Film taraması başlıyor...\n")

    movies = scrape_all_movies()

    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Toplam film: {len(movies)}")
    print("💾 film.json kaydedildi!\n")
