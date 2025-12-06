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
        print(f"⚠ Hata: {e}")
    return ""

def get_embed_fast(detail_url):
    """Hızlı embed URL çözücü"""
    if not detail_url:
        return ""
    
    html = get_html(detail_url, timeout=8)
    if not html:
        return ""
    
    # 1. iframe'den src al
    iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if iframe_match:
        src = iframe_match.group(1)
        if src.startswith("//"):
            src = "https:" + src
        elif not src.startswith("http"):
            src = "https://dizipal.website" + src
        return src
    
    # 2. data-video-id'den al
    video_match = re.search(r'data-video-id=["\']([a-zA-Z0-9]{10,15})["\']', html, re.IGNORECASE)
    if video_match:
        return f"https://dizipal.website/{video_match.group(1)}"
    
    # 3. dizipal.website linki ara
    embed_match = re.search(r'https?://dizipal\.website/[a-zA-Z0-9]{10,15}', html, re.IGNORECASE)
    if embed_match:
        return embed_match.group(0)
    
    # 4. Fallback
    slug = detail_url.rstrip('/').split('/')[-1]
    import hashlib
    hash_md5 = hashlib.md5(slug.encode()).hexdigest()[:13]
    return f"https://dizipal.website/{hash_md5}"

def get_embed_for_movie(movie_data):
    """Thread için embed alma"""
    movie_data['embed_url'] = get_embed_fast(movie_data['detail_url'])
    return movie_data

