#!/usr/bin/env python3
"""
hdch_ultimate_fixed.py - Ultimate HDFilmCehennemi scraper - FIXED VERSION
"""
import urllib.request
import json
import re
import html
import time
import random
import ssl
from datetime import datetime
from urllib.parse import urljoin, quote
from urllib.error import HTTPError, URLError

# SSL sertifika doğrulamasını devre dışı bırak
ssl._create_default_https_context = ssl._create_unverified_context

BASE_URL = "https://www.hdfilmcehennemi.ws/"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url, headers=None):
    """Get HTML content with improved error handling"""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': BASE_URL,
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        # URL'yi güvenli şekilde kodla
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            
            # Kodlamayı otomatik tespit et
            encodings = ['utf-8', 'iso-8859-9', 'windows-1254']
            for encoding in encodings:
                try:
                    return content.decode(encoding, errors='ignore')
                except UnicodeDecodeError:
                    continue
            
            # Hiçbiri çalışmazsa varsayılan
            return content.decode('utf-8', errors='ignore')
            
    except HTTPError as e:
        print(f"    HTTP Error {e.code}: {url}")
        return None
    except URLError as e:
        print(f"    URL Error: {url} - {e.reason}")
        return None
    except Exception as e:
        print(f"    Error fetching {url}: {str(e)[:50]}")
        return None

def find_film_urls_in_html(html_content, base_url):
    """Find all film URLs in HTML content"""
    film_urls = []
    
    if not html_content:
        return film_urls
    
    # Yeni pattern: data-token ile film linkleri
    pattern = r'data-token="\d+"\s+href="([^"]+)"'
    matches = re.findall(pattern, html_content, re.IGNORECASE)
    
    for match in matches:
        if match and not match.startswith('http'):
            full_url = urljoin(base_url, match)
            if '/film/' in full_url.lower() or '/dizi/' in full_url.lower():
                if full_url not in film_urls:
                    film_urls.append(full_url)
    
    # Alternatif pattern: poster class ile
    if not film_urls:
        pattern = r'class="[^"]*poster[^"]*"[^>]*href="([^"]+)"'
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        
        for match in matches:
            if match and not match.startswith('http'):
                full_url = urljoin(base_url, match)
                if full_url not in film_urls:
                    film_urls.append(full_url)
    
    return film_urls

