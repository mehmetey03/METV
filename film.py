import requests
from bs4 import BeautifulSoup
import json
import time
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://dizipall30.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# HTML çekme
def get_html(url):
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

# Embed URL çözme
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
        return f"https://dizipal.website/{video_div['data-video-id']}"

    slug = detail_url.rstrip('/').split('/')[-1]
    return f"https://dizipal.website/{hashlib.md5(slug.encode()).hexdigest()[:13]}"

# Sayfa scrape
def scrape_page(page=1):
    url = f"{BASE}/filmler" if page == 1 else f"{BASE}/filmler/{page}"
    print(f"→ Sayfa {page} çekiliyor: {url}")
    html = get_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.select('li.w-1\\/2')
    if not containers:
        containers = soup.find_all(class_=lambda x: x and 'w-1/2' in x)
    if not containers:
        print(f"❌ Film kutusu yok → Durdu.")
        return []

    movies = []
    for container in containers:
        try:
            title_elem = container.find(['h2', 'h3', 'h4'])
            title = title_elem.get_text(strip=True) if title_elem else ""

            year_elem = container.find(class_=lambda x: x and 'year' in x)
            year = year_elem.get_text(strip=True) if year_elem else ""

            genre_elem = container.find(class_=lambda x: x and 'title' in x)
            genre = genre_elem.get('title', '') if genre_elem else ""

            img_elem = container.find('img')
            img = ""
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and 'uploads/movies/original/' in src:
                    img = src
                elif src and 'uploads/video/group/original/' in src:
                    img = src

            link_elem = container.find('a', href=lambda x: x and '/film/' in x)
            detail_url = ""
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    detail_url = BASE + href
                elif href.startswith('http'):
                    detail_url = href

            movies.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": ""  # Sonra doldurulacak
            })
        except:
            continue
    return movies

# Embed URL'leri paralel al
def fill_embed_urls(movies):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_embed_url, m['detail_url']): m for m in movies}
        for future in as_completed(futures):
            movie = futures[future]
            try:
                movie['embed_url'] = future.result(timeout=10)
            except:
                movie['embed_url'] = ""

# Tüm sayfaları çek
def scrape_all(max_pages=50):
    all_movies = []
    for page in range(1, max_pages + 1):
        movies = scrape_page(page)
        if not movies:
            break
        fill_embed_urls(movies)
        all_movies.extend(movies)
        print(f"✓ Sayfa {page}: {len(movies)} film eklendi (Toplam: {len(all_movies)})")
        time.sleep(0.2)
    return all_movies

# MAIN
if __name__ == "__main__":
    print("🎬 DIZIPAL FILM SCRAPER")
    movies = scrape_all(max_pages=50)

    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "film.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)
    print(f"\n🎉 Toplam film: {len(movies)}")
    print(f"💾 film.json kaydedildi! ({file_path})")
