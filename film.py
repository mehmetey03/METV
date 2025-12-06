import requests
from bs4 import BeautifulSoup
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

BASE = "https://dizipall30.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

def get_html(url):
    """URL'den HTML al"""
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

def get_embed_url(detail_url):
    """Film detay sayfasından embed URL al"""
    if not detail_url:
        return ""

    html = get_html(detail_url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 1) <iframe src="">
    iframe = soup.find("iframe")
    if iframe and iframe.get("src"):
        src = iframe["src"]
        if src.startswith("//"):
            return "https:" + src
        if src.startswith("/"):
            return "https://dizipal.website" + src
        return src

    # 2) data-video-id
    video_div = soup.find(attrs={"data-video-id": True})
    if video_div:
        vid = video_div["data-video-id"]
        return f"https://dizipal.website/{vid}"

    # 3) fallback (md5)
    slug = detail_url.rstrip("/").split("/")[-1]
    return f"https://dizipal.website/{hashlib.md5(slug.encode()).hexdigest()[:13]}"

def get_embed_for_movie(movie):
    movie["embed_url"] = get_embed_url(movie["detail_url"])
    return movie

def scrape_page(page):
    """Bir sayfadaki filmleri çek"""
    print(f"\n→ Sayfa {page} taranıyor...")

    if page == 1:
        url = f"{BASE}/filmler"
    else:
        url = f"{BASE}/filmler/{page}"

    html = get_html(url)
    if not html:
        print("  ⚠ HTML alınamadı")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Film listesi
    containers = soup.select("li.w-1\\/2")

    # Eğer 0 film bulursa durdur
    if not containers:
        print("  ❌ Film bulunamadı, bu sayfa boş.")
        return []

    movies = []

    for box in containers:
        try:
            # Başlık
            title_el = box.find("h2") or box.find("h3") or box.find("h4")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # Detay link
            a = box.find("a", href=True)
            detail_url = ""
            if a:
                href = a["href"]
                if href.startswith("/"):
                    detail_url = BASE + href
                elif href.startswith("http"):
                    detail_url = href

            # Resim
            img_el = box.find("img")
            img = ""
            if img_el:
                img = img_el.get("src") or img_el.get("data-src") or ""

            # Yıl
            year = ""
            year_el = box.find(class_=lambda x: x and "year" in x)
            if year_el:
                year = year_el.get_text(strip=True)

            # Tür
            genre = ""
            genre_el = box.find(class_=lambda x: x and ("genre" in x or "category" in x))
            if genre_el:
                genre = genre_el.get_text(strip=True)

            # Puan
            rating = "0.0"
            rate_el = box.find(class_=lambda x: x and "rating" in x)
            if rate_el:
                import re
                nums = re.findall(r"\d+\.?\d*", rate_el.get_text())
                if nums:
                    rating = nums[0]

            movies.append({
                "title": title,
                "rating": rating,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": ""
            })

            print(f"   ✓ {title[:40]}")

        except Exception as e:
            print(f"   ⚠ HATA: {e}")

    # Embed URL'leri paralelde al
    print(f"  → {len(movies)} embed URL alınıyor...")
    with ThreadPoolExecutor(max_workers=5) as exe:
        futures = [exe.submit(get_embed_for_movie, m) for m in movies]
        for i, future in enumerate(as_completed(futures)):
            try:
                movies[i] = future.result()
            except:
                pass

    return movies

def main():
    print("🎬 DIZIPAL FILM SCRAPER BAŞLADI")
    print("=" * 50)

    all_movies = []

    for page in range(1, 160):   # 10 sayfa tarar
        movies = scrape_page(page)

        if not movies:
            print(f"✗ Sayfa {page} boş → tarama bitti.")
            break

        all_movies.extend(movies)
        print(f"✓ Sayfa {page} tamamlandı → Toplam film: {len(all_movies)}")

        time.sleep(0.5)

    # JSON kaydet
    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(all_movies, f, indent=2, ensure_ascii=False)

    print("=" * 50)
    print(f"🎉 TOPLAM {len(all_movies)} FİLM KAYDEDİLDİ")
    print("💾 film.json oluşturuldu.")

if __name__ == "__main__":
    main()
