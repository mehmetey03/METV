import requests
import re
import json
import time

BASE = "https://dizipall30.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Encoding": "gzip"
}


# -----------------------------------------
# FAST REQUEST
# -----------------------------------------
def fast_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            return r.text
    except:
        return ""
    return ""


# -----------------------------------------
# EMBED ÇÖZÜCÜ (PHP'DEKİYLE AYNI)
# -----------------------------------------
def get_embed_fast(detail_url):
    html = fast_get(detail_url)
    if not html:
        return ""

    # <iframe src="">
    m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    if m:
        src = m.group(1)
        if not src.startswith("http"):
            src = "https://dizipal.website" + src
        return src

    # data-video-id
    m = re.search(r'data-video-id=["\']([A-Za-z0-9]+)', html)
    if m:
        return "https://dizipal.website/" + m.group(1)

    # direkt dizipal.website linki
    m = re.search(r'(https?://dizipal\.website/[A-Za-z0-9]+)', html)
    if m:
        return m.group(1)

    # fallback slug → md5 → 13 karakter
    slug = detail_url.rstrip("/").split("/")[-1]
    import hashlib
    h = hashlib.md5(slug.encode()).hexdigest()[:13]
    return "https://dizipal.website/" + h


# -----------------------------------------
# TÜM SAYFALARI TARAMA
# -----------------------------------------
def scrape_all_movies():
    page = 1
    all_movies = []

    while True:
        url = f"{BASE}/filmler/{page}"
        print(f"→ Tarama: {url}")

        html = fast_get(url)
        if not html:
            print("❌ Sayfa boş, durduruluyor...")
            break

        # li bloklarını bul
        blocks = re.findall(r'<li class="[^"]*w-1/2[^"]*"[^>]*>(.*?)</li>', html, re.S)

        if len(blocks) == 0:
            print("❌ Film bulunamadı, durduruluyor.")
            break

        for b in blocks:

            # title
            t = re.search(r'<h2[^>]*>(.*?)</h2>', b)
            title = t.group(1).strip() if t else ""

            # year
            y = re.search(r'year[^>]*>(.*?)<', b)
            year = y.group(1).strip() if y else ""

            # genre (title="")
            g = re.search(r'title="([^"]+)"', b)
            genre = g.group(1).strip() if g else ""

            # image
            img = ""
            m = re.search(r'src="(https://dizipall30\.com/uploads/movies/original/[^"]+)"', b)
            if m:
                img = m.group(1)
            else:
                m2 = re.search(r'src="(https://dizipall30\.com/uploads/video/group/original/[^"]+)"', b)
                if m2:
                    img = m2.group(1)

            # detail url
            u = re.search(r'href="(https://dizipall30\.com/film/[^"]+)"', b)
            detail_url = u.group(1) if u else ""

            # embed
            embed = get_embed_fast(detail_url) if detail_url else ""

            all_movies.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": embed
            })

        page += 1
        time.sleep(0.2)  # 0.2 saniye gecikme

    return all_movies


# -----------------------------------------
# JSON KAYIT
# -----------------------------------------
if __name__ == "__main__":
    movies = scrape_all_movies()

    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=4, ensure_ascii=False)

    print(f"\n🎉 Toplam film: {len(movies)}")
    print("💾 film.json kaydedildi!\n")
