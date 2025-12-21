import requests
from bs4 import BeautifulSoup
import json
import time
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ------------------------------
# DOMAIN BULMA - GÜNCELLENMİŞ
# ------------------------------
def find_active_domain():
    """
    Aktif domain'i otomatik bulur
    """
    # Önce en güncel olabilecek domain'leri test et
    possible_domains = [
        "https://dizipal1.com",  # Yeni format
        "https://dizipal2.com",
        "https://dizipal3.com",
        "https://dizipal4.com",
        "https://dizipal5.com",
        "https://dizipal6.com",
        "https://dizipall1.com",
        "https://dizipall2.com",
        "https://dizipall3.com",
        "https://dizipall4.com",
        "https://dizipall5.com",
        "https://dizipall6.com",
        "https://dizipal.com",  # Ana domain
        "https://www.dizipal.com",
    ]
    
    # Eski numaralı domain'leri de ekle
    for i in range(30, 45):
        possible_domains.append(f"https://dizipall{i}.com")
        possible_domains.append(f"https://dizipal{i}.com")
    
    print("🔍 Searching for active domain...")
    
    for domain in possible_domains:
        try:
            print(f"  Testing: {domain}")
            response = requests.get(domain, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                # Sayfanın gerçekten Dizipal olup olmadığını kontrol et
                if "dizipal" in response.text.lower() or "film" in response.text.lower():
                    print(f"✓ Active domain found: {domain}")
                    return domain
        except:
            continue
    
    # Google'dan bulmaya çalış
    print("⚠ Trying to find domain via search...")
    try:
        search_url = "https://www.google.com/search"
        params = {"q": "dizipal film izle"}
        response = requests.get(search_url, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/url?q=' in href:
                    url = href.split('/url?q=')[1].split('&')[0]
                    if 'dizipal' in url and 'http' in url:
                        print(f"✓ Found via search: {url}")
                        return url.split('?')[0]  # Query parametrelerini temizle
    except:
        pass
    
    # Son çare
    fallback = "https://dizipal1.com"
    print(f"⚠ Using fallback domain: {fallback}")
    return fallback

# Aktif domain'i bul
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive"
}

BASE = find_active_domain()
print(f"🌐 Using domain: {BASE}")

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ------------------------------
# HTML çekme
# ------------------------------
def get_html(url, retries=2):
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=10)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 403:
                print(f"❌ 403 Forbidden: {url}")
                return ""
            elif r.status_code == 404:
                print(f"❌ 404 Not Found: {url}")
                return ""
            else:
                print(f"⚠ Status {r.status_code} for {url}")
                time.sleep(1)
        except Exception as e:
            print(f"⚠ Error for {url}: {e}")
            time.sleep(1)
    return ""

