import requests
import re
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

BASE = "https://dizipall30.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
})

# Cache klasörü
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_html(url, timeout=10):
    """Hızlı HTML çekme"""
    try:
        response = SESSION.get(url, timeout=timeout)
        if response.status_code == 200 and len(response.text) > 500:
            return response.text
    except Exception as e:
        print(f"⚠ Hata ({url}): {e}")
    return ""

def get_embed_fast(detail_url):
    """Hızlı embed URL çözücü (PHP'deki mantıkla)"""
    html = get_html(detail_url, timeout=8)
    if not html:
        return ""
    
    # 1. iframe'den src al
    iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    if iframe_match:
        src = iframe_match.group(1)
        if src.startswith("//"):
            src = "https:" + src
        elif not src.startswith("http"):
            src = "https://dizipal.website" + src
        return src
    
    # 2. data-video-id'den al
    video_match = re.search(r'data-video-id=["\']([a-zA-Z0-9]+)', html)
    if video_match:
        return f"https://dizipal.website/{video_match.group(1)}"
    
    # 3. dizipal.website linki ara
    embed_match = re.search(r'https?://dizipal\.website/[a-zA-Z0-9]+', html)
    if embed_match:
        return embed_match.group(0)
    
    # 4. Fallback: slug'dan hash oluştur
    slug = detail_url.split('/')[-1] if '/' in detail_url else detail_url
    import hashlib
    hash_md5 = hashlib.md5(slug.encode()).hexdigest()[:13]
    return f"https://dizipal.website/{hash_md5}"

def get_embed_for_movie(movie_data):
    """Thread için embed alma fonksiyonu"""
    if movie_data['detail_url']:
        movie_data['embed_url'] = get_embed_fast(movie_data['detail_url'])
    return movie_data

