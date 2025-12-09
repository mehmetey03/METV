#!/usr/bin/env python3
"""
hdch_final.py - HDFilmCehennemi scraper with working embed detection
"""
import urllib.request
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.hdfilmcehennemi.ws/"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url):
    """Get HTML content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': BASE_URL,
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def extract_films_from_homepage():
    """Extract films from homepage and other pages"""
    films = []
    
    # Önce ana sayfayı dene
    print("Scraping homepage...")
    homepage = get_html(BASE_URL)
    
    if homepage:
        # Ana sayfadaki film linklerini bul
        film_links = re.findall(r'<a\s+href="(https://www\.hdfilmcehennemi\.ws/[^"/]+/)"[^>]*>', homepage)
        
        # Benzersiz linkler
        unique_links = list(set(film_links))
        print(f"Found {len(unique_links)} unique film links on homepage")
        
        # Her film sayfasını işle
        for i, film_url in enumerate(unique_links[:30], 1):  # İlk 30'u al
            print(f"  [{i}/{min(30, len(unique_links))}] Processing: {film_url}")
            
            film_data = scrape_film_page(film_url)
            if film_data:
                films.append(film_data)
            
            time.sleep(0.5)  # Polite delay
    
    # Popüler filmler sayfasını da dene
    print("\nScraping popular films...")
    popular_urls = [
        "https://www.hdfilmcehennemi.ws/box-office/",
        "https://www.hdfilmcehennemi.ws/populer-filmler/",
        "https://www.hdfilmcehennemi.ws/yeni-filmler/",
    ]
    
    for url in popular_urls:
        print(f"  Checking: {url}")
        html_content = get_html(url)
        if html_content:
            links = re.findall(r'<a\s+href="(https://www\.hdfilmcehennemi\.ws/[^"/]+/)"[^>]*>', html_content)
            for film_url in links[:10]:  # Her sayfadan ilk 10'u al
                if film_url not in [f['url'] for f in films]:
                    film_data = scrape_film_page(film_url)
                    if film_data:
                        films.append(film_data)
                    time.sleep(0.5)
    
    return films

def scrape_film_page(film_url):
    """Scrape individual film page"""
    html_content = get_html(film_url)
    if not html_content:
        return None
    
    try:
        # Başlık
        title = extract_title(html_content, film_url)
        if not title:
            return None
        
        # Yıl
        year = extract_year(html_content, title)
        
        # Resim
        image = extract_image(html_content)
        
        # Embed URL
        embed_url = extract_embed_url_from_page(html_content)
        
        # IMDB
        imdb = extract_imdb(html_content)
        
        # Tür (film/dizi)
        film_type = 'dizi' if '/dizi/' in film_url else 'film'
        
        # Dil
        language = extract_language(html_content)
        
        # Token
        token = extract_token(embed_url) if embed_url else ''
        
        return {
            'url': film_url,
            'title': title,
            'year': year,
            'imdb': imdb,
            'image': image,
            'embed_url': embed_url,
            'token': token,
            'type': film_type,
            'language': language,
            'source': film_url,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"    Error scraping {film_url}: {e}")
        return None

def extract_title(html_content, url):
    """Extract title from film page"""
    # Method 1: h1 tag
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL)
    if h1_match:
        title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
        title = html.unescape(title)
        return clean_title(title)
    
    # Method 2: og:title meta tag
    meta_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html_content)
    if meta_match:
        title = html.unescape(meta_match.group(1)).strip()
        return clean_title(title)
    
    # Method 3: title tag
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.DOTALL)
    if title_match:
        title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
        title = html.unescape(title)
        # Remove site name
        title = re.sub(r'\s*-\s*HDFilmCehennemi.*$', '', title, flags=re.IGNORECASE)
        return clean_title(title)
    
    # Method 4: URL'den
    url_parts = url.rstrip('/').split('/')
    if url_parts:
        last_part = url_parts[-1].replace('-', ' ').title()
        return clean_title(last_part)
    
    return None

def clean_title(title):
    """Clean and format title"""
    if not title:
        return title
    
    title = re.sub(r'\s+', ' ', title)  # Multiple spaces
    title = re.sub(r'^\s*[♪♫★☆♥♦♣♠■□▪▫●○◆◇►◄▲▼]+\s*', '', title)  # Special chars
    title = re.sub(r'\s*(?:\(?\d{4}\)?|izle|türkçe|dublaj|altyazı|yabancı|dizi|film|hd|full|1080p|720p|online|ücretsiz)\s*$', '', title, flags=re.IGNORECASE)
    title = title.strip()
    return title

def extract_year(html_content, title):
    """Extract year from page or title"""
    # Title'da yıl var mı?
    year_match = re.search(r'\((\d{4})\)', title)
    if year_match:
        return year_match.group(1)
    
    # Sayfada yıl ara
    year_patterns = [
        r'<span[^>]*>\s*(\d{4})\s*</span>',
        r'Yıl:\s*<span[^>]*>\s*(\d{4})\s*</span>',
        r'Year:\s*<span[^>]*>\s*(\d{4})\s*</span>',
        r'\((\d{4})\)',
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return ''

def extract_image(html_content):
    """Extract image URL"""
    # og:image meta tag
    meta_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html_content)
    if meta_match:
        image = meta_match.group(1)
        if not image.startswith('http'):
            image = urljoin(BASE_URL, image)
        return image
    
    # img tag with poster
    img_patterns = [
        r'<img[^>]*src="([^"]+\.(?:webp|jpg|jpeg|png))"[^>]*class="[^"]*poster[^"]*"[^>]*>',
        r'<img[^>]*class="[^"]*poster[^"]*"[^>]*src="([^"]+\.(?:webp|jpg|jpeg|png))"[^>]*>',
        r'poster="([^"]+\.(?:webp|jpg|jpeg|png))"',
    ]
    
    for pattern in img_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            image = match.group(1)
            if not image.startswith('http'):
                image = urljoin(BASE_URL, image)
            return image
    
    return ''

def extract_embed_url_from_page(html_content):
    """Extract embed URL from film page - NEW METHOD based on your finding"""
    # Pattern 1: Look for iframe with data-src containing embed URL
    iframe_pattern = r'<iframe[^>]*data-src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"[^>]*>'
    iframe_match = re.search(iframe_pattern, html_content, re.IGNORECASE)
    
    if iframe_match:
        embed_url = iframe_match.group(1)
        if embed_url.startswith('//'):
            embed_url = 'https:' + embed_url
        return embed_url
    
    # Pattern 2: Look for GKsnOLw2hsT pattern
    gksn_pattern = r'(GKsnOLw2hsT[^"\']*)'
    gksn_match = re.search(gksn_pattern, html_content)
    if gksn_match:
        embed_code = gksn_match.group(1)
        # Format: GKsnOLw2hsT/?rapidrame_id=bgnlte9jeoiu
        embed_match = re.search(r'([A-Za-z0-9_\-]+)/\?rapidrame_id=([A-Za-z0-9]+)', embed_code)
        if embed_match:
            embed_path = embed_match.group(1)
            rapidrame_id = embed_match.group(2)
            return f"{EMBED_BASE}{embed_path}/?rapidrame_id={rapidrame_id}"
    
    # Pattern 3: Direct iframe src
    direct_iframe = r'<iframe[^>]*src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"[^>]*>'
    direct_match = re.search(direct_iframe, html_content, re.IGNORECASE)
    if direct_match:
        return direct_match.group(1)
    
    # Pattern 4: video-container div içinde
    video_container = r'<div[^>]*class="[^"]*video-container[^"]*"[^>]*>.*?(https://hdfilmcehennemi\.mobi/video/embed/[^<]+)</iframe>'
    container_match = re.search(video_container, html_content, re.DOTALL | re.IGNORECASE)
    if container_match:
        return container_match.group(1).strip()
    
    return None

def extract_token(embed_url):
    """Extract token from embed URL"""
    if not embed_url:
        return ''
    
    # Pattern: /?rapidrame_id=TOKEN
    token_match = re.search(r'rapidrame_id=([A-Za-z0-9]+)', embed_url)
    if token_match:
        return token_match.group(1)
    
    return ''

def extract_imdb(html_content):
    """Extract IMDB rating"""
    imdb_patterns = [
        r'imdb[^>]*>\s*(\d+\.\d+)',
        r'IMDb:\s*(\d+\.\d+)',
        r'rating[^>]*>\s*(\d+\.\d+)',
        r'<span[^>]*class="[^"]*imdb[^"]*"[^>]*>.*?(\d+\.\d+)',
    ]
    
    for pattern in imdb_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                rating = float(match.group(1))
                if 1.0 <= rating <= 10.0:
                    return f"{rating:.1f}"
            except:
                pass
    
    return '0.0'

def extract_language(html_content):
    """Extract language info"""
    content_lower = html_content.lower()
    
    if 'türkçe dublaj' in content_lower:
        return 'Türkçe Dublaj'
    elif 'türkçe altyazı' in content_lower:
        return 'Türkçe Altyazı'
    elif 'dublaj' in content_lower:
        return 'Türkçe Dublaj'
    elif 'altyazı' in content_lower:
        return 'Türkçe Altyazı'
    
    return ''

def main():
    print("=" * 70)
    print("HDFilmCehennemi Direct Film Scraper")
    print("=" * 70)
    
    # Filmleri topla
    all_films = extract_films_from_homepage()
    
    if not all_films:
        print("\n❌ No films found!")
        
        # Test için bilinen birkaç film
        print("\nTrying known films as test...")
        test_films = [
            "https://www.hdfilmcehennemi.ws/die-my-love/",
            "https://www.hdfilmcehennemi.ws/sentimental-value/",
            "https://www.hdfilmcehennemi.ws/keeper-2025-1/",
            "https://www.hdfilmcehennemi.ws/kombucha/",
            "https://www.hdfilmcehennemi.ws/the-carpenter-s-son/",
        ]
        
        for url in test_films:
            film_data = scrape_film_page(url)
            if film_data:
                all_films.append(film_data)
            time.sleep(1)
    
    if not all_films:
        print("\n🚫 Failed to scrape any films!")
        return
    
    # Benzersiz filmler
    unique_films = []
    seen_urls = set()
    
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Total unique films: {len(unique_films)}")
    
    # Filmleri embed URL'ye göre filtrele
    films_with_embeds = [f for f in unique_films if f.get('embed_url')]
    print(f"Films with embed URLs: {len(films_with_embeds)}")
    
    # Kaydet
    save_results(unique_films, films_with_embeds)
    
    # Özet göster
    print_summary(unique_films)

def save_results(all_films, films_with_embeds):
    """Save results to files"""
    # Ana dosya (tüm filmler)
    try:
        result = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(all_films),
                'films_with_embeds': len(films_with_embeds),
                'source': 'hdfilmcehennemi.ws'
            },
            'films': all_films
        }
        
        with open('hdfilms_complete.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Complete results saved to: hdfilms_complete.json")
    except Exception as e:
        print(f"❌ Error saving complete file: {e}")
    
    # GitHub Actions için (sadece embed'li filmler)
    try:
        simple_data = []
        for film in films_with_embeds:
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
    
    print(f"\nSUMMARY:")
    print(f"  Total: {len(films)}")
    print(f"  Films: {films_count}")
    print(f"  Diziler: {diziler_count}")
    print(f"  With embeds: {embeds_count}")
    
    # Yıllara göre dağılım
    years = {}
    for film in films:
        year = film.get('year', 'Unknown')
        if year:
            years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\n  Years distribution:")
        for year, count in sorted(years.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {year}: {count}")
    
    # Örnek filmler
    print(f"\n  Sample films with embeds:")
    films_with_embeds = [f for f in films if f.get('embed_url')]
    
    if films_with_embeds:
        for i, film in enumerate(films_with_embeds[:10], 1):
            title = film['title'][:40] + "..." if len(film['title']) > 40 else film['title']
            year = film.get('year', 'N/A')
            embed_short = film['embed_url'][40:80] + "..." if len(film['embed_url']) > 80 else film['embed_url'][40:]
            print(f"    {i:2}. {title:45} {year:6}")
            if embed_short:
                print(f"        Embed: ...{embed_short}")
    else:
        print("    No films with embed URLs found")
    
    print(f"\n{'='*70}")
    print("DONE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
