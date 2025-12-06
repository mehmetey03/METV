import requests
import json
from bs4 import BeautifulSoup

HEAD = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
}

def aktif_domaini_bul():
    print("🔍 Aktif domain aranıyor...\n")

    for i in range(30, 101):   # 30 → 100
        domain = f"https://dizipall{i}.com"

        print(f"  Deneniyor: {domain}")
        try:
            r = requests.get(domain + "/filmler/1", headers=HEAD, timeout=5)
            if r.status_code == 200 and "filmler" in r.text.lower():
                print(f"  ✓ Aktif bulundu: {domain}\n")
                return domain
        except:
            pass

    print("❌ Domain bulunamadı!")
    return None


def filmleri_tar(domain):
    print("📄 Film sayfaları taranıyor...\n")

    filmler = []
    sayfa = 1

    while True:
        url = f"{domain}/filmler/{sayfa}"
        print(f"  → Sayfa: {url}")

        try:
            r = requests.get(url, headers=HEAD, timeout=10)
            if r.status_code != 200:
                break
        except:
            break

        soup = BeautifulSoup(r.text, "html.parser")

        items = soup.select(".movie-item")
        if not items:
            break  # artık film yok → dur

        for item in items:
            title = item.select_one("h3").get_text(strip=True)
            link = domain + item.select_one("a")["href"]
            img = item.select_one("img")["src"]

            filmler.append({
                "title": title,
                "link": link,
                "image": img
            })

        sayfa += 1

    print(f"\n🎉 Toplam film: {len(filmler)}\n")
    return filmler


def kaydet(veri):
    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    print("💾 film.json kaydedildi!")


if __name__ == "__main__":
    domain = aktif_domaini_bul()
    if domain:
        data = filmleri_tar(domain)
        kaydet(data)
