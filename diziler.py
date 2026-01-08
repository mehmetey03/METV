import requests
from bs4 import BeautifulSoup
import json
import time
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://dizipall35.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ------------------------------
# HTML çekme
# ------------------------------
def get_html(url):
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

# ------------------------------
# Embed URL çözme
# ------------------------------
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

# ------------------------------
# Dizi sayfa scraping
# ------------------------------
def scrape_page(page=1):
    url = f"{BASE}/diziler" if page == 1 else f"{BASE}/diziler/{page}"
    print(f"→ DİZİLER | Sayfa {page}: {url}")

    html = get_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.select('li.w-1\\/2')
    if not containers:
        containers = soup.find_all(class_=lambda x: x and 'w-1/2' in x)
    if not containers:
        return []

    series = []
    for container in containers:
        try:
            title_elem = container.find(['h2', 'h3', 'h4'])
            title = title_elem.get_text(strip=True) if title_elem else ""

            year_elem = container.find(class_=lambda x: x and 'year' in x)
            year = year_elem.get_text(strip=True) if year_elem else ""

            genre_elem = container.find(class_=lambda x: x and 'title' in x)
            genre = genre_elem.get('title', '') if genre_elem else ""

            img = ""
            for img_elem in container.find_all('img'):
                src = img_elem.get('data-src') or img_elem.get('src') or ""
                if 'uploads' in src:
                    if src.startswith('//'):
                        img = 'https:' + src
                    elif src.startswith('/'):
                        img = BASE + src
                    else:
                        img = src
                    break

            link_elem = container.find('a', href=True)
            detail_url = ""
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    detail_url = BASE + href
                elif href.startswith('http'):
                    detail_url = href

            series.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": ""
            })
        except:
            pass

    return series

# ------------------------------
# Embed URL'leri paralel doldur
# ------------------------------
def fill_embed_urls(series):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_embed_url, s['detail_url']): s for s in series}
        for future in as_completed(futures):
            try:
                futures[future]['embed_url'] = future.result(timeout=10)
            except:
                futures[future]['embed_url'] = ""

# ------------------------------
# Tüm dizileri çek
# ------------------------------
def scrape_all(max_pages=158):
    all_series = []
    for page in range(1, max_pages + 1):
        series = scrape_page(page)
        if not series:
            break
        fill_embed_urls(series)
        all_series.extend(series)
        print(f"✓ Toplam dizi: {len(all_series)}")
        time.sleep(0.2)
    return all_series

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    print("📺 DİZİ SCRAPER BAŞLADI")

    series = scrape_all(158)

    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diziler.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(series, f, indent=2, ensure_ascii=False)

    print("\n✅ TAMAMLANDI")
    print(f"📺 Toplam dizi: {len(series)}")
    print(f"💾 diziler.json kaydedildi → {file_path}")
