import requests
import re
import json
import time
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

BASE = "https://dizipall30.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
})

# Cache klasörü
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def fast_curl(url):
    """PHP'deki fastCurl fonksiyonunun Python karşılığı"""
    try:
        response = SESSION.get(url, timeout=6)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"⚠ CURL hatası ({url}): {e}")
    return ""

def get_embed_fast(detail_url):
    """PHP'deki getEmbedFast fonksiyonunun Python karşılığı"""
    if not detail_url:
        return ""
    
    html = fast_curl(detail_url)
    if not html:
        return ""
    
    # 1. iframe'den src al
    iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if iframe_match:
        src = iframe_match.group(1)
        # HTML entity decode
        src = src.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#039;', "'")
        
        if not src.startswith("http"):
            src = "https://dizipal.website" + src
        return src
    
    # 2. data-video-id'den al
    video_match = re.search(r'data-video-id=["\']([a-zA-Z0-9]+)', html, re.IGNORECASE)
    if video_match:
        return f"https://dizipal.website/{video_match.group(1)}"
    
    # 3. dizipal.website linki ara
    embed_match = re.search(r'https?://dizipal\.website/[a-zA-Z0-9]+', html, re.IGNORECASE)
    if embed_match:
        return embed_match.group(0)
    
    # 4. Fallback: slug'dan hash oluştur (PHP'deki gibi)
    from urllib.parse import urlparse
    parsed_url = urlparse(detail_url)
    slug = os.path.basename(parsed_url.path)
    hash_md5 = hashlib.md5(slug.encode()).hexdigest()[:13]
    return f"https://dizipal.website/{hash_md5}"

def scrape_page_php_style(page):
    """PHP kodundaki mantıkla aynı şekilde scrape et"""
    cache_file = f"{CACHE_DIR}/movies_page_{page}.json"
    
    # Cache kontrolü (PHP'deki gibi 1 saat)
    if os.path.exists(cache_file):
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_time < timedelta(hours=1):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
    
    print(f"→ Sayfa {page} çekiliyor (PHP mantığıyla)...")
    
    # URL oluştur
    if page == 1:
        url = f"{BASE}/filmler"
    else:
        url = f"{BASE}/filmler/{page}"
    
    html = fast_curl(url)
    
    if not html:
        return {"status": "error", "msg": "Sayfa çekilemedi", "page": page, "movies": []}
    
    movies = []
    
    # PHP'DEKİ AYNI REGEX PATTERN'İ
    # preg_match_all('/<li class="[^"]*w-1\/2[^"]*"[^>]*>(.*?)<\/li>/s', $html, $blocks);
    pattern = r'<li class="[^"]*w-1/2[^"]*"[^>]*>(.*?)</li>'
    blocks = re.findall(pattern, html, re.DOTALL)
    
    print(f"  • {len(blocks)} film bloğu bulundu")
    
    if not blocks:
        # HTML'yi debug için kaydet
        with open(f"php_debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(html[:10000])  # İlk 10k karakter
        print(f"  ⚠ Film bloğu bulunamadı. HTML kaydedildi.")
        return {"status": "error", "msg": "Film bloğu bulunamadı", "page": page, "movies": []}
    
    for i, block in enumerate(blocks):
        # DEBUG: İlk bloğu göster
        if i == 0:
            print(f"\n  DEBUG - İlk blok (ilk 500 karakter):")
            print(f"  {block[:500]}...\n")
        
        # Başlık: preg_match('/<h2[^>]*>(.*?)<\/h2>/', $b, $t);
        title_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.DOTALL)
        if not title_match:
            continue
        
        title = title_match.group(1).strip()
        # HTML tag'larını temizle
        title = re.sub(r'<[^>]+>', '', title)
        
        # Yıl: preg_match('/year[^>]*>(.*?)</', $b, $y);
        year_match = re.search(r'year[^>]*>(.*?)<', block, re.IGNORECASE)
        year = year_match.group(1).strip() if year_match else ""
        
        # Tür: preg_match('/title="([^"]+)"/', $b, $g);
        genre_match = re.search(r'title="([^"]+)"', block)
        genre = genre_match.group(1).strip() if genre_match else ""
        
        # Resim: PHP'deki mantıkla aynı
        img = ""
        # İlk pattern: src="https://dizipall30.com/uploads/movies/original/[^"]+"
        img_match1 = re.search(r'src="(https://dizipall30\.com/uploads/movies/original/[^"]+)"', block)
        if img_match1:
            img = img_match1.group(1)
        else:
            # Fallback pattern: src="https://dizipall30.com/uploads/video/group/original/[^"]+"
            img_match2 = re.search(r'src="(https://dizipall30\.com/uploads/video/group/original/[^"]+)"', block)
            if img_match2:
                img = img_match2.group(1)
        
        # Detay URL: preg_match('/href="(https:\/\/dizipall30\.com\/film\/[^"]+)"/', $b, $u);
        url_match = re.search(r'href="(https://dizipall30\.com/film/[^"]+)"', block)
        detail_url = url_match.group(1) if url_match else ""
        
        # Embed URL (PHP'deki gibi)
        embed_url = ""
        if detail_url:
            embed_url = get_embed_fast(detail_url)
        
        # Puanı da ekleyelim (PHP kodunda yok ama HTML'de var)
        rating = "0.0"
        # PHP'deki rating regex'ini deneyelim
        rating_match = re.search(r'<span[^>]*class="[^"]*rating[^"]*"[^>]*>.*?</svg>\s*([\d\.]+)', block, re.DOTALL)
        if not rating_match:
            rating_match = re.search(r'<span[^>]*class="rating[^"]*"[^>]*>([^<]*[\d\.]+[^<]*)<', block, re.DOTALL)
        
        if rating_match:
            num_match = re.search(r'[\d\.]+', rating_match.group(1))
            if num_match:
                rating = num_match.group(0)
        
        movies.append({
            "title": title,
            "rating": rating,  # PHP'de olmayan ek alan
            "year": year,
            "genre": genre,
            "image": img,
            "detail_url": detail_url,
            "embed_url": embed_url
        })
    
    # PHP çıktısına benzer JSON oluştur
    result = {
        "status": "success",
        "page": page,
        "total": len(movies),
        "movies": movies
    }
    
    # Cache'e kaydet
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  ⚠ Cache kaydedilemedi: {e}")
    
    return result

