import requests
import re
import json
import yaml
from time import sleep

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "gzip"
})


# --------------------------------------------------
# 🔍 1) Aktif DİZİPALL Domainini Bul
# --------------------------------------------------
def find_active_domain():
    print("🔍 Aktif dizipall domaini aranıyor...")
    for i in range(1, 101):
        url = f"https://dizipall{i}.com"
        try:
            r = session.get(url, timeout=4)
            if r.status_code == 200 and len(r.text) > 500:
                print(f"✅ Aktif domain bulundu → {url}")
                return url
        except:
            pass

        print(f"❌ {url} çalışmıyor…")

    print("⛔ Hiçbir domain çalışmadı!")
    return None


# --------------------------------------------------
# 🔍 2) Embed URL Tespit Et
# --------------------------------------------------
def get_embed(detail_url):
    html = fast_get(detail_url)
    if not html:
        return ""

    # iframe
    m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    if m:
        src = m.group(1)
        if src.startswith("//"):
            return "https:" + src
        if src.startswith("/"):
            return "https://dizipal.website" + src
        return src

    # data-video-id
    m = re.search(r'data-video-id=["\']([A-Za-z0-9]+)["\']', html)
    if m:
        return "https://dizipal.website/" + m.group(1)

    # fallback
    m = re.search(r'https?://dizipal\.website/[A-Za-z0-9]+', html)
    if m:
        return m.group(0)

    return ""


# --------------------------------------------------
# Güvenli istek
# --------------------------------------------------
def fast_get(url):
    try:
        r = session.get(url, timeout=8)
        return r.text
    except:
        return ""


# --------------------------------------------------
# 🔍 3) Tek Sayfa Film Listele
# --------------------------------------------------
def scrape_page(domain, page):
    print(f"➡ Sayfa taranıyor: {page}")
    LIST_URL = domain + "/filmler/{}"
    html = fast_get(LIST_URL.format(page))

    if not html:
        print(f"⚠ Sayfa okunamadı {page}")
        return []

    movies = []

    blocks = re.findall(r'<li class="[^"]*w-1/2[^"]*"[^>]*>(.*?)</li>', html, flags=re.DOTALL)

    for b in blocks:
        title = re.search(r'<h2[^>]*>(.*?)</h2>', b)
        year = re.search(r'year[^>]*>(.*?)<', b)
        genre = re.search(r'title="([^"]+)"', b)
        image = re.search(r'src="(https://dizipall\d+\.com[^"]+)"', b)
        detail = re.search(r'href="(https://dizipall\d+\.com/film/[^"]+)"', b)

        if not title:
            continue

        detail_url = detail.group(1) if detail else ""
        embed_url = get_embed(detail_url) if detail_url else ""

        movies.append({
            "title": title.group(1).strip(),
            "year": year.group(1).strip() if year else "",
            "genre": genre.group(1).strip() if genre else "",
            "image": image.group(1) if image else "",
            "detail_url": detail_url,
            "embed_url": embed_url
        })

        sleep(0.15)

    return movies


# --------------------------------------------------
# 🔥 4) ANA PROGRAM
# --------------------------------------------------
def main():
    domain = find_active_domain()
    if domain is None:
        print("⛔ Domain bulunamadı, çıkılıyor.")
        return

    all_movies = []
    max_pages = 160  # istenirse artırılabilir

    for p in range(1, max_pages + 1):
        films = scrape_page(domain, p)
        if not films:
            print("⛔ Boş sayfa → tarama bitti")
            break
        all_movies.extend(films)

    print(f"\n✔ Toplam film: {len(all_movies)}\n")

    # JSON yaz
    with open("filmjson.json", "w", encoding="utf-8") as f:
        json.dump(all_movies, f, ensure_ascii=False, indent=2)
    print("📁 Kaydedildi: filmjson.json")

    # YAML yaz
    with open("filmjson.yml", "w", encoding="utf-8") as f:
        yaml.dump(all_movies, f, allow_unicode=True)
    print("📁 Kaydedildi: filmjson.yml")


if __name__ == "__main__":
    main()