def scrape_page(page):
    """Tek sayfa scrape et"""
    cache_file = f"{CACHE_DIR}/movies_page_{page}.json"
    
    # Cache kontrolü
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
    
    movies = []
    
    # GÜNCELLENMİŞ PATTERN - w-1/2 yerine w-1\/2 (escape edilmiş)
    pattern = r'<li\s+class="[^"]*w-1\\/2[^"]*"[^>]*>(.*?)</li>'
    blocks = re.findall(pattern, html, re.DOTALL)
    
    # Eğer yoksa, alternatif pattern dene
    if not blocks:
        pattern = r'<li[^>]*class="[^"]*w-1/2[^"]*"[^>]*>(.*?)</li>'
        blocks = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    # Hala yoksa, tüm li'leri kontrol et
    if not blocks:
        pattern = r'<li[^>]*>(.*?)</li>'
        all_li = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        # Sadece film içeren li'leri filtrele
        for li in all_li:
            if '/film/' in li and 'uploads/movies/' in li:
                blocks.append(li)
    
    print(f"  • {len(blocks)} film bloğu bulundu")
    
    if not blocks:
        # HTML'yi kaydet debug için
        with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(html[:5000])
        return {"status": "error", "msg": "Film bloğu bulunamadı", "page": page, "movies": []}
    
    for block in blocks[:3]:  # İlk 3'ü debug için göster
        print(f"\n  DEBUG Blok (ilk 300 karakter):")
        print(f"  {block[:300]}...")
    
    for block in blocks:
        # Başlık - farklı pattern'ler dene
        title = ""
        title_patterns = [
            r'<h2[^>]*class="truncate"[^>]*>(.*?)</h2>',
            r'<h2[^>]*>(.*?)</h2>',
            r'<h3[^>]*>(.*?)</h3>',
            r'<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, block, re.DOTALL | re.IGNORECASE)
            if match:
                title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                break
        
        if not title:
            continue
        
        # Yıl
        year = ""
        year_match = re.search(r'<span[^>]*class="[^"]*year[^"]*"[^>]*>([^<]+)</span>', block, re.IGNORECASE)
        if year_match:
            year = year_match.group(1).strip()
        
        # Tür
        genre = ""
        genre_match = re.search(r'<p[^>]*class="truncate"[^>]*title="([^"]+)"', block, re.IGNORECASE)
        if not genre_match:
            genre_match = re.search(r'<p[^>]*class="truncate"[^>]*>([^<]+)</p>', block, re.DOTALL | re.IGNORECASE)
        if genre_match:
            genre = genre_match.group(1).strip()
            genre = re.sub(r'<[^>]+>', '', genre)
        
        # Resim
        img = ""
        img_patterns = [
            r'src="(https://dizipall30\.com/uploads/movies/original/[^"]+\.webp)"',
            r'data-src="(https://dizipall30\.com/uploads/movies/original/[^"]+\.webp)"',
            r'src="(https://dizipall30\.com/uploads/movies/[^"]+)"',
        ]
        
        for pattern in img_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                img = match.group(1)
                break
        
        # Detay URL
        detail_url = ""
        url_patterns = [
            r'href="(https://dizipall30\.com/film/[^"]+)"',
            r'href="(/film/[^"]+)"',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                detail_url = match.group(1)
                if detail_url.startswith("/"):
                    detail_url = BASE + detail_url
                break
        
        # Puan
        rating = "0.0"
        rating_patterns = [
            r'<span[^>]*class="[^"]*rating[^"]*"[^>]*>.*?</svg>\s*([\d\.]+)',
            r'<span[^>]*class="rating[^"]*"[^>]*>([^<]*[\d\.]+[^<]*)<',
            r'<div[^>]*class="[^"]*rating[^"]*"[^>]*>([^<]*[\d\.]+[^<]*)<',
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, block, re.DOTALL | re.IGNORECASE)
            if match:
                num_match = re.search(r'[\d\.]+', match.group(1))
                if num_match:
                    rating = num_match.group(0)
                break
        
        movies.append({
            "title": title,
            "rating": rating,
            "year": year,
            "genre": genre,
            "image": img,
            "detail_url": detail_url,
            "embed_url": ""  # Sonra dolduracağız
        })
    
    # Embed URL'leri paralel al
    print(f"  • {len(movies)} film için embed URL'leri alınıyor...")
    
    # Thread sayısını sınırla
    max_workers = min(10, len(movies))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_movie = {executor.submit(get_embed_for_movie, movie): movie for movie in movies}
        
        updated_movies = []
        completed = 0
        for future in as_completed(future_to_movie):
            completed += 1
            if completed % 5 == 0:
                print(f"    {completed}/{len(movies)} embed tamamlandı")
            
            try:
                updated_movie = future.result(timeout=15)
                updated_movies.append(updated_movie)
            except Exception as e:
                original_movie = future_to_movie[future]
                updated_movies.append(original_movie)
    
    # Orijinal sıraya göre sırala
    title_to_movie = {m['title']: m for m in updated_movies}
    final_movies = []
    for orig_movie in movies:
        if orig_movie['title'] in title_to_movie:
            final_movies.append(title_to_movie[orig_movie['title']])
    
    result = {
        "status": "success",
        "page": page,
        "total": len(final_movies),
        "movies": final_movies
    }
    
    # Cache'e kaydet
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠ Cache kaydedilemedi: {e}")
    
    return result

def test_scraper():
    """Sadece test için"""
    print("🧪 Scraper test ediliyor...")
    
    # Test için 1. sayfa
    result = scrape_page(1)
    
    if result['status'] == 'success' and result['movies']:
        print(f"\n✅ TEST BAŞARILI!")
        print(f"📊 {len(result['movies'])} film bulundu")
        
        print("\n📋 İlk 5 film:")
        for i, movie in enumerate(result['movies'][:5]):
            print(f"\n{i+1}. {movie['title']}")
            print(f"   ⭐ Puan: {movie['rating']}")
            print(f"   📅 Yıl: {movie['year']}")
            print(f"   🎭 Tür: {movie['genre']}")
            print(f"   🖼️  Resim: {movie['image'][:50]}...")
            print(f"   🔗 Embed: {movie['embed_url'][:50]}...")
        
        # Tümünü JSON'a kaydet
        with open("test_output.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 test_output.json dosyasına kaydedildi")
        
        return True
    else:
        print(f"\n❌ TEST BAŞARISIZ!")
        print(f"Mesaj: {result.get('msg', 'Bilinmeyen hata')}")
        
        # Debug dosyalarını kontrol et
        if os.path.exists("debug_page_1.html"):
            print("\n📄 Debug HTML dosyası oluşturuldu: debug_page_1.html")
        
        return False

if __name__ == "__main__":
    print("🎬 DIZIPAL FILM SCRAPER - Python")
    print("=" * 50)
    
    # Önce test et
    if test_scraper():
        print("\n" + "=" * 50)
        print("🎉 Test başarılı! Tüm sayfaları çekmek ister misiniz?")
        print("1. Evet, tüm sayfaları çek (1-158)")
        print("2. Hayır, sadece test yeterli")
        
        choice = input("\nSeçiminiz (1/2): ").strip()
        
        if choice == "1":
            print("\n📥 Tüm sayfalar çekiliyor...")
            
            all_movies = []
            start_time = time.time()
            
            for page in range(1, 159):  # 1-158
                try:
                    result = scrape_page(page)
                    
                    if result['status'] == 'success' and result['movies']:
                        all_movies.extend(result['movies'])
                        print(f"✓ Sayfa {page}: {len(result['movies'])} film (Toplam: {len(all_movies)})")
                    else:
                        print(f"✗ Sayfa {page}: {result.get('msg', 'Film yok')}")
                        if page > 5:  # İlk 5 sayfadan sonra boşsa dur
                            break
                    
                    # Bekle
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"✗ Sayfa {page} hatası: {e}")
                    break
            
            end_time = time.time()
            
            print(f"\n{'='*50}")
            print(f"✅ İŞLEM TAMAMLANDI")
            print(f"⏱️  Süre: {end_time - start_time:.2f} saniye")
            print(f"🎬 Toplam film: {len(all_movies)}")
            
            # JSON olarak kaydet
            with open("all_movies.json", "w", encoding="utf-8") as f:
                json.dump(all_movies, f, indent=2, ensure_ascii=False)
            print(f"💾 all_movies.json dosyasına kaydedildi")
        else:
            print("\n👋 Çıkılıyor...")
    else:
        print("\n⚠ Scraper düzeltilmesi gerekiyor!")