def test_php_scraper():
    """PHP scraper'ı test et"""
    print("🧪 PHP Scraper test ediliyor...")
    
    result = scrape_page_php_style(2)  # 2. sayfayı test et (örneğiniz 2. sayfa)
    
    if result['status'] == 'success' and result['movies']:
        print(f"\n✅ TEST BAŞARILI!")
        print(f"📊 {len(result['movies'])} film bulundu")
        
        # Örnekteki gibi filmleri göster
        print("\n📋 İlk 3 film:")
        for i, movie in enumerate(result['movies'][:3]):
            print(f"\n{i+1}. {movie['title']}")
            print(f"   📅 Yıl: {movie['year']}")
            print(f"   🎭 Tür: {movie['genre']}")
            print(f"   ⭐ Puan: {movie['rating']}")
            print(f"   🖼️  Resim: {movie['image'][:50]}..." if movie['image'] else "   🖼️  Resim: Yok")
            print(f"   🔗 Embed: {movie['embed_url']}")
        
        # JSON'ı kaydet
        with open("php_test_output.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 php_test_output.json dosyasına kaydedildi")
        return True
    else:
        print(f"\n❌ TEST BAŞARISIZ!")
        print(f"Mesaj: {result.get('msg', 'Bilinmeyen hata')}")
        return False

def scrape_all_pages_parallel(start_page=1, end_page=10):
    """Tüm sayfaları paralel olarak çek"""
    all_results = []
    
    print(f"\n📥 Sayfa {start_page}-{end_page} paralel çekiliyor...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Tüm sayfalar için future'lar oluştur
        future_to_page = {executor.submit(scrape_page_php_style, page): page 
                         for page in range(start_page, end_page + 1)}
        
        completed = 0
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            completed += 1
            
            try:
                result = future.result(timeout=30)
                
                if result['status'] == 'success' and result['movies']:
                    all_results.append(result)
                    print(f"✓ Sayfa {page}: {len(result['movies'])} film")
                else:
                    print(f"✗ Sayfa {page}: {result.get('msg', 'Film yok')}")
                    
            except Exception as e:
                print(f"✗ Sayfa {page} hatası: {e}")
    
    # Tüm filmleri birleştir
    all_movies = []
    for result in all_results:
        if result['status'] == 'success':
            all_movies.extend(result['movies'])
    
    return all_movies

def main():
    print("🎬 DIZIPAL FILM SCRAPER - PHP MANTIĞI")
    print("=" * 50)
    
    # Önce test et
    if test_php_scraper():
        print("\n" + "=" * 50)
        print("PHP scraper çalışıyor! Devam etmek ister misiniz?")
        print("1. Evet, 10 sayfa paralel çek")
        print("2. Evet, tüm sayfaları (1-158) çek")
        print("3. Hayır, çık")
        
        choice = input("\nSeçiminiz (1/2/3): ").strip()
        
        if choice in ["1", "2"]:
            if choice == "1":
                start_page = 1
                end_page = 10
            else:
                start_page = 1
                end_page = 158
            
            start_time = time.time()
            all_movies = scrape_all_pages_parallel(start_page, end_page)
            end_time = time.time()
            
            print(f"\n{'='*50}")
            print(f"✅ İŞLEM TAMAMLANDI")
            print(f"⏱️  Süre: {end_time - start_time:.2f} saniye")
            print(f"🎬 Toplam film: {len(all_movies)}")
            
            # Tüm filmleri kaydet
            filename = f"all_movies_{start_page}_{end_page}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_movies, f, indent=2, ensure_ascii=False)
            
            print(f"💾 {filename} dosyasına kaydedildi")
            
            # İstatistikler
            print("\n📊 İstatistikler:")
            years = {}
            for movie in all_movies:
                year = movie['year']
                if year:
                    years[year] = years.get(year, 0) + 1
            
            print(f"   • Yıllara göre film sayısı:")
            for year in sorted(years.keys())[-5:]:  # Son 5 yıl
                print(f"     {year}: {years[year]} film")
            
        else:
            print("\n👋 Çıkılıyor...")
    else:
        print("\n⚠ PHP scraper çalışmıyor. HTML yapısı değişmiş olabilir.")

if __name__ == "__main__":
    main()
