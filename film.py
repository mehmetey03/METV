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
def find_active_domain(base_templates, max_attempts=10):
    """
    Aktif domain'i otomatik bulur (34, 35, 36 vb.)
    """
    for domain_template in base_templates:
        for i in range(34, 34 + max_attempts):
            test_domain = domain_template.format(i)
            try:
                print(f"🔍 Testing: {test_domain}")
                response = requests.get(test_domain, headers=HEADERS, timeout=5)
                if response.status_code == 200:
                    print(f"✓ Active domain found: {test_domain}")
                    return test_domain
            except:
                continue
    
    # Eğer bulunamazsa, son bilinen domain'i dene
    fallback = "https://dizipall34.com"
    print(f"⚠ No active domain found, using fallback: {fallback}")
    return fallback

# Domain şablonları
DOMAIN_TEMPLATES = [
    "https://dizipall{}.com",
    "https://dizipal{}.com",
    "https://dizipall{}.net",
    "https://dizipal{}.net"
]

# Aktif domain'i bul
BASE = find_active_domain(DOMAIN_TEMPLATES)
print(f"🌐 Using domain: {BASE}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
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
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"⚠ Connection error for {url}: {e}, retry {attempt+1}")
            time.sleep(2)
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
    
    # Önce iframe kontrolü
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = 'https://dizipal.website' + src
        return src
    
    # Video player div'i
    video_div = soup.find(attrs={"data-video-id": True})
    if video_div and video_div.get('data-video-id'):
        video_id = video_div['data-video-id']
        return f"https://dizipal.website/{video_id}"
    
    # Video tag'i
    video_tag = soup.find('video')
    if video_tag and video_tag.get('src'):
        return video_tag['src']
    
    # JavaScript içinde embed URL arama
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Regex ile URL bulma
            patterns = [
                r'https?://[^\s"\']+\.(mp4|m3u8)[^\s"\']*',
                r'src\s*:\s*["\']([^"\']+video[^"\']*)["\']',
                r'embedUrl\s*:\s*["\']([^"\']+)["\']',
                r'videoUrl\s*:\s*["\']([^"\']+)["\']'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, script.string, re.IGNORECASE)
                if matches:
                    return matches[0] if isinstance(matches[0], str) else matches[0][0]
    
    # Fallback: slug'dan hash oluştur
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
    
    # Farklı container seçenekleri
    selectors = [
        'li.w-1\\/2',
        'div.w-1\\/2',
        '.movie-poster',
        '.film-item',
        '[class*="film"]',
        '[class*="movie"]'
    ]
    
    containers = []
    for selector in selectors:
        containers = soup.select(selector)
        if containers:
            break
    
    if not containers:
        # Class name ile bulma
        containers = soup.find_all(class_=lambda x: x and any(keyword in str(x).lower() 
                           for keyword in ['film', 'movie', 'poster', 'item']))
    
    if not containers:
        print(f"❌ No movie containers found on page {page}")
        return []
    
    movies = []
    for container in containers:
        try:
            # Başlık
            title_elem = container.find(['h2', 'h3', 'h4', 'h5'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Yıl
            year_elem = container.find(class_=lambda x: x and any(keyword in str(x).lower() 
                                   for keyword in ['year', 'yıl', 'date']))
            year = year_elem.get_text(strip=True) if year_elem else ""
            
            # Tür/Genre
            genre_elem = container.find(class_=lambda x: x and any(keyword in str(x).lower() 
                                    for keyword in ['genre', 'tür', 'category', 'type']))
            genre = genre_elem.get_text(strip=True) if genre_elem else ""
            
            # Resim
            img = ""
            img_elem = container.find('img')
            if img_elem:
                src = img_elem.get('data-src') or img_elem.get('src') or img_elem.get('data-lazy-src') or ""
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
                if href and ('/film/' in href or '/movie/' in href):
                    if href.startswith('/'):
                        detail_url = BASE + href
                    elif href.startswith('http'):
                        detail_url = href
            
            if title and detail_url:  # Sadece geçerli filmleri ekle
                movies.append({
                    "title": title,
                    "year": year,
                    "genre": genre,
                    "image": img,
                    "detail_url": detail_url,
                    "embed_url": ""  # Will be filled later
                })
        except Exception as e:
            print(f"⚠ Error processing movie: {e}")
            continue
    
    return movies

# ------------------------------
# Embed URL'leri paralel al
# ------------------------------
def fill_embed_urls(movies, max_workers=5):
    if not movies:
        return
    
    print(f"  ↳ Fetching embed URLs for {len(movies)} movies...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for movie in movies:
            if movie.get('detail_url'):
                futures[executor.submit(get_embed_url, movie['detail_url'])] = movie
        
        completed = 0
        for future in as_completed(futures):
            movie = futures[future]
            try:
                movie['embed_url'] = future.result(timeout=15)
                completed += 1
                if completed % 10 == 0:
                    print(f"    {completed}/{len(movies)} embed URLs fetched")
            except Exception as e:
                movie['embed_url'] = ""
                print(f"⚠ Error fetching embed URL for {movie.get('title', 'unknown')}: {e}")
    
    print(f"  ✓ {completed}/{len(movies)} embed URLs fetched successfully")

# ------------------------------
# Maksimum sayfa sayısını otomatik bul
# ------------------------------
def get_max_pages():
    url = f"{BASE}/filmler"
    html = get_html(url)
    if not html:
        return 158  # Fallback değer
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Sayfa numaralarını bul
    page_links = soup.select('a[href*="/filmler/"]')
    page_numbers = []
    
    for link in page_links:
        href = link.get('href', '')
        if href:
            # URL'den sayfa numarasını çıkar
            match = re.search(r'/filmler/(\d+)', href)
            if match:
                page_numbers.append(int(match.group(1)))
    
    # Sayfa numaralarından en büyüğünü bul
    if page_numbers:
        max_page = max(page_numbers)
        print(f"📊 Detected {max_page} pages")
        return max_page
    
    # Pagination container kontrolü
    pagination = soup.find(class_=lambda x: x and any(keyword in str(x).lower() 
                          for keyword in ['pagination', 'page', 'sayfa']))
    if pagination:
        last_page_link = pagination.find_all('a')[-1]
        if last_page_link and last_page_link.get_text(strip=True).isdigit():
            return int(last_page_link.get_text(strip=True))
    
    return 158  # Varsayılan değer

# ------------------------------
# Tüm sayfaları çek
# ------------------------------
def scrape_all():
    print(f"\n🚀 Starting scraping from: {BASE}")
    
    # Maksimum sayfa sayısını bul
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
        
        # Dinamik bekleme süresi
        time.sleep(0.5 if page % 10 != 0 else 2)
    
    return all_movies

# ------------------------------
# JSON kaydet
# ------------------------------
def save_to_json(data, filename="film.json"):
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        print(f"\n💾 Saved to {file_path}")
        print(f"📊 Total movies: {len(data)}")
        
        # İstatistikler
        with_embed = sum(1 for movie in data if movie.get('embed_url'))
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
    
    # Domain kontrolü
    print(f"\n🌐 Active Domain: {BASE}")
    
    # Filmleri çek
    movies = scrape_all()
    
    # JSON'a kaydet
    if movies:
        save_to_json(movies)
        print("\n✅ Scraping completed successfully!")
    else:
        print("\n❌ No movies were scraped!")
    
    print("=" * 50)
