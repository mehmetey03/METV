import requests
from bs4 import BeautifulSoup
import json
import time
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ------------------------------
# DOMAIN BULMA
# ------------------------------
def find_active_domain():
    """
    Aktif domain'i otomatik bulur (34, 35, 36 vb.)
    """
    for i in range(34, 45):  # 34'ten 44'e kadar dene
        test_domain = f"https://dizipall{i}.com"
        try:
            print(f"🔍 Testing: {test_domain}")
            response = requests.get(test_domain, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                print(f"✓ Active domain found: {test_domain}")
                return test_domain
        except:
            continue
    
    # Eğer bulunamazsa, en son bilinen domain'i dene
    fallback = "https://dizipall34.com"
    print(f"⚠ No active domain found, using fallback: {fallback}")
    return fallback

# Aktif domain'i bul
BASE = find_active_domain()
print(f"🌐 Using domain: {BASE}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ------------------------------
# HTML çekme
# ------------------------------
def get_html(url, retries=3):
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=15)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 404:
                print(f"❌ 404 Not Found: {url}")
                return ""
            else:
                print(f"⚠ Status {r.status_code} for {url}, retry {attempt+1}")
                time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"⚠ Connection error for {url}: {e}, retry {attempt+1}")
            time.sleep(1)
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
    
    # 1. iframe kontrolü
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = 'https://dizipal.website' + src
        return src
    
    # 2. Video player div'i
    video_div = soup.find(attrs={"data-video-id": True})
    if video_div and video_div.get('data-video-id'):
        video_id = video_div['data-video-id']
        return f"https://dizipal.website/{video_id}"
    
    # 3. Video tag'i
    video_tag = soup.find('video')
    if video_tag and video_tag.get('src'):
        src = video_tag['src']
        if src.startswith('//'):
            src = 'https:' + src
        return src
    
    # 4. JavaScript içinde embed URL arama
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            patterns = [
                r'src\s*[=:]\s*["\'](https?://[^"\']*\.(mp4|m3u8)[^"\']*)["\']',
                r'embedUrl\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                r'videoUrl\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                r'file\s*[=:]\s*["\'](https?://[^"\']+)["\']'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                if matches:
                    url = matches[0][0] if isinstance(matches[0], tuple) else matches[0]
                    if 'dizipal' in url or 'video' in url or 'mp4' in url or 'm3u8' in url:
                        return url
    
    # 5. Fallback: slug'dan hash oluştur
    slug = detail_url.rstrip('/').split('/')[-1]
    if slug:
        return f"https://dizipal.website/{hashlib.md5(slug.encode()).hexdigest()[:13]}"
    
    return ""

# ------------------------------
# Film scraping
# ------------------------------
def scrape_page(page=1):
    url = f"{BASE}/filmler" if page == 1 else f"{BASE}/filmler/{page}"
    print(f"→ Page {page}: {url}")
    
    html = get_html(url)
    if not html:
        print(f"⚠ Could not fetch HTML for page {page}")
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Film container'larını bul
    containers = soup.select('li.w-1\\/2')
    if not containers:
        containers = soup.find_all(class_=lambda x: x and 'w-1/2' in str(x))
    
    if not containers:
        print(f"❌ No movie containers found on page {page}")
        return []
    
    movies = []
    for container in containers:
        try:
            # Başlık
            title_elem = container.find(['h2', 'h3', 'h4'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Yıl
            year_elem = container.find(class_=lambda x: x and 'year' in str(x).lower())
            year = year_elem.get_text(strip=True) if year_elem else ""
            
            # Tür
            genre_elem = container.find(class_=lambda x: x and 'title' in str(x))
            genre = genre_elem.get('title', '') if genre_elem else ""
            
            # Resim
            img = ""
            img_elem = container.find('img')
            if img_elem:
                src = img_elem.get('data-src') or img_elem.get('src') or ""
                if src:
                    if src.startswith('//'):
                        img = 'https:' + src
                    elif src.startswith('/'):
                        img = BASE + src
                    elif not src.startswith('http'):
                        img = BASE + '/' + src
                    else:
                        img = src
            
            # Detay URL
            detail_url = ""
            link_elem = container.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href and '/film/' in href:
                    if href.startswith('/'):
                        detail_url = BASE + href
                    elif href.startswith('http'):
                        detail_url = href
            
            if title and detail_url:
                movies.append({
                    "title": title,
                    "year": year,
                    "genre": genre,
                    "image": img,
                    "detail_url": detail_url,
                    "embed_url": ""
                })
        except Exception as e:
            print(f"⚠ Error processing movie: {e}")
            continue
    
    return movies

# ------------------------------
# Embed URL'leri paralel al
# ------------------------------
def fill_embed_urls(movies):
    if not movies:
        return
    
    print(f"  ↳ Fetching embed URLs for {len(movies)} movies...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for movie in movies:
            if movie.get('detail_url'):
                futures[executor.submit(get_embed_url, movie['detail_url'])] = movie
        
        completed = 0
        for future in as_completed(futures):
            movie = futures[future]
            try:
                movie['embed_url'] = future.result(timeout=10)
                completed += 1
                if completed % 10 == 0:
                    print(f"    {completed}/{len(movies)} embed URLs fetched")
            except Exception as e:
                movie['embed_url'] = ""
                print(f"⚠ Error fetching embed URL: {e}")
    
    print(f"  ✓ {completed}/{len(movies)} embed URLs fetched")

# ------------------------------
# Maksimum sayfa sayısını bul
# ------------------------------
def get_max_pages():
    url = f"{BASE}/filmler"
    html = get_html(url)
    if not html:
        return 158  # Fallback
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Sayfa numaralarını bul
    page_links = soup.select('a[href*="/filmler/"]')
    max_page = 1
    
    for link in page_links:
        href = link.get('href', '')
        if href:
            match = re.search(r'/filmler/(\d+)', href)
            if match:
                page_num = int(match.group(1))
                if page_num > max_page:
                    max_page = page_num
    
    # Son sayfa linkini kontrol et
    pagination = soup.find(class_='pagination')
    if pagination:
        last_page = pagination.find_all('a')[-1]
        if last_page and last_page.get_text(strip=True).isdigit():
            max_page = max(max_page, int(last_page.get_text(strip=True)))
    
    print(f"📊 Detected {max_page} pages")
    return max_page

# ------------------------------
# Tüm sayfaları çek
# ------------------------------
def scrape_all():
    print(f"\n🚀 Starting scraping from: {BASE}")
    
    max_pages = get_max_pages()
    print(f"📚 Total pages to scrape: {max_pages}\n")
    
    all_movies = []
    
    for page in range(1, max_pages + 1):
        start_time = time.time()
        
        movies = scrape_page(page)
        if not movies:
            print(f"⚠ No movies found on page {page}, stopping...")
            break
        
        fill_embed_urls(movies)
        all_movies.extend(movies)
        
        elapsed = time.time() - start_time
        print(f"✓ Page {page}: {len(movies)} movies added (Total: {len(all_movies)}) in {elapsed:.1f}s\n")
        
        # Sayfalar arası bekleme
        if page % 5 == 0:
            time.sleep(1)
        else:
            time.sleep(0.3)
    
    return all_movies

# ------------------------------
# JSON kaydet
# ------------------------------
def save_to_json(data, filename="film.json"):
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # İstatistikler
        with_embed = sum(1 for movie in data if movie.get('embed_url'))
        
        print(f"\n💾 Saved to {file_path}")
        print(f"📊 Total movies: {len(data)}")
        print(f"🎬 Movies with embed URL: {with_embed}/{len(data)} ({with_embed/len(data)*100:.1f}%)")
        
        return True
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("🎬 DIZIPAL FILM SCRAPER")
    print("=" * 50)
    
    movies = scrape_all()
    
    if movies:
        save_to_json(movies)
        print("\n✅ Scraping completed successfully!")
    else:
        print("\n❌ No movies were scraped!")
    
    print("=" * 50)
