#!/usr/bin/env python3
"""
hdch_final_ultimate.py - Ultimate HDFilmCehennemi scraper
"""
import urllib.request
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

BASE_URL = "https://www.hdfilmcehennemi.nl/"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url, headers=None):
    """Get HTML content"""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': BASE_URL,
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def extract_films_from_html(html_content, source_url):
    """Extract films from HTML"""
    films = []
    
    if not html_content:
        return films
    
    # Pattern 1: Look for film posters with data-token
    film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
    film_matches = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    for match in film_matches:
        film = parse_film_poster(match, source_url)
        if film:
            films.append(film)
    
    return films

def parse_film_poster(poster_html, source_url):
    """Parse a film poster HTML block"""
    try:
        # URL
        url_match = re.search(r'href="([^"]+)"', poster_html)
        if not url_match:
            return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # Title from title attribute
        title = ''
        title_match = re.search(r'title="([^"]+)"', poster_html)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
        
        # Alternative: from poster-title class
        if not title:
            title_match = re.search(r'class="poster-title"[^>]*>(.*?)</strong>', poster_html, re.DOTALL)
            if title_match:
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                title = html.unescape(title)
        
        if not title:
            return None
        
        # Clean title
        title = clean_title(title)
        
        # Year
        year = ''
        year_match = re.search(r'<span>\s*(\d{4})\s*</span>', poster_html)
        if year_match:
            year = year_match.group(1)
        
        # IMDB rating
        imdb = '0.0'
        imdb_match = re.search(r'class="imdb"[^>]*>.*?(\d+\.\d+)', poster_html, re.DOTALL)
        if not imdb_match:
            imdb_match = re.search(r'<svg[^>]*><path[^>]*></path></svg>\s*<p>\s*(\d+\.\d+)', poster_html, re.DOTALL)
        
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    imdb = f"{rating:.1f}"
            except:
                pass
        
        # Image
        image = ''
        img_match = re.search(r'src="([^"]+\.(?:webp|jpg|jpeg|png))"', poster_html)
        if img_match:
            image = img_match.group(1)
            if not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', poster_html)
        if token_match:
            token = token_match.group(1)
        
        # Type
        film_type = 'dizi' if '/dizi/' in url or 'dizi' in source_url.lower() else 'film'
        
        # Language
        language = ''
        if 'Yerli' in poster_html:
            language = 'Yerli'
        elif 'Dublaj' in poster_html and 'Altyazı' in poster_html:
            language = 'Dublaj & Altyazılı'
        elif 'Dublaj' in poster_html:
            language = 'Türkçe Dublaj'
        elif 'Altyazı' in poster_html:
            language = 'Türkçe Altyazı'
        
        return {
            'url': url,
            'title': title,
            'year': year,
            'imdb': imdb,
            'image': image,
            'language': language,
            'type': film_type,
            'token': token,
            'source': source_url,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        return None

def clean_title(title):
    """Clean and format title"""
    title = html.unescape(title)
    
    # Remove common suffixes
    suffixes = [
        r'\s*izle\s*$',
        r'\s*türkçe\s*$',
        r'\s*dublaj\s*$',
        r'\s*altyazı\s*$',
        r'\s*yabancı\s*$',
        r'\s*dizi\s*$',
        r'\s*film\s*$',
        r'\s*hd\s*$',
        r'\s*full\s*$',
        r'\s*1080p\s*$',
        r'\s*720p\s*$',
        r'\s*online\s*$',
    ]
    
    for suffix in suffixes:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    
    title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def extract_embed_url_from_film_page(film_url, token):
    """Extract embed URL from individual film page - GELİŞTİRİLMİŞ VERSİYON"""
    html_content = get_html(film_url)
    if not html_content:
        return None
    
    embed_url = None
    
    # 1. ÖNCEKİ YÖNTEMLER: iframe data-src veya src
    patterns = [
        r'<iframe[^>]*data-src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"',
        r'<iframe[^>]*src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"',
        r'iframe[^>]*data-src="(https?://[^"]*hdfilmcehennemi[^"]*)"',
        r'iframe[^>]*src="(https?://[^"]*hdfilmcehennemi[^"]*)"',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            embed_url = match.group(1)
            if embed_url.startswith('//'):
                embed_url = 'https:' + embed_url
            break
    
    # 2. YENİ YÖNTEM: Video ID'sini arayalım
    if not embed_url:
        # Video ID pattern 1: data-id="..."
        video_id_match = re.search(r'data-id="([^"]+)"', html_content)
        if video_id_match:
            video_id = video_id_match.group(1)
            embed_url = f"{EMBED_BASE}{video_id}/"
        else:
            # Video ID pattern 2: rapidrame_id parametresi
            rapidrame_match = re.search(r'rapidrame_id=(\d+)', html_content)
            if rapidrame_match:
                rapidrame_id = rapidrame_match.group(1)
                embed_url = f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={rapidrame_id}"
    
    # 3. ALTERNATİF YÖNTEM: JavaScript kodunda embed URL'si
    if not embed_url:
        js_patterns = [
            r'embed\.php\?id=([^&"\']+)',
            r'video/embed/([^"\']+)',
            r'embedURL[^=]*=[^"\']*["\']([^"\']+)["\']',
            r'videoEmbedUrl[^=]*=[^"\']*["\']([^"\']+)["\']',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if 'hdfilmcehennemi' in match:
                    embed_url = match if match.startswith('http') else f"https://hdfilmcehennemi.mobi/video/embed/{match}"
                    break
                elif not match.startswith('http') and len(match) > 5:
                    # Muhtemelen bir ID
                    embed_url = f"{EMBED_BASE}{match}"
                    break
        
        # Eğer embed URL'si tam değilse, base URL ekle
        if embed_url and embed_url.startswith('/'):
            embed_url = f"https://hdfilmcehennemi.mobi{embed_url}"
    
    # 4. SON ÇARE: Token kullanarak oluştur
    if not embed_url and token:
        # Farklı embed formatlarını dene
        embed_patterns = [
            f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={token}",
            f"{EMBED_BASE}{token}/",
            f"{EMBED_BASE}?id={token}",
        ]
        
        # Her birini test et
        for pattern in embed_patterns:
            test_html = get_html(pattern)
            if test_html and 'video' in test_html.lower():
                embed_url = pattern
                break
    
    # 5. EK YÖNTEM: Film URL'sinden ID çıkart
    if not embed_url:
        # URL'den ID çıkartmaya çalış
        url_path = urlparse(film_url).path
        # Örnek: /1-esaretin-bedeli-film-izle-hdf-hdf-6/
        # Son sayıyı al (6)
        id_match = re.search(r'-(\d+)/?$', url_path)
        if id_match:
            film_id = id_match.group(1)
            # Farklı embed formatlarını dene
            test_urls = [
                f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={film_id}",
                f"{EMBED_BASE}{film_id}/",
            ]
            
            for test_url in test_urls:
                try:
                    # Hızlı bir bağlantı testi
                    req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
                    urllib.request.urlopen(req, timeout=5)
                    embed_url = test_url
                    break
                except:
                    continue
    
    return embed_url

def scrape_discovery_pages():
    """Keşfetme sayfalarını tarar"""
    all_films = []
    
    print("=" * 70)
    print("HDFilmCehennemi Discovery Scraper")
    print("=" * 70)
    
    # 1. Ana sayfa
    print("\n1. Scraping homepage...")
    html_content = get_html(BASE_URL)
    if html_content:
        films = extract_films_from_html(html_content, BASE_URL)
        if films:
            all_films.extend(films)
            print(f"  Found {len(films)} films")
    
    # 2. Bilinen film listesi sayfaları
    print("\n2. Scraping known list pages...")
    
    # Farklı listeleme sayfalarını dene
    list_pages = [
        # Film robotu sayfaları
        "https://www.hdfilmcehennemi.nl/film-robotu-1/",
        
        # Diğer olası listeleme sayfaları
        "https://www.hdfilmcehennemi.nl/",
        "https://www.hdfilmcehennemi.nl/category/film-izle-2/",
        "https://www.hdfilmcehennemi.nl/category/nette-ilk-filmler/",
        "https://www.hdfilmcehennemi.nl/dil/turkce-dublajli-film-izleyin-4/",
        "https://www.hdfilmcehennemi.nl/yil/2025-filmleri-izle-3/",
        "https://www.hdfilmcehennemi.nl/tur/aile-filmleri-izleyin-7/",
        "https://www.hdfilmcehennemi.nl/tur/aksiyon-filmleri-izleyin-6/",
        "https://www.hdfilmcehennemi.nl/tur/bilim-kurgu-filmlerini-izleyin-5/",
        "https://www.hdfilmcehennemi.nl/tur/fantastik-filmlerini-izleyin-3/",
        "https://www.hdfilmcehennemi.nl/category/1080p-hd-film-izle-5/",
        "https://www.hdfilmcehennemi.nl/serifilmlerim-3/",
        "https://www.hdfilmcehennemi.ws/ulke/turkiye-2/",
        "https://www.hdfilmcehennemi.ws/tur/savas-filmleri-izle-5/",
        "https://www.hdfilmcehennemi.ws/komedi-filmleri/",
        "https://www.hdfilmcehennemi.ws/dram-filmleri/",
        "https://www.hdfilmcehennemi.ws/gerilim-filmleri/",
        "https://www.hdfilmcehennemi.ws/bilim-kurgu-filmleri/",
        "https://www.hdfilmcehennemi.ws/fantastik-filmleri/",
        "https://www.hdfilmcehennemi.ws/en-cok-begenilen-filmleri-izle-2/",
        "https://www.hdfilmcehennemi.ws/en-cok-yorumlananlar-2/",
        "https://www.hdfilmcehennemi.ws/imdb-7-puan-uzeri-filmler-2/",
        
        # Sayfa numaralı listeler
        "https://www.hdfilmcehennemi.ws/sayfa/1/",
        "https://www.hdfilmcehennemi.ws/sayfa/2/",
        "https://www.hdfilmcehennemi.ws/sayfa/3/",
        "https://www.hdfilmcehennemi.ws/sayfa/4/",
        "https://www.hdfilmcehennemi.ws/sayfa/5/",
    ]
    
    for url in list_pages:
        print(f"  Testing: {url}")
        html_content = get_html(url)
        if html_content:
            films = extract_films_from_html(html_content, url)
            if films:
                # Benzersiz filmleri ekle
                existing_urls = {f['url'] for f in all_films}
                new_films = []
                for film in films:
                    if film['url'] not in existing_urls:
                        new_films.append(film)
                        existing_urls.add(film['url'])
                
                if new_films:
                    all_films.extend(new_films)
                    print(f"    Added {len(new_films)} new films, total: {len(all_films)}")
        
        time.sleep(0.5)
    
    # 3. Daha fazla robotu sayfası dene (1-50)
    print("\n3. Testing more robotu pages (1-50)...")
    for i in range(1, 51):
        url = f"https://www.hdfilmcehennemi.ws/film-robotu-{i}/"
        html_content = get_html(url)
        if html_content:
            films = extract_films_from_html(html_content, url)
            if films:
                existing_urls = {f['url'] for f in all_films}
                new_films = []
                for film in films:
                    if film['url'] not in existing_urls:
                        new_films.append(film)
                        existing_urls.add(film['url'])
                
                if new_films:
                    all_films.extend(new_films)
                    print(f"    Robotu-{i}: Added {len(new_films)} new films, total: {len(all_films)}")
        
        if i % 10 == 0:
            time.sleep(1)
    
    return all_films

def scrape_by_popular_films():
    """Popüler filmlerden başlayarak tarar"""
    all_films = []
    
    print("\n4. Scraping by exploring popular film pages...")
    
    # Önce bilinen popüler filmleri al
    popular_films = [
        "https://www.hdfilmcehennemi.ws/1-esaretin-bedeli-film-izle-hdf-hdf-6/",
        "https://www.hdfilmcehennemi.ws/hd-the-godfather-izle-10/",
        "https://www.hdfilmcehennemi.ws/batman-kara-sovalye-hd-film-izle-hdf-hdf-7/",
        "https://www.hdfilmcehennemi.ws/1-yuzuklerin-efendisi-kralin-donusu-izle-hdf-7/",
        "https://www.hdfilmcehennemi.ws/1-dovus-kulubu-izle-6/",
        "https://www.hdfilmcehennemi.ws/ucuz-roman-izle-hdf-7/",
        "https://www.hdfilmcehennemi.ws/1-iyi-kotu-ve-cirkin-izle-hdf-7/",
        "https://www.hdfilmcehennemi.ws/hd-schindlerin-listesi-film-izle-7/",
        "https://www.hdfilmcehennemi.ws/12-angry-men-6/",
        "https://www.hdfilmcehennemi.ws/yuzuklerin-efendisi-iki-kule-film-izle-hdf-7/",
        "https://www.hdfilmcehennemi.ws/1-baslangic-izle-7/",
        "https://www.hdfilmcehennemi.ws/hd-star-wars-empire-strikes-back-film-izle-6/",
        "https://www.hdfilmcehennemi.ws/1-matrix-film-izle-hdf-hdf-7/",
        "https://www.hdfilmcehennemi.ws/hd-yedi-samura-izle-7/",
        "https://www.hdfilmcehennemi.ws/1-silahsor-film-izle-5/",
        "https://www.hdfilmcehennemi.ws/hd-terminator-2-judgment-day-izle-7/",
    ]
    
    # Bu film sayfalarından "benzer filmler" veya "diğer filmler" bölümlerini çıkarmaya çalış
    for film_url in popular_films:
        print(f"  Exploring: {film_url}")
        html_content = get_html(film_url)
        if html_content:
            # Sayfada diğer film linkleri olabilir
            films = extract_films_from_html(html_content, film_url)
            if films:
                existing_urls = {f['url'] for f in all_films}
                new_films = []
                for film in films:
                    if film['url'] not in existing_urls:
                        new_films.append(film)
                        existing_urls.add(film['url'])
                
                if new_films:
                    all_films.extend(new_films)
                    print(f"    Added {len(new_films)} new films, total: {len(all_films)}")
        
        time.sleep(0.5)
    
    return all_films

def scrape_additional_pages():
    """Ek sayfaları tarar"""
    all_films = []
    
    print("\n5. Scraping additional pages...")
    
    # Daha fazla sayfa numarası dene
    for page_num in range(6, 31):
        url = f"https://www.hdfilmcehennemi.ws/sayfa/{page_num}/"
        print(f"  Testing: {url}")
        html_content = get_html(url)
        if html_content:
            films = extract_films_from_html(html_content, url)
            if films:
                all_films.extend(films)
                print(f"    Page {page_num}: Found {len(films)} films, total: {len(all_films)}")
        
        time.sleep(0.2)
    
    return all_films

def scrape_by_search():
    """Arama yaparak film bul"""
    all_films = []
    
    print("\n6. Trying search-based discovery...")
    
    # Popüler kelimelerle arama
    search_terms = [
        "film", "izle", "2024", "2023", "hd", "türkçe", 
        "aksiyon", "komedi", "dram", "korku", "macera"
    ]
    
    for term in search_terms:
        search_url = f"https://www.hdfilmcehennemi.ws/?s={term}"
        print(f"  Searching: {term}")
        
        html_content = get_html(search_url)
        if html_content:
            films = extract_films_from_html(html_content, search_url)
            if films:
                existing_urls = {f['url'] for f in all_films}
                new_films = []
                for film in films:
                    if film['url'] not in existing_urls:
                        new_films.append(film)
                        existing_urls.add(film['url'])
                
                if new_films:
                    all_films.extend(new_films)
                    print(f"    Found {len(new_films)} new films, total: {len(all_films)}")
        
        time.sleep(0.5)
    
    return all_films

def main():
    # Tüm filmleri topla
    print("Starting comprehensive scraping...")
    
    all_films = []
    
    # Discovery sayfalarını tara
    print("\nPhase 1: Discovery pages")
    films1 = scrape_discovery_pages()
    all_films.extend(films1)
    
    # Popüler filmleri tara
    print("\nPhase 2: Popular films")
    films2 = scrape_by_popular_films()
    all_films.extend(films2)
    
    # Ek sayfaları tara
    print("\nPhase 3: Additional pages")
    films3 = scrape_additional_pages()
    all_films.extend(films3)
    
    # Arama yaparak film bul
    print("\nPhase 4: Search-based discovery")
    films4 = scrape_by_search()
    all_films.extend(films4)
    
    if not all_films:
        print("\n❌ No films found!")
        return
    
    # Benzersiz filmler
    unique_films = []
    seen_urls = set()
    
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\n{'='*70}")
    print(f"Found {len(unique_films)} unique films")
    print(f"{'='*70}")
    
    # TÜM filmler için embed URL'leri al (daha etkili yöntemle)
    print(f"\nFetching embed URLs for ALL films (optimized)...")
    films_with_embeds = []
    total_films = len(unique_films)
    
    # Embed URL'lerini toplu olarak işlemek için batch sistemi
    batch_size = 20
    failed_embeds = []
    
    for i in range(0, total_films, batch_size):
        batch = unique_films[i:i+batch_size]
        batch_start = i + 1
        batch_end = min(i + batch_size, total_films)
        
        print(f"\n  Processing batch {batch_start}-{batch_end} of {total_films}...")
        
        for j, film in enumerate(batch, 1):
            film_num = i + j
            print(f"    [{film_num}/{total_films}] {film['title'][:40]}...")
            
            # Embed URL'yi al
            embed_url = extract_embed_url_from_film_page(film['url'], film.get('token', ''))
            film['embed_url'] = embed_url
            
            films_with_embeds.append(film)
            
            if not embed_url:
                failed_embeds.append(film['url'])
            
            # Request'ler arasında kısa bir bekleme
            if j < len(batch):
                time.sleep(0.05)  # Çok kısa bir delay
        
        # Batch'ler arasında biraz daha uzun bekleme
        if batch_end < total_films:
            time.sleep(0.5)
    
    # Embed URL'si bulunamayan filmler için tekrar deneme
    if failed_embeds:
        print(f"\n  Retrying {len(failed_embeds)} films without embed URLs...")
        
        for url in failed_embeds:
            # Bu URL'ye karşılık gelen filmi bul
            for film in films_with_embeds:
                if film['url'] == url:
                    print(f"    Retrying: {film['title'][:40]}...")
                    
                    # Farklı yöntemlerle tekrar dene
                    embed_url = extract_embed_url_from_film_page(film['url'], film.get('token', ''))
                    
                    if not embed_url:
                        # Alternatif URL oluştur
                        url_parts = film['url'].split('/')
                        if len(url_parts) > 1:
                            last_part = url_parts[-2] if url_parts[-1] == '' else url_parts[-1]
                            # Sayı içeren kısmı bul
                            id_match = re.search(r'(\d+)$', last_part)
                            if id_match:
                                film_id = id_match.group(1)
                                # Farklı embed formatlarını dene
                                embed_urls_to_try = [
                                    f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={film_id}",
                                    f"{EMBED_BASE}{film_id}/",
                                    f"https://hdfilmcehennemi.mobi/video/embed.php?id={film_id}",
                                ]
                                
                                for embed_url_try in embed_urls_to_try:
                                    try:
                                        req = urllib.request.Request(embed_url_try, headers={'User-Agent': 'Mozilla/5.0'})
                                        urllib.request.urlopen(req, timeout=3)
                                        embed_url = embed_url_try
                                        break
                                    except:
                                        continue
                    
                    film['embed_url'] = embed_url
                    break
    
    # Sonuçları kaydet
    save_results(films_with_embeds)
    
    # Özet göster
    print_summary(films_with_embeds)

def save_results(films):
    """Save results to files"""
    try:
        result = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(films),
                'films_with_embeds': sum(1 for f in films if f.get('embed_url')),
                'embed_success_rate': f"{(sum(1 for f in films if f.get('embed_url')) / len(films) * 100):.1f}%" if films else "0%",
                'source': 'hdfilmcehennemi.ws'
            },
            'films': films
        }
        
        with open('hdfilms_complete.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Complete results saved to: hdfilms_complete.json")
    except Exception as e:
        print(f"❌ Error saving complete file: {e}")
    
    try:
        simple_data = []
        for film in films:
            simple_data.append({
                'title': film['title'],
                'year': film.get('year', ''),
                'type': film['type'],
                'url': film['url'],
                'embed_url': film.get('embed_url', ''),
                'imdb': film['imdb'],
                'image': film.get('image', ''),
                'token': film.get('token', '')
            })
        
        with open('hdceh_embeds.json', 'w', encoding='utf-8') as f:
            json.dump(simple_data, f, ensure_ascii=False, indent=2)
        print(f"✅ GitHub Actions file saved to: hdceh_embeds.json")
    except Exception as e:
        print(f"❌ Error saving embeds file: {e}")

def print_summary(films):
    """Print summary"""
    if not films:
        return
    
    films_count = sum(1 for f in films if f['type'] == 'film')
    diziler_count = sum(1 for f in films if f['type'] == 'dizi')
    embeds_count = sum(1 for f in films if f.get('embed_url'))
    embed_rate = (embeds_count / len(films) * 100) if films else 0
    
    print(f"\n{'='*70}")
    print(f"SUMMARY:")
    print(f"{'='*70}")
    print(f"  Total films: {len(films)}")
    print(f"  Films: {films_count}")
    print(f"  Diziler: {diziler_count}")
    print(f"  With embed URLs: {embeds_count} ({embed_rate:.1f}%)")
    
    # Film türlerine göre dağılım
    print(f"\n  Categories found:")
    categories = {}
    for film in films:
        if 'source' in film:
            source = film['source']
            if '/tur/' in source:
                category_match = re.search(r'/tur/([^/-]+)', source)
                if category_match:
                    category = category_match.group(1).replace('-', ' ').title()
                    categories[category] = categories.get(category, 0) + 1
    
    if categories:
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
        for category, count in sorted_categories:
            print(f"    {category}: {count} films")
    
    # En yüksek IMDB'li filmler
    films_with_imdb = [f for f in films if f['imdb'] != '0.0']
    if films_with_imdb:
        films_with_imdb.sort(key=lambda x: float(x['imdb']), reverse=True)
        print(f"\n  Top 10 films by IMDB:")
        for i, film in enumerate(films_with_imdb[:10], 1):
            title = film['title'][:45] + "..." if len(film['title']) > 45 else film['title']
            year = film.get('year', 'N/A')
            has_embed = "✓" if film.get('embed_url') else "✗"
            print(f"    {i:2}. {title:50} {year:6} ⭐{film['imdb']} [embed:{has_embed}]")
    
    # Embed istatistikleri
    print(f"\n  Embed statistics:")
    embed_sources = {}
    for film in films:
        embed_url = film.get('embed_url', '')
        if embed_url:
            if 'GKsnOLw2hsT' in embed_url:
                embed_sources['rapidrame'] = embed_sources.get('rapidrame', 0) + 1
            elif 'embed.php' in embed_url:
                embed_sources['embed_php'] = embed_sources.get('embed_php', 0) + 1
            elif '/embed/' in embed_url:
                embed_sources['embed_path'] = embed_sources.get('embed_path', 0) + 1
            else:
                embed_sources['other'] = embed_sources.get('other', 0) + 1
    
    for source_type, count in embed_sources.items():
        percentage = (count / embeds_count * 100) if embeds_count else 0
        print(f"    {source_type}: {count} ({percentage:.1f}%)")
    
    print(f"\n{'='*70}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