def extract_film_data_from_page(film_url):
    """Extract film data from individual film page"""
    print(f"  Processing: {film_url}")
    html_content = get_html(film_url)
    
    if not html_content:
        return None
    
    film_data = {
        'url': film_url,
        'title': '',
        'year': '',
        'imdb': '0.0',
        'image': '',
        'token': '',
        'embed_url': '',
        'type': 'film',
        'scraped_at': datetime.now().isoformat()
    }
    
    try:
        # 1. Başlığı çıkar
        title_match = re.search(r'<title>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            # Temizle
            title = re.sub(r'\s*-\s*HDFilmCehennemi.*', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*\(?\d{4}\)?', '', title)
            title = re.sub(r'\s*izle\s*', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*HD\s*', '', title, flags=re.IGNORECASE)
            film_data['title'] = title.strip()
        
        # 2. Token'ı çıkar (URL'den veya içerikten)
        token_match = re.search(r'data-token="(\d+)"', html_content)
        if not token_match:
            # URL'den almayı dene
            token_match = re.search(r'-(\d+)/$', film_url)
        
        if token_match:
            film_data['token'] = token_match.group(1)
        
        # 3. Yılı çıkar
        year_match = re.search(r'(\d{4})\s*Yılı', html_content, re.IGNORECASE)
        if not year_match:
            year_match = re.search(r'<span[^>]*>\s*(\d{4})\s*</span>', html_content)
        
        if year_match:
            film_data['year'] = year_match.group(1)
        
        # 4. IMDB puanı
        imdb_match = re.search(r'IMDB[^>]*>.*?(\d+\.\d+)', html_content, re.DOTALL | re.IGNORECASE)
        if not imdb_match:
            imdb_match = re.search(r'imdb[^>]*>.*?(\d+\.\d+)', html_content, re.DOTALL | re.IGNORECASE)
        
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    film_data['imdb'] = f"{rating:.1f}"
            except:
                pass
        
        # 5. Resim URL'si
        img_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html_content, re.IGNORECASE)
        if not img_match:
            img_match = re.search(r'<img[^>]*class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', html_content, re.IGNORECASE)
        
        if img_match:
            film_data['image'] = img_match.group(1)
        
        # 6. Tür belirle
        if '/dizi/' in film_url.lower():
            film_data['type'] = 'dizi'
        
        # 7. EMBED URL'sini çıkar - YENİ VE GELİŞMİŞ METOD
        film_data['embed_url'] = extract_embed_url_advanced(html_content, film_data.get('token', ''))
        
        return film_data
        
    except Exception as e:
        print(f"    Error parsing film data: {str(e)[:50]}")
        return film_data

def extract_embed_url_advanced(html_content, token):
    """Advanced method to extract embed URL"""
    if not html_content:
        return ""
    
    # 1. İlk olarak iframe'leri ara
    iframe_patterns = [
        r'<iframe[^>]*data-src="([^"]+hdfilmcehennemi\.mobi[^"]*)"',
        r'<iframe[^>]*src="([^"]+hdfilmcehennemi\.mobi[^"]*)"',
        r'src="(https?://hdfilmcehennemi\.mobi/video/embed/[^"]*)"',
    ]
    
    for pattern in iframe_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            embed_url = match.group(1)
            if embed_url.startswith('//'):
                embed_url = 'https:' + embed_url
            print(f"    Found embed URL in iframe")
            return embed_url
    
    # 2. Script tag'lerinde ara
    script_pattern = r'<script[^>]*>.*?(https?://hdfilmcehennemi\.mobi/video/embed/[^\'"]+).*?</script>'
    script_match = re.search(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if script_match:
        print(f"    Found embed URL in script")
        return script_match.group(1)
    
    # 3. rapidrame_id ara
    rapidrame_patterns = [
        r'rapidrame_id=([a-zA-Z0-9]+)',
        r'embed/([^/]+)/\?rapidrame_id=([a-zA-Z0-9]+)',
        r'video_id["\']?\s*[:=]\s*["\']([a-zA-Z0-9]+)["\']',
    ]
    
    for pattern in rapidrame_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            video_id = match.group(1) if len(match.groups()) == 1 else match.group(2)
            embed_url = f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={video_id}"
            print(f"    Constructed embed URL from rapidrame_id: {video_id}")
            return embed_url
    
    # 4. Token kullan
    if token:
        embed_url = f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={token}"
        print(f"    Constructed embed URL from token: {token}")
        return embed_url
    
    # 5. data-player-id veya benzeri attribute'lar
    player_pattern = r'data-player-id=["\']([^"\']+)["\']'
    player_match = re.search(player_pattern, html_content, re.IGNORECASE)
    if player_match:
        video_id = player_match.group(1)
        embed_url = f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={video_id}"
        print(f"    Constructed embed URL from player ID: {video_id}")
        return embed_url
    
    return ""

def get_working_list_pages():
    """Get actual working list pages"""
    # TEST İÇİN ÖNCE AZ SAYIDA SAYFA
    return [
        BASE_URL,
        "https://www.hdfilmcehennemi.ws/category/film-izle-2/",
        "https://www.hdfilmcehennemi.ws/category/nette-ilk-filmler/",
        "https://www.hdfilmcehennemi.ws/dil/turkce-dublajli-film-izleyin-4/",
        "https://www.hdfilmcehennemi.ws/yil/2024-filmleri-izle/",
        "https://www.hdfilmcehennemi.ws/yil/2023-filmleri-izle/",
        "https://www.hdfilmcehennemi.ws/tur/aksiyon/",
        "https://www.hdfilmcehennemi.ws/tur/dram/",
        "https://www.hdfilmcehennemi.ws/tur/komedi/",
    ]

def crawl_all_films():
    """Main crawling function"""
    print("=" * 70)
    print("HDFilmCehennemi ULTIMATE SCRAPER")
    print("=" * 70)
    
    all_films = []
    all_urls = set()
    
    # 1. Çalışan sayfaları al
    list_pages = get_working_list_pages()
    
    print("\n1. Film listesi sayfalarını tarıyor...")
    for page_url in list_pages:
        print(f"  Tarıyor: {page_url}")
        
        html_content = get_html(page_url)
        if not html_content:
            continue
        
        # Film URL'lerini bul
        film_urls = find_film_urls_in_html(html_content, BASE_URL)
        
        # Yeni film URL'lerini ekle
        new_urls = [url for url in film_urls if url not in all_urls]
        
        if new_urls:
            print(f"    {len(new_urls)} yeni film bulundu")
            all_urls.update(new_urls)
        else:
            print(f"    Yeni film bulunamadı")
        
        # Kısa bekle
        time.sleep(random.uniform(1, 2))
    
    print(f"\nToplam {len(all_urls)} benzersiz film URL'si bulundu")
    
    # 2. Her film sayfasını işle
    print("\n2. Film detaylarını çekiyor...")
    films_data = []
    
    for i, film_url in enumerate(list(all_urls), 1):
        print(f"  [{i}/{len(all_urls)}]")
        
        film_data = extract_film_data_from_page(film_url)
        if film_data:
            films_data.append(film_data)
        
        # Progress göstergesi
        if i % 10 == 0:
            print(f"    İlerleme: {i}/{len(all_urls)} - Başarılı: {len(films_data)}")
        
        # Rastgele bekleme (anti-ban)
        time.sleep(random.uniform(0.5, 1.5))
    
    return films_data

def save_final_results(films):
    """Save results in required format"""
    if not films:
        print("❌ Kaydedilecek film yok!")
        return
    
    # 1. Sizin JSON formatınıza çevir
    formatted_films = []
    
    for film in films:
        # Embed URL'yi metv formatına çevir
        embed_url = film.get('embed_url', '')
        final_embed_url = ""
        
        if embed_url:
            # rapidrame_id'yi çıkar
            rapidrame_match = re.search(r'rapidrame_id=([a-zA-Z0-9]+)', embed_url)
            if rapidrame_match:
                video_id = rapidrame_match.group(1)
                final_embed_url = f"https://metvmetv33.byethost15.com/hdcehennemi.php?ID={video_id}&video.mp4"
        
        formatted_films.append({
            'title': film.get('title', ''),
            'year': film.get('year', ''),
            'type': film.get('type', 'film'),
            'url': film.get('url', ''),
            'embed_url': final_embed_url if final_embed_url else None,
            'imdb': film.get('imdb', '0.0'),
            'image': film.get('image', ''),
            'token': film.get('token', '')
        })
    
    # 2. JSON dosyasına kaydet
    try:
        with open('hdceh_embeds_final.json', 'w', encoding='utf-8') as f:
            json.dump(formatted_films, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Başarıyla kaydedildi: hdceh_embeds_final.json")
        print(f"   Toplam film: {len(formatted_films)}")
        
        # İstatistikler
        with_embed = sum(1 for f in formatted_films if f.get('embed_url'))
        print(f"   Embed URL'si olan filmler: {with_embed}")
        print(f"   Başarı oranı: %{(with_embed/len(formatted_films)*100):.1f}")
        
    except Exception as e:
        print(f"❌ Kaydetme hatası: {e}")
    
    # 3. Ayrıca tüm detayları da kaydet
    try:
        full_data = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(films),
                'source': 'hdfilmcehennemi.ws'
            },
            'films': films
        }
        
        with open('hdfilms_full_details.json', 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Tam detaylar kaydedildi: hdfilms_full_details.json")
        
    except Exception as e:
        print(f"⚠️ Tam detaylar kaydedilemedi: {e}")

def main():
    """Main function"""
    print("HDFilmCehennemi Scraper - Tüm filmleri çekiyor...")
    print("Bu işlem 30-60 dakika sürebilir...\n")
    
    try:
        # Tüm filmleri çek
        all_films = crawl_all_films()
        
        if not all_films:
            print("\n❌ Hiç film bulunamadı! Site yapısı değişmiş olabilir.")
            return
        
        # Sonuçları kaydet
        save_final_results(all_films)
        
        # Başarı özeti
        print("\n" + "=" * 70)
        print("İŞLEM TAMAMLANDI!")
        print("=" * 70)
        
        # İlk 5 filmi göster
        print("\nİlk 5 film:")
        for i, film in enumerate(all_films[:5], 1):
            title = film.get('title', 'Bilinmeyen')[:50]
            has_embed = "✓" if film.get('embed_url') else "✗"
            print(f"  {i}. {title} [Embed: {has_embed}]")
        
        print(f"\nToplam {len(all_films)} film işlendi.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ İşlem kullanıcı tarafından durduruldu!")
        print("Şu ana kadar işlenen filmler kaydedilecek...")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
