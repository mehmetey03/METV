import requests
from bs4 import BeautifulSoup
import json
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://dizipall30.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})


# -------------------------------
# HTML ÇEKME
# -------------------------------
def get_html(url):
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""


# -------------------------------
# EMBED URL ÇÖZÜCÜ
# -------------------------------
def get_embed_url(detail_url):
    if not detail_url:
        return ""
    html = get_html(detail_url)
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')

    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = 'https://dizipal.website' + src
        return src

    video_div = soup.find(attrs={"data-video-id": True})
    if video_div:
        video_id = video_div['data-video-id']
        return f"https://dizipal.website/{video_id}"

    direct = soup.find('a', href=lambda x: x and 'dizipal.website/' in x)
    if direct:
        return direct['href']

    slug = detail_url.rstrip('/').split('/')[-1]
    h = hashlib.md5(slug.encode()).hexdigest()[:13]
    return f"https://dizipal.website/{h}"


# -------------------------------
# SAYFA SCRAPE
# -------------------------------
def scrape_page(page=1):
    url = f"{BASE}/filmler" if page == 1 else f"{BASE}/filmler/{page}"
    print(f"→ Sayfa {page} çekiliyor: {url}")
    html = get_html(url)
    if not html:
        print("  ⚠ HTML çekilemedi")
        return []

    soup = BeautifulSoup(html, 'html.parser')

    # Film container'ları
    containers = soup.select('li.w-1\\/2')
    if not containers:
        containers = soup.find_all(class_=lambda x: x and 'w-1/2' in x)

    if not containers:
        print(f"❌ Film kutusu yok → Durdu.")
        with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        return []

    movies = []
    for box in containers:
        try:
            title_el = box.find(["h2", "h3", "h4"])
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            # Detay link
            a = box.find("a", href=lambda x: x and '/film/' in x)
            detail_url = ""
            if a:
                href = a["href"]
                if href.startswith('/'):
                    detail_url = BASE + href
                elif href.startswith('http'):
                    detail_url = href

            # Resim URL (doğru)
            img = ""
            img_tag = box.find('img', src=lambda x: x and '/uploads/movies/original/' in x)
            if img_tag:
                img = img_tag['src']
            else:
                # fallback /uploads/video/group/original/
                img_tag2 = box.find('img', src=lambda x: x and '/uploads/video/group/original/' in x)
                if img_tag2:
                    img = img_tag2['src']

            # Yıl
            year_el = box.find(class_=lambda x: x and 'year' in x)
            year = year_el.get_text(strip=True) if year_el else ""

            # Tür
            genre_el = box.find(class_=lambda x: x and ('genre' in x or 'category' in x))
            genre = ""
            if genre_el:
                genre = genre_el.get('title', '') or genre_el.get_text(strip=True)

            # Puan
            rating = "0.0"
            rate_el = box.find(class_=lambda x: x and "rating" in x)
            if rate_el:
                import re
                numbers = re.findall(r"\d+\.?\d*", rate_el.get_text())
                if numbers:
                    rating = numbers[0]

            movies.append({
                "title": title,
                "rating": rating,
                "year": year,
                "genre": genre,
                "image": img,  # doğru resim URL
                "detail_url": detail_url,
                "embed_url": ""  # sonra doldurulacak
            })

        except Exception as e:
            print(f"⚠ Hata: {e}")

    # Embed URL paralel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(lambda m: {**m, "embed_url": get_embed_url(m["detail_url"])}, movie): movie for movie in movies}
        for future in as_completed(futures):
            try:
                movie = future.result()
                for i, m in enumerate(movies):
                    if m["detail_url"] == movie["detail_url"]:
                        movies[i] = movie
                        break
            except:
                pass

    print(f"  • {len(movies)} film çekildi")
    return movies


# -------------------------------
# TÜM SAYFALARI ÇEK
# -------------------------------
def scrape_all(max_pages=50):
    all_movies = []
    for page in range(1, max_pages + 1):
        movies = scrape_page(page)
        if not movies:
            break
        all_movies.extend(movies)
        time.sleep(0.3)
    return all_movies


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    print("🎬 DIZIPAL FILM SCRAPER")
    movies = scrape_all(max_pages=50)

    # JSON kaydet
    with open("film.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Toplam film: {len(movies)}")
    print("💾 film.json kaydedildi!")
