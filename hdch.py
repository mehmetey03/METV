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
from urllib.parse import urljoin

BASE_URL = "https://www.hdfilmcehennemi.ws/"
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
    """Extract embed URL from individual film page"""
    html_content = get_html(film_url)
    if not html_content:
        return None
    
    # Pattern 1: Look for iframe with data-src
    iframe_pattern = r'<iframe[^>]*data-src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"'
    iframe_match = re.search(iframe_pattern, html_content, re.IGNORECASE)
    
    if iframe_match:
        embed_url = iframe_match.group(1)
        if embed_url.startswith('//'):
            embed_url = 'https:' + embed_url
        return embed_url
    
    # Pattern 2: Direct iframe src
    direct_pattern = r'<iframe[^>]*src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"'
    direct_match = re.search(direct_pattern, html_content, re.IGNORECASE)
    if direct_match:
        return direct_match.group(1)
    
    # Pattern 3: Construct from token
    if token:
        return f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={token}"
    
    return None

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
        "https://www.hdfilmcehennemi.ws/film-robotu-1/",
        
        # Diğer olası listeleme sayfaları
        "https://www.hdfilmcehennemi.ws/arsiv/",
        "https://www.hdfilmcehennemi.ws/tum-filmler/",
        "https://www.hdfilmcehennemi.ws/tum-diziler/",
        "https://www.hdfilmcehennemi.ws/en-iyi-filmler/",
        "https://www.hdfilmcehennemi.ws/imdb-top-250/",
        "https://www.hdfilmcehennemi.ws/yabanci-filmler/",
        "https://www.hdfilmcehennemi.ws/yerli-filmler/",
        "https://www.hdfilmcehennemi.ws/aksiyon-filmleri/",
        "https://www.hdfilmcehennemi.ws/komedi-filmleri/",
        "https://www.hdfilmcehennemi.ws/dram-filmleri/",
        "https://www.hdfilmcehennemi.ws/gerilim-filmleri/",
        "https://www.hdfilmcehennemi.ws/bilim-kurgu-filmleri/",
        "https://www.hdfilmcehennemi.ws/fantastik-filmleri/",
        "https://www.hdfilmcehennemi.ws/macera-filmleri/",
        "https://www.hdfilmcehennemi.ws/romantik-filmleri/",
        "https://www.hdfilmcehennemi.ws/korku-filmleri/",
        
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
    
    # 4. Kategori sayfalarını dene
    print("\n4. Testing category pages...")
    categories = [
        "film", "dizi", "aksiyon", "komedi", "dram", "gerilim", 
        "bilim-kurgu", "fantastik", "macera", "romantik", "korku",
        "suç", "biyografi", "tarih", "belgesel", "aile", "animasyon",
        "müzikal", "spor", "savaş", "western", "gizem", "polisiye"
    ]
    
    for category in categories:
        url = f"https://www.hdfilmcehennemi.ws/kategori/{category}/"
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
                    print(f"    Category {category}: Added {len(new_films)} new films, total: {len(all_films)}")
        
        time.sleep(0.3)
    
    return all_films

def scrape_by_popular_films():
    """Popüler filmlerden başlayarak tarar"""
    all_films = []
    
    print("\n5. Scraping by exploring popular film pages...")
    
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

def main():
    # Tüm filmleri topla
    print("Starting comprehensive scraping...")
    
    all_films = []
    
    # Discovery sayfalarını tara
    films1 = scrape_discovery_pages()
    all_films.extend(films1)
    
    # Popüler filmleri tara
    films2 = scrape_by_popular_films()
    all_films.extend(films2)
    
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
    
    # Embed URL'leri al (ilk 50 film için)
    print(f"\nFetching embed URLs (first 50 films)...")
    films_with_embeds = []
    max_to_process = min(50, len(unique_films))
    
    for i, film in enumerate(unique_films[:max_to_process], 1):
        print(f"  [{i}/{max_to_process}] {film['title'][:40]}...")
        
        embed_url = extract_embed_url_from_film_page(film['url'], film.get('token', ''))
        film['embed_url'] = embed_url
        
        films_with_embeds.append(film)
        
        if i < max_to_process:
            time.sleep(0.2)
    
    # Kalan filmleri embed olmadan ekle
    if len(unique_films) > max_to_process:
        remaining = unique_films[max_to_process:]
        for film in remaining:
            film['embed_url'] = None
            films_with_embeds.append(film)
    
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
    
    print(f"\nSUMMARY:")
    print(f"  Total films: {len(films)}")
    print(f"  Films: {films_count}")
    print(f"  Diziler: {diziler_count}")
    print(f"  With embed URLs: {embeds_count}")
    
    # En yüksek IMDB'li filmler
    films_with_imdb = [f for f in films if f['imdb'] != '0.0']
    if films_with_imdb:
        films_with_imdb.sort(key=lambda x: float(x['imdb']), reverse=True)
        print(f"\n  Top 10 films by IMDB:")
        for i, film in enumerate(films_with_imdb[:10], 1):
            title = film['title'][:45] + "..." if len(film['title']) > 45 else film['title']
            year = film.get('year', 'N/A')
            print(f"    {i:2}. {title:50} {year:6} ⭐{film['imdb']}")
    
    # Yıllara göre dağılım
    years = {}
    for film in films:
        year = film.get('year', 'Unknown')
        if year:
            years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\n  Years distribution:")
        sorted_years = sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]
        for year, count in sorted_years:
            print(f"    {year}: {count} films")
    
    print(f"\n{'='*70}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
