import requests
from bs4 import BeautifulSoup
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://dizipall30.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

def get_html(url):
    try:
        response = SESSION.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return ""

def get_embed_url(detail_url):
    """Embed URL'sini al"""
    if not detail_url:
        return ""
    
    html = get_html(detail_url)
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. iframe'den al
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = 'https://dizipal.website' + src
        return src
    
    # 2. data-video-id'den al
    video_div = soup.find(attrs={"data-video-id": True})
    if video_div:
        video_id = video_div['data-video-id']
        return f"https://dizipal.website/{video_id}"
    
    # 3. Fallback
    slug = detail_url.rstrip('/').split('/')[-1]
    import hashlib
    return f"https://dizipal.website/{hashlib.md5(slug.encode()).hexdigest()[:13]}"

def scrape_with_bs4(page=1):
    """BeautifulSoup ile scrape et"""
    print(f"→ Sayfa {page} çekiliyor (BeautifulSoup)...")
    
    # URL
    if page == 1:
        url = f"{BASE}/filmler"
    else:
        url = f"{BASE}/filmler/{page}"
    
    html = get_html(url)
    if not html:
        print(f"  ⚠ HTML çekilemedi")
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Önce HTML'nin yapısını anlamaya çalış
    print(f"  • HTML analiz ediliyor...")
    
    # Tüm olası film container'larını bul
    film_containers = []
    
    # 1. w-1/2 class'lı li'leri bul
    film_containers.extend(soup.select('li.w-1\\/2'))
    
    # 2. w-1/2 class'ı olan tüm elementler
    if not film_containers:
        film_containers.extend(soup.find_all(class_=lambda x: x and 'w-1/2' in x))
    
    # 3. /film/ içeren linklerin parent'larını bul
    if not film_containers:
        film_links = soup.find_all('a', href=lambda x: x and '/film/' in x)
        for link in film_links:
            # Link'in parent veya grandparent'ını al
            container = link.find_parent('li') or link.find_parent('div') or link.parent
            if container and container not in film_containers:
                film_containers.append(container)
    
    print(f"  • {len(film_containers)} film container'ı bulundu")
    
    if not film_containers:
        # Debug için HTML'yi kaydet
        with open(f"bs4_debug_page_{page}.html", "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"  ⚠ Film container'ı bulunamadı. HTML kaydedildi.")
        return []
    
    movies = []
    
    for i, container in enumerate(film_containers[:10]):  # İlk 10'u işle
        try:
            # Başlık
            title_elem = container.find(['h2', 'h3', 'h4']) or container.find(class_=lambda x: x and ('title' in str(x) or 'name' in str(x)))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            if not title:
                continue
            
            # Yıl
            year_elem = container.find(class_=lambda x: x and 'year' in str(x))
            year = year_elem.get_text(strip=True) if year_elem else ""
            
            # Tür
            genre_elem = container.find(class_=lambda x: x and ('genre' in str(x) or 'category' in str(x)))
            genre = genre_elem.get('title', '') if genre_elem and genre_elem.get('title') else genre_elem.get_text(strip=True) if genre_elem else ""
            
            # Resim
            img_elem = container.find('img')
            img = ""
            if img_elem:
                img = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            # Detay URL
            detail_url = ""
            link_elem = container.find('a', href=lambda x: x and '/film/' in x)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    detail_url = BASE + href
                elif href.startswith('http'):
                    detail_url = href
            
            # Puan
            rating_elem = container.find(class_=lambda x: x and 'rating' in str(x))
            rating = "0.0"
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                import re
                numbers = re.findall(r'\d+\.?\d*', rating_text)
                if numbers:
                    rating = numbers[0]
            
            movies.append({
                "title": title,
                "rating": rating,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": ""  # Sonra dolduracağız
            })
            
            print(f"    ✓ {title[:30]}...")
            
        except Exception as e:
            print(f"    ⚠ Film {i+1} işlenirken hata: {e}")
    
    # Embed URL'leri paralel al
    print(f"  • {len(movies)} film için embed URL'leri alınıyor...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for movie in movies:
            futures.append(executor.submit(get_embed_for_movie, movie))
        
        for i, future in enumerate(as_completed(futures)):
            try:
                movie = future.result(timeout=10)
                movies[i] = movie
            except:
                pass
    
    print(f"  • {len(movies)} film başarıyla çekildi")
    return movies

def get_embed_for_movie(movie):
    """Thread için embed alma"""
    movie['embed_url'] = get_embed_url(movie['detail_url'])
    return movie

def main():
    print("🎬 DIZIPAL FILM SCRAPER - BeautifulSoup")
    print("=" * 50)
    
    # Önce bir sayfayı test et
    test_movies = scrape_with_bs4(1)
    
    if test_movies:
        print(f"\n✅ TEST BAŞARILI! {len(test_movies)} film bulundu")
        
        # İlk 3 filmi göster
        print("\n📋 İlk 3 film:")
        for i, movie in enumerate(test_movies[:3]):
            print(f"\n{i+1}. {movie['title']}")
            print(f"   ⭐ Puan: {movie['rating']}")
            print(f"   📅 Yıl: {movie['year']}")
            print(f"   🎭 Tür: {movie['genre']}")
            print(f"   🔗 Embed: {movie['embed_url'][:50]}...")
        
        # Kaydet
        with open("bs4_output.json", "w", encoding="utf-8") as f:
            json.dump(test_movies, f, indent=2, ensure_ascii=False)
        print(f"\n💾 bs4_output.json dosyasına kaydedildi")
        
        # Daha fazla sayfa çekmek ister misin?
        print("\n" + "=" * 50)
        print("Daha fazla sayfa çekmek ister misiniz?")
        print("1. Evet, 10 sayfa çek")
        print("2. Hayır, sadece test yeterli")
        
        choice = input("\nSeçiminiz (1/2): ").strip()
        
        if choice == "1":
            all_movies = test_movies.copy()
            
            for page in range(2, 11):
                print(f"\n→ Sayfa {page} çekiliyor...")
                movies = scrape_with_bs4(page)
                
                if movies:
                    all_movies.extend(movies)
                    print(f"✓ Sayfa {page}: {len(movies)} film (Toplam: {len(all_movies)})")
                    time.sleep(0.5)
                else:
                    print(f"✗ Sayfa {page}: Film bulunamadı")
                    break
            
            # Tümünü kaydet
            with open("all_movies_bs4.json", "w", encoding="utf-8") as f:
                json.dump(all_movies, f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*50}")
            print(f"✅ TOPLAM {len(all_movies)} FİLM ÇEKİLDİ")
            print(f"💾 all_movies_bs4.json dosyasına kaydedildi")
        
    else:
        print("\n❌ TEST BAŞARISIZ!")
        print("HTML yapısı değişmiş olabilir.")

if __name__ == "__main__":
    main()
