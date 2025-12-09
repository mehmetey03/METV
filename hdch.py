#!/usr/bin/env python3
"""
hdch_final.py - HDFilmCehennemi scraper with multiple fallback methods
"""
import urllib.request
import urllib.error
import json
import re
import html
import time
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.hdfilmcehennemi.ws/"
EMBED_BASE_URL = "https://hdfilmcehennemi.mobi/video/embed/"

# Farklı URL kombinasyonlarını deneyelim
CATEGORIES = {
    'film': [
        'https://www.hdfilmcehennemi.ws/category/film/',
        'https://www.hdfilmcehennemi.ws/category/film-izle/',
        'https://www.hdfilmcehennemi.ws/filmler/',
        'https://www.hdfilmcehennemi.ws/'
    ],
    'dizi': [
        'https://www.hdfilmcehennemi.ws/category/dizi/',
        'https://www.hdfilmcehennemi.ws/category/dizi-izle/',
        'https://www.hdfilmcehennemi.ws/diziler/'
    ]
}

def get_html(url, retry=3):
    """Get HTML content with retry mechanism"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Referer': BASE_URL,
    }
    
    for attempt in range(retry):
        try:
            req = urllib.request.Request(url, headers=headers)
            # Add timeout and handle redirects
            with urllib.request.urlopen(req, timeout=30) as response:
                # Check if response is gzipped
                if response.info().get('Content-Encoding') == 'gzip':
                    import gzip
                    content = gzip.decompress(response.read()).decode('utf-8', errors='ignore')
                else:
                    content = response.read().decode('utf-8', errors='ignore')
                return content
        except urllib.error.HTTPError as e:
            if attempt == retry - 1:
                print(f"  HTTP Error {e.code} for {url}")
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            if attempt == retry - 1:
                print(f"  Error fetching {url}: {e}")
                return None
            time.sleep(2 ** attempt)
    
    return None

def extract_films_new_method(html_content, source_url):
    """Yeni yöntem: Daha esnek parsing"""
    films = []
    
    if not html_content:
        return films
    
    # Method 1: Direct search for film links with data-token
    film_patterns = [
        r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>',  # Original pattern
        r'<div\s+class="[^"]*film-item[^"]*"[^>]*>.*?</div>',  # Film item div
        r'<article[^>]*data-id="\d+"[^>]*>.*?</article>',  # Article with data-id
        r'<div\s+class="[^"]*poster[^"]*"[^>]*>.*?</div>',  # Poster div
    ]
    
    all_matches = []
    for pattern in film_patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        if matches:
            print(f"  Found {len(matches)} matches with pattern: {pattern[:50]}...")
            all_matches.extend(matches)
    
    if not all_matches:
        # Try to find any links that look like film/dizi links
        links = re.findall(r'<a\s+href="(https://www\.hdfilmcehennemi\.ws/[^"]+)"[^>]*>(.*?)</a>', html_content, re.DOTALL)
        film_links = []
        for link, content in links:
            if '/film' in link or '/dizi' in link or '-izle' in link:
                film_links.append(f'<a href="{link}">{content}</a>')
        
        print(f"  Found {len(film_links)} film-like links")
        all_matches = film_links
    
    for match in all_matches[:50]:  # Limit to first 50 to avoid too many
        film = parse_film_flexible(match, source_url)
        if film:
            films.append(film)
    
    return films

def parse_film_flexible(html_block, source_url):
    """Esnek parsing - çeşitli formatları destekler"""
    try:
        # URL
        url_match = re.search(r'href="([^"]+)"', html_block)
        if not url_match:
            return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # Başlık - çeşitli yerlerden dene
        title = ''
        
        # 1. title attribute'den
        title_attr = re.search(r'title="([^"]+)"', html_block)
        if title_attr:
            title = html.unescape(title_attr.group(1)).strip()
        
        # 2. İçerikten (a tag içinden)
        if not title:
            content_match = re.search(r'<a[^>]*>(.*?)</a>', html_block, re.DOTALL)
            if content_match:
                # HTML tag'lerini temizle
                title = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
                title = html.unescape(title)
        
        # 3. img alt'tan
        if not title:
            alt_match = re.search(r'alt="([^"]+)"', html_block)
            if alt_match:
                title = html.unescape(alt_match.group(1)).strip()
        
        if not title or len(title) < 2:
            return None
        
        # Temizleme
        title = re.sub(r'\s+', ' ', title)  # Multiple spaces
        title = re.sub(r'^\s*[♪♫★☆♥♦♣♠■□▪▫●○◆◇►◄▲▼]+\s*', '', title)  # Special chars
        title = re.sub(r'\s*(?:\(?\d{4}\)?|izle|türkçe|dublaj|altyazı|yabancı|dizi|film|hd|full|1080p|720p|online)\s*$', '', title, flags=re.IGNORECASE)
        title = title.strip()
        
        if len(title) < 2:
            return None
        
        # Yıl
        year = ''
        year_match = re.search(r'\((\d{4})\)', title)
        if year_match:
            year = year_match.group(1)
            title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
        else:
            # HTML blok içinde ara
            year_in_block = re.search(r'<span[^>]*>\s*(\d{4})\s*</span>', html_block)
            if year_in_block:
                year = year_in_block.group(1)
        
        # IMDB
        imdb = '0.0'
        imdb_patterns = [
            r'imdb[^>]*>\s*(\d+\.\d+)',
            r'(\d+\.\d+)\s*/10',
            r'rating[^>]*>\s*(\d+\.\d+)',
        ]
        for pattern in imdb_patterns:
            imdb_match = re.search(pattern, html_block, re.IGNORECASE)
            if imdb_match:
                try:
                    rating = float(imdb_match.group(1))
                    if 1.0 <= rating <= 10.0:
                        imdb = f"{rating:.1f}"
                        break
                except:
                    pass
        
        # Resim
        image = ''
        img_patterns = [
            r'src="([^"]+\.(?:webp|jpg|jpeg|png|gif))"',
            r'data-src="([^"]+\.(?:webp|jpg|jpeg|png|gif))"',
            r'data-original="([^"]+\.(?:webp|jpg|jpeg|png|gif))"',
        ]
        for pattern in img_patterns:
            img_match = re.search(pattern, html_block, re.IGNORECASE)
            if img_match:
                image = img_match.group(1)
                if image.startswith('//'):
                    image = 'https:' + image
                elif not image.startswith('http'):
                    image = urljoin(BASE_URL, image)
                break
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', html_block)
        if token_match:
            token = token_match.group(1)
        else:
            # URL'den çıkar
            token_from_url = re.search(r'/(\d+)(?:-|$|/)', url)
            if token_from_url:
                token = token_from_url.group(1)
        
        # Tür
        film_type = 'dizi' if '/dizi' in url or 'dizi' in source_url.lower() else 'film'
        
        # Dil
        language = ''
        if 'türkçe dublaj' in html_block.lower():
            language = 'Türkçe Dublaj'
        elif 'türkçe altyazı' in html_block.lower():
            language = 'Türkçe Altyazı'
        elif 'dublaj' in html_block.lower():
            language = 'Türkçe Dublaj'
        elif 'altyazı' in html_block.lower():
            language = 'Türkçe Altyazı'
        
        return {
            'url': url,
            'title': title,
            'year': year,
            'imdb': imdb,
            'image': image,
            'token': token,
            'type': film_type,
            'language': language,
            'source': source_url,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"    Error parsing: {e}")
        return None

def extract_embed_url(film_url, token):
    """Embed URL çıkar"""
    print(f"    Fetching embed for: {film_url}")
    
    html_content = get_html(film_url)
    if not html_content:
        return None
    
    # Çeşitli embed pattern'leri
    embed_patterns = [
        r'<iframe[^>]*src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"',
        r'src="(https://hdfilmcehennemi\.mobi/video/embed/[^"]*)"',
        r'embed-url="([^"]*hdfilmcehennemi\.mobi[^"]*)"',
        r'data-embed="([^"]*)"',
    ]
    
    for pattern in embed_patterns:
        embed_match = re.search(pattern, html_content, re.IGNORECASE)
        if embed_match:
            embed_url = embed_match.group(1)
            if not embed_url.startswith('http'):
                embed_url = 'https:' + embed_url if embed_url.startswith('//') else urljoin(BASE_URL, embed_url)
            return embed_url
    
    # Script içinde ara
    script_pattern = r'<script[^>]*>.*?(GKsnOLw2hsT[^"\']*).*?</script>'
    script_match = re.search(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if script_match:
        embed_code = script_match.group(1)
        # Format: GKsnOLw2hsT/?rapidrame_id=bgnlte9jeoiu
        embed_match = re.search(r'([A-Za-z0-9_\-]+)/\?rapidrame_id=([A-Za-z0-9]+)', embed_code)
        if embed_match:
            embed_path = embed_match.group(1)
            rapidrame_id = embed_match.group(2)
            return f"{EMBED_BASE_URL}{embed_path}/?rapidrame_id={rapidrame_id}"
    
    # Token'dan oluştur
    if token:
        return f"{EMBED_BASE_URL}GKsnOLw2hsT/?rapidrame_id={token}"
    
    return None

def scrape_with_fallback():
    """Çeşitli yöntemlerle scrape et"""
    all_films = []
    
    print("Trying different scraping methods...")
    
    # Method 1: Ana sayfadan
    print("\n1. Trying homepage...")
    homepage = get_html(BASE_URL)
    if homepage:
        films = extract_films_new_method(homepage, BASE_URL)
        all_films.extend(films)
        print(f"   Found {len(films)} films from homepage")
    
    # Method 2: Farklı kategori URL'lerini dene
    for category_name, urls in CATEGORIES.items():
        print(f"\n2. Trying {category_name} URLs...")
        for url in urls:
            print(f"   Testing: {url}")
            html_content = get_html(url)
            if html_content:
                films = extract_films_new_method(html_content, url)
                if films:
                    all_films.extend(films)
                    print(f"   Found {len(films)} films from {url}")
                    break  # Bir URL çalışıyorsa diğerlerini deneme
            time.sleep(1)
    
    # Method 3: Site haritası veya popüler sayfalar
    popular_urls = [
        'https://www.hdfilmcehennemi.ws/populer/',
        'https://www.hdfilmcehennemi.ws/en-cok-izlenen/',
        'https://www.hdfilmcehennemi.ws/yeni-eklenen/',
        'https://www.hdfilmcehennemi.ws/box-office/',
    ]
    
    print("\n3. Trying popular pages...")
    for url in popular_urls:
        print(f"   Testing: {url}")
        html_content = get_html(url)
        if html_content:
            films = extract_films_new_method(html_content, url)
            if films:
                all_films.extend(films)
                print(f"   Found {len(films)} films from {url}")
        time.sleep(1)
    
    return all_films

def main():
    print("=" * 70)
    print("HDFilmCehennemi Smart Scraper")
    print("=" * 70)
    
    # Farklı yöntemlerle filmleri topla
    all_films = scrape_with_fallback()
    
    if not all_films:
        print("\n❌ No films found with any method!")
        
        # Son çare: Manuel test için bazı bilinen film URL'leri
        print("\nTrying known film URLs as last resort...")
        known_films = [
            'https://www.hdfilmcehennemi.ws/sentimental-value/',
            'https://www.hdfilmcehennemi.ws/die-my-love/',
            'https://www.hdfilmcehennemi.ws/keeper-2025-1/',
        ]
        
        for url in known_films:
            print(f"  Testing: {url}")
            html_content = get_html(url)
            if html_content:
                # Tek film için manuel parsing
                film = parse_single_film_page(html_content, url)
                if film:
                    all_films.append(film)
            time.sleep(1)
    
    if not all_films:
        print("\n🚫 COMPLETELY FAILED! Site structure might have changed significantly.")
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
    
    # Embed URL'leri al
    print(f"\nFetching embed URLs...")
    films_with_embeds = []
    
    for i, film in enumerate(unique_films, 1):
        print(f"  [{i}/{len(unique_films)}] {film['title'][:30]}...")
        
        embed_url = extract_embed_url(film['url'], film.get('token', ''))
        film['embed_url'] = embed_url
        
        if embed_url:
            print(f"    ✓ Embed found")
        else:
            print(f"    ✗ No embed")
        
        films_with_embeds.append(film)
        time.sleep(0.5)  # Polite delay
    
    # Kaydet
    save_results(films_with_embeds)
    
    # Özet
    print_summary(films_with_embeds)

def parse_single_film_page(html_content, url):
    """Tek film sayfasından bilgi çıkar"""
    try:
        # Başlık
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL)
        if not title_match:
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.DOTALL)
        
        title = title_match.group(1).strip() if title_match else 'Unknown'
        title = re.sub(r'<[^>]+>', '', title)
        title = html.unescape(title)
        title = re.sub(r'\s*-\s*HDFilmCehennemi.*$', '', title, flags=re.IGNORECASE)
        
        # Yıl
        year = ''
        year_match = re.search(r'\((\d{4})\)', title)
        if year_match:
            year = year_match.group(1)
            title = re.sub(r'\s*\(\d{4}\)\s*', ' ', title)
        
        # Resim
        image = ''
        img_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html_content)
        if img_match:
            image = img_match.group(1)
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', html_content)
        if token_match:
            token = token_match.group(1)
        
        return {
            'url': url,
            'title': title.strip(),
            'year': year,
            'imdb': '0.0',
            'image': image,
            'token': token,
            'type': 'film' if '/film' in url else 'dizi',
            'language': '',
            'source': url,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error parsing single page: {e}")
        return None

def save_results(films):
    """Sonuçları kaydet"""
    # Ana dosya
    try:
        result = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(films),
                'films_with_embeds': sum(1 for f in films if f.get('embed_url')),
                'source': 'hdfilmcehennemi.ws'
            },
            'films': films
        }
        
        with open('hdfilms_complete.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved to: hdfilms_complete.json")
    except Exception as e:
        print(f"❌ Error saving main file: {e}")
    
    # GitHub Actions için
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
                'image': film.get('image', '')
            })
        
        with open('hdceh_embeds.json', 'w', encoding='utf-8') as f:
            json.dump(simple_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved to: hdceh_embeds.json")
    except Exception as e:
        print(f"❌ Error saving embeds file: {e}")

def print_summary(films):
    """Özet göster"""
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    films_count = sum(1 for f in films if f['type'] == 'film')
    diziler_count = sum(1 for f in films if f['type'] == 'dizi')
    embeds_count = sum(1 for f in films if f.get('embed_url'))
    
    print(f"Total films: {len(films)}")
    print(f"Films: {films_count}")
    print(f"Diziler: {diziler_count}")
    print(f"With embed URLs: {embeds_count}")
    
    if films:
        print(f"\nSample films:")
        print("-" * 70)
        for i, film in enumerate(films[:10], 1):
            title = film['title'][:40] + "..." if len(film['title']) > 40 else film['title']
            year = film.get('year', 'N/A')
            embed = "✓" if film.get('embed_url') else "✗"
            print(f"{i:2}. [{embed}] {title:45} {year:6}")
    
    print(f"\n{'='*70}")
    print("DONE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