# ------------------------------
# Film scraping - GÜNCELLENMİŞ
# ------------------------------
def scrape_page(page=1):
    if page == 1:
        url = f"{BASE}/filmler"
    else:
        url = f"{BASE}/filmler?page={page}"  # Farklı sayfa formatı
    
    print(f"→ Page {page}: {url}")
    
    html = get_html(url)
    if not html:
        # Alternatif URL formatını dene
        alt_url = f"{BASE}/filmler/{page}" if page > 1 else f"{BASE}/filmler"
        print(f"  Trying alternative URL: {alt_url}")
        html = get_html(alt_url)
        if not html:
            return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Birden fazla container pattern'i dene
    containers = []
    
    # Pattern 1: CSS selector
    selectors = [
        '.film-list .film-item',
        '.movies .movie',
        '.film-container',
        '.movie-list',
        'article',
        'div[class*="film"]',
        'div[class*="movie"]',
        'li[class*="film"]'
    ]
    
    for selector in selectors:
        containers = soup.select(selector)
        if containers:
            print(f"  Found {len(containers)} containers with selector: {selector}")
            break
    
    # Pattern 2: Class adına göre
    if not containers:
        containers = soup.find_all(class_=lambda x: x and any(
            keyword in str(x).lower() 
            for keyword in ['film', 'movie', 'poster', 'item', 'card']
        ))
    
    if not containers:
        # Tüm div'leri kontrol et
        print("  Checking all div elements...")
        all_divs = soup.find_all('div')
        for div in all_divs:
            # Film içeriği olan div'leri bul
            if div.find('a') and (div.find('img') or div.find('h2') or div.find('h3')):
                containers.append(div)
    
    if not containers:
        print(f"❌ No movie containers found on page {page}")
        # HTML'yi debug için kaydet
        debug_file = f"debug_page_{page}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html[:5000])  # İlk 5000 karakter
        print(f"  Saved HTML snippet to {debug_file}")
        return []
    
    movies = []
    for container in containers[:50]:  # İlk 50 container'ı al (limit)
        try:
            # Başlık bul
            title = ""
            for tag in ['h2', 'h3', 'h4', 'h5', 'span']:
                title_elem = container.find(tag)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 2:
                        break
            
            # Detay URL bul
            detail_url = ""
            for link in container.find_all('a', href=True):
                href = link['href']
                if href and ('/film/' in href or '/movie/' in href or '/dizi/' in href):
                    if href.startswith('/'):
                        detail_url = BASE + href
                    elif href.startswith('http'):
                        detail_url = href
                    else:
                        detail_url = BASE + '/' + href
                    break
            
            # Resim bul
            img = ""
            img_elem = container.find('img')
            if img_elem:
                for attr in ['data-src', 'src', 'data-lazy-src']:
                    src = img_elem.get(attr)
                    if src:
                        if src.startswith('//'):
                            img = 'https:' + src
                        elif src.startswith('/'):
                            img = BASE + src
                        elif not src.startswith('http'):
                            img = BASE + '/' + src
                        else:
                            img = src
                        break
            
            # Yıl ve Tür bilgileri
            year = ""
            genre = ""
            
            # Container içindeki tüm text'leri analiz et
            all_text = container.get_text(' ', strip=True)
            words = all_text.split()
            for i, word in enumerate(words):
                # Yıl kontrolü (4 haneli sayı)
                if word.isdigit() and len(word) == 4 and 1900 <= int(word) <= 2024:
                    year = word
                # Tür kontrolü
                if word.lower() in ['aksiyon', 'drama', 'komedi', 'korku', 'romantik', 'bilim', 'fantastik']:
                    genre = word
            
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
            continue
    
    return movies

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
        return src
    
    # 2. Video sources
    video = soup.find('video')
    if video:
        source = video.find('source')
        if source and source.get('src'):
            return source['src']
    
    return ""

# ------------------------------
# Maksimum sayfa sayısını bul
# ------------------------------
def get_max_pages():
    url = f"{BASE}/filmler"
    html = get_html(url)
    if not html:
        return 1  # Sadece ilk sayfa
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Pagination bul
    pagination = soup.find(class_='pagination')
    if pagination:
        links = pagination.find_all('a')
        if links:
            last_link = links[-1]
            if last_link.get_text(strip=True).isdigit():
                return int(last_link.get_text(strip=True))
    
    return 1

# ------------------------------
# Tüm sayfaları çek
# ------------------------------
def scrape_all():
    print(f"\n🚀 Starting scraping from: {BASE}")
    
    max_pages = get_max_pages()
    print(f"📚 Will try up to {max_pages} pages\n")
    
    all_movies = []
    
    for page in range(1, max_pages + 1):
        if len(all_movies) >= 1000:  # Maksimum 1000 film
            print("⚠ Reached maximum limit of 1000 movies")
            break
            
        start_time = time.time()
        movies = scrape_page(page)
        
        if not movies:
            print(f"⚠ No movies on page {page}, stopping")
            break
        
        # Embed URL'leri al
        print(f"  ↳ Fetching embed URLs for {len(movies)} movies...")
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for movie in movies:
                futures.append(executor.submit(get_embed_url, movie['detail_url']))
            
            for i, future in enumerate(futures):
                try:
                    movies[i]['embed_url'] = future.result(timeout=5)
                except:
                    movies[i]['embed_url'] = ""
        
        all_movies.extend(movies)
        elapsed = time.time() - start_time
        
        print(f"✓ Page {page}: {len(movies)} movies (Total: {len(all_movies)}) in {elapsed:.1f}s\n")
        
        # Bekle
        time.sleep(1)
        
        # İlk 3 sayfadan sonra dur (test için)
        if page >= 3:
            print("⚠ Stopping after 3 pages for testing")
            break
    
    return all_movies

# ------------------------------
# JSON kaydet
# ------------------------------
def save_to_json(data, filename="film.json"):
    if not data:
        print("❌ No data to save!")
        return False
    
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved {len(data)} movies to {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("🎬 DIZIPAL FILM SCRAPER v2")
    print("=" * 50)
    
    movies = scrape_all()
    
    if movies:
        if save_to_json(movies):
            print("\n✅ Scraping completed successfully!")
    else:
        print("\n❌ No movies were scraped!")
    
    print("=" * 50)