def scrape_page(page):
    """Tek sayfa scrape et"""
    cache_file = f"{CACHE_DIR}/movies_page_{page}.json"
    
    # Cache kontrolü (1 saat)
    if os.path.exists(cache_file):
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_time < timedelta(hours=1):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
    
    print(f"→ Sayfa {page} çekiliyor...")
    
    # URL oluştur
    if page == 1:
        url = f"{BASE}/filmler"
    else:
        url = f"{BASE}/filmler/{page}"
    
    html = get_html(url, timeout=15)
    if not html:
        return {"status": "error", "msg": "Sayfa çekilemedi", "page": page, "movies": []}
    
    # PHP'deki regex mantığı
    movies = []
    
    # 1. Tüm film bloklarını bul
    pattern = r'<li\s+class="[^"]*w-1/2[^"]*"[^>]*>(.*?)</li>'
    blocks = re.findall(pattern, html, re.DOTALL)
    
    print(f"  • {len(blocks)} film bloğu bulundu")
    
    for i, block in enumerate(blocks):
        # Başlık
        title_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
        if not title_match:
            continue
            
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        
        # Yıl
        year_match = re.search(r'year[^>]*>(.*?)<', block)
        year = year_match.group(1).strip() if year_match else ""
        
        # Tür (title attribute'undan)
        genre_match = re.search(r'title="([^"]+)"', block)
        genre = genre_match.group(1).strip() if genre_match else ""
        
        # Resim - PHP'deki mantıkla
        img = ""
        img_match = re.search(r'src="(https://dizipall30\.com/uploads/movies/original/[^"]+)"', block)
        if img_match:
            img = img_match.group(1)
        else:
            # Fallback: video/group/original
            img_match2 = re.search(r'src="(https://dizipall30\.com/uploads/video/group/original/[^"]+)"', block)
            if img_match2:
                img = img_match2.group(1)
        
        # Detay URL
        url_match = re.search(r'href="(https://dizipall30\.com/film/[^"]+)"', block)
        detail_url = url_match.group(1) if url_match else ""
        
        # Puan (PHP kodunda olmadığı için ekliyoruz)
        rating_match = re.search(r'<span[^>]*class="[^"]*rating[^"]*"[^>]*>.*?</svg>\s*([\d\.]+)', block, re.DOTALL)
        if not rating_match:
            rating_match = re.search(r'<span[^>]*class="rating[^"]*"[^>]*>([^<]*[\d\.]+[^<]*)<', block, re.DOTALL)
        
        rating = "0.0"
        if rating_match:
            num_match = re.search(r'[\d\.]+', rating_match.group(1))
            if num_match:
                rating = num_match.group(0)
        
        movies.append({
            "title": title,
            "rating": rating,
            "year": year,
            "genre": genre,
            "image": img,
            "detail_url": detail_url,
            "embed_url": ""  # Sonra dolduracağız
        })
    
    # Thread ile embed URL'leri paralel al
    print(f"  • Embed URL'leri alınıyor...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_movie = {executor.submit(get_embed_for_movie, movie): movie for movie in movies}
        
        updated_movies = []
        for future in as_completed(future_to_movie):
            try:
                updated_movie = future.result(timeout=10)
                updated_movies.append(updated_movie)
            except Exception as e:
                # Hata olursa orijinal movie'i ekle
                original_movie = future_to_movie[future]
                updated_movies.append(original_movie)
    
    # Sıralamayı koru
    updated_movies.sort(key=lambda x: movies.index(next(m for m in movies if m['title'] == x['title'])))
    
    result = {
        "status": "success",
        "page": page,
        "total": len(updated_movies),
        "movies": updated_movies
    }
    
    # Cache'e kaydet
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except:
        pass
    
    return result

def scrape_all_pages(start_page=1, end_page=158):
    """Tüm sayfaları scrape et"""
    all_movies = []
    
    for page in range(start_page, end_page + 1):
        try:
            result = scrape_page(page)
            
            if result['status'] == 'success' and result['movies']:
                all_movies.extend(result['movies'])
                print(f"✓ Sayfa {page}: {len(result['movies'])} film eklendi (Toplam: {len(all_movies)})")
            else:
                print(f"✗ Sayfa {page}: Film bulunamadı veya hata")
                break  # Sonraki sayfalarda da boşsa döngüyü kır
            
            # Sunucuyu yormamak için
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Sayfa {page} hatası: {e}")
            break
    
    return all_movies

def save_as_json(movies, filename="all_movies.json"):
    """JSON olarak kaydet"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)
    print(f"\n💾 {len(movies)} film {filename} dosyasına kaydedildi")

# API endpoint için
def api_endpoint():
    """PHP API gibi çalışan endpoint"""
    import sys
    
    if len(sys.argv) > 1:
        # Komut satırı argümanı: python script.py 3
        page = int(sys.argv[1])
    else:
        # Web isteği için (GET parametresi)
        import cgi
        params = cgi.FieldStorage()
        page = int(params.getvalue('s', 1))
    
    result = scrape_page(page)
    
    # JSON header'ı
    print("Content-Type: application/json; charset=utf-8\n")
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        # API modu
        api_endpoint()
    else:
        # Normal mod - tüm sayfaları çek
        print("🎬 DIZIPAL FILM SCRAPER - Python")
        print("=" * 40)
        
        # Sadece belirli sayfaları çekmek için
        start_page = 1
        end_page = 10  # Test için 10 sayfa
        
        # Tüm sayfalar için: end_page = 158
        
        print(f"\n📥 Sayfa {start_page} - {end_page} arası çekiliyor...\n")
        
        start_time = time.time()
        all_movies = scrape_all_pages(start_page, end_page)
        end_time = time.time()
        
        print(f"\n{'='*40}")
        print(f"✅ İŞLEM TAMAMLANDI")
        print(f"⏱️  Süre: {end_time - start_time:.2f} saniye")
        print(f"🎬 Toplam film: {len(all_movies)}")
        
        # JSON olarak kaydet
        save_as_json(all_movies, "all_movies.json")
        
        # İlk 5 filmi göster
        print("\n📊 İlk 5 film:")
        for i, movie in enumerate(all_movies[:5]):
            print(f"  {i+1}. {movie['title']} ({movie['year']}) - ⭐{movie['rating']}")
            print(f"     🎭 {movie['genre']}")
            print(f"     🔗 {movie['embed_url'][:50]}...")
            print()
