#!/usr/bin/env python3
"""
hdch_final.py - HDFilmCehennemi scraper with load-more support
"""
import urllib.request
import urllib.parse
import json
import re
import html
import time
import math
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.hdfilmcehennemi.ws/"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"
API_URL = "https://www.hdfilmcehennemi.ws/ajax/discover"

def get_html(url, headers=None):
    """Get HTML content"""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': BASE_URL,
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def post_data(url, data, headers=None):
    """POST request gönder"""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.hdfilmcehennemi.ws',
        'Referer': BASE_URL,
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded, headers=default_headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  POST error to {url}: {e}")
        return None

def extract_films_from_html(html_content, source_url):
    """Extract films from HTML"""
    films = []
    
    if not html_content:
        return films
    
    # Pattern 1: Look for film posters with data-token
    film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
    film_matches = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    print(f"  Found {len(film_matches)} film posters")
    
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
            # Try alternative pattern
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
        
        # Comments count
        comments = '0'
        comment_match = re.search(r'<svg[^>]*>.*?</svg>\s*(\d+)', poster_html, re.DOTALL)
        if comment_match:
            comments = comment_match.group(1)
        
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
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', poster_html)
        if token_match:
            token = token_match.group(1)
        
        # Type
        film_type = 'dizi' if '/dizi/' in url or 'dizi' in source_url.lower() else 'film'
        
        return {
            'url': url,
            'title': title,
            'year': year,
            'imdb': imdb,
            'image': image,
            'comments': comments,
            'language': language,
            'type': film_type,
            'token': token,
            'source': source_url,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"    Error parsing poster: {e}")
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
    
    # Remove year in parentheses
    title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
    
    # Clean up spaces
    title = re.sub(r'\s+', ' ', title).strip()
    
    return title

def extract_embed_url_from_film_page(film_url, token):
    """Extract embed URL from individual film page"""
    print(f"    Fetching embed for: {film_url}")
    
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
    
    # Pattern 3: video-container div içinde
    container_pattern = r'<div[^>]*class="[^"]*video-container[^"]*"[^>]*>.*?(https://hdfilmcehennemi\.mobi/video/embed/[^<]+)'
    container_match = re.search(container_pattern, html_content, re.DOTALL | re.IGNORECASE)
    if container_match:
        return container_match.group(1).strip()
    
    # Pattern 4: GKsnOLw2hsT pattern
    gksn_pattern = r'(GKsnOLw2hsT[^"\']*)'
    gksn_match = re.search(gksn_pattern, html_content)
    if gksn_match:
        embed_code = gksn_match.group(1)
        # Format: GKsnOLw2hsT/?rapidrame_id=TOKEN
        embed_match = re.search(r'([A-Za-z0-9_\-]+)/\?rapidrame_id=([A-Za-z0-9]+)', embed_code)
        if embed_match:
            embed_path = embed_match.group(1)
            rapidrame_id = embed_match.group(2)
            return f"{EMBED_BASE}{embed_path}/?rapidrame_id={rapidrame_id}"
    
    # Pattern 5: Construct from token
    if token:
        return f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={token}"
    
    return None

def scrape_with_load_more(base_url, max_items=100):
    """Load more butonunu simüle ederek tüm filmleri çek"""
    all_films = []
    page = 1
    
    print(f"\nScraping with load-more: {base_url}")
    
    # İlk sayfayı al
    html_content = get_html(base_url)
    if not html_content:
        return all_films
    
    # İlk sayfadaki filmleri çıkar
    films = extract_films_from_html(html_content, base_url)
    all_films.extend(films)
    print(f"  Page {page}: {len(films)} films")
    
    # Load more butonu için gerekli parametreleri bul
    # data-discover-more attribute'ünden parametreleri al
    discover_match = re.search(r'data-discover-more="([^"]+)"', html_content)
    if not discover_match:
        print("  No load-more button found, using manual pagination")
        return scrape_with_pagination(base_url, max_items)
    
    discover_data = discover_match.group(1)
    print(f"  Discover data: {discover_data}")
    
    # JSON formatına çevir
    try:
        import ast
        discover_dict = ast.literal_eval(discover_data.replace('&quot;', '"'))
    except:
        print("  Could not parse discover data")
        return all_films
    
    # Load more döngüsü
    total_loaded = len(films)
    
    while total_loaded < max_items:
        page += 1
        print(f"  Loading more... Page {page}")
        
        # POST data hazırla
        post_data_dict = {
            'action': 'discover',
            'page': str(page),
            'type': discover_dict.get('type', 'movie'),
            'category': discover_dict.get('category', ''),
            'genre': discover_dict.get('genre', ''),
            'country': discover_dict.get('country', ''),
            'year': discover_dict.get('year', ''),
            'imdb': discover_dict.get('imdb', ''),
            'sort': discover_dict.get('sort', ''),
        }
        
        # POST isteği gönder
        response = post_data(API_URL, post_data_dict)
        if not response:
            print(f"    Failed to load page {page}")
            break
        
        try:
            # JSON response'u parse et
            response_data = json.loads(response)
            if response_data.get('success') and response_data.get('html'):
                # Yeni filmleri çıkar
                new_films = extract_films_from_html(response_data['html'], f"{base_url}?page={page}")
                
                if not new_films:
                    print(f"    No more films found")
                    break
                
                all_films.extend(new_films)
                total_loaded += len(new_films)
                print(f"    Added {len(new_films)} films, total: {total_loaded}")
                
                # Be polite
                time.sleep(1)
            else:
                print(f"    API error: {response_data.get('message', 'Unknown error')}")
                break
                
        except json.JSONDecodeError:
            print(f"    Invalid JSON response")
            break
        except Exception as e:
            print(f"    Error processing response: {e}")
            break
    
    return all_films

def scrape_with_pagination(base_url, max_items=100):
    """Manuel pagination ile çek"""
    all_films = []
    
    for page in range(1, 10):  # Max 10 sayfa
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page}/"
        
        print(f"  Page {page}: {url}")
        
        html_content = get_html(url)
        if not html_content:
            print(f"    Failed to fetch page {page}")
            break
        
        films = extract_films_from_html(html_content, url)
        
        if not films:
            print(f"    No films found on page {page}")
            break
        
        all_films.extend(films)
        print(f"    Found {len(films)} films, total: {len(all_films)}")
        
        if len(all_films) >= max_items:
            print(f"    Reached max items limit: {max_items}")
            break
        
        # Be polite
        time.sleep(1)
    
    return all_films

def scrape_all_films():
    """Tüm filmleri çek"""
    all_films = []
    
    # Farklı URL'lerden çek
    urls_to_scrape = [
        ("https://www.hdfilmcehennemi.ws/", "homepage", 50),
        ("https://www.hdfilmcehennemi.ws/filmler/", "films", 100),
        ("https://www.hdfilmcehennemi.ws/diziler/", "series", 50),
        ("https://www.hdfilmcehennemi.ws/populer-filmler/", "popular", 30),
        ("https://www.hdfilmcehennemi.ws/yeni-filmler/", "new", 30),
    ]
    
    for url, name, limit in urls_to_scrape:
        print(f"\nScraping {name}: {url}")
        films = scrape_with_load_more(url, limit)
        
        if films:
            # Benzersiz filmleri ekle
            existing_urls = {f['url'] for f in all_films}
            for film in films:
                if film['url'] not in existing_urls:
                    all_films.append(film)
                    existing_urls.add(film['url'])
            
            print(f"  Added {len(films)} films from {name}, total unique: {len(all_films)}")
        else:
            print(f"  No films found from {name}")
        
        time.sleep(2)
    
    return all_films

def main():
    print("=" * 70)
    print("HDFilmCehennemi Advanced Scraper")
    print("=" * 70)
    
    # Tüm filmleri çek
    all_films = scrape_all_films()
    
    if not all_films:
        print("\n❌ No films found!")
        return
    
    print(f"\n{'='*70}")
    print(f"Found {len(all_films)} unique films")
    print(f"{'='*70}")
    
    # Embed URL'leri al
    print(f"\nFetching embed URLs...")
    films_with_embeds = []
    
    for i, film in enumerate(all_films, 1):
        print(f"  [{i}/{len(all_films)}] {film['title'][:40]}...")
        
        embed_url = extract_embed_url_from_film_page(film['url'], film.get('token', ''))
        film['embed_url'] = embed_url
        
        if embed_url:
            print(f"    ✓ Embed found")
        else:
            print(f"    ✗ No embed found")
        
        films_with_embeds.append(film)
        
        # Be polite
        if i < len(all_films):
            time.sleep(0.3)
    
    # Count films with embeds
    films_with_embeds_count = sum(1 for f in films_with_embeds if f.get('embed_url'))
    
    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Total unique films: {len(films_with_embeds)}")
    print(f"Films with embed URLs: {films_with_embeds_count}")
    
    # Save results
    save_results(films_with_embeds)
    
    # Print summary
    print_summary(films_with_embeds)

def save_results(films):
    """Save results to files"""
    # Complete results
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
    
    # GitHub Actions file
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
    print(f"  Total: {len(films)}")
    print(f"  Films: {films_count}")
    print(f"  Diziler: {diziler_count}")
    print(f"  With embeds: {embeds_count}")
    
    # Sample films
    print(f"\n  Sample films (first 20):")
    for i, film in enumerate(films[:20], 1):
        title = film['title'][:45] + "..." if len(film['title']) > 45 else film['title']
        year = film.get('year', 'N/A')
        imdb = f"⭐{film['imdb']}" if film['imdb'] != '0.0' else ""
        embed = "✓" if film.get('embed_url') else "✗"
        type_icon = "🎬" if film['type'] == 'film' else "📺"
        print(f"    {i:2}. [{embed}] {type_icon} {title:48} {year:6} {imdb}")
    
    # Films with highest IMDB
    films_with_imdb = [f for f in films if f['imdb'] != '0.0']
    if films_with_imdb:
        films_with_imdb.sort(key=lambda x: float(x['imdb']), reverse=True)
        print(f"\n  Top films by IMDB:")
        for i, film in enumerate(films_with_imdb[:10], 1):
            title = film['title'][:40] + "..." if len(film['title']) > 40 else film['title']
            year = film.get('year', 'N/A')
            print(f"    {i:2}. {title:45} {year:6} ⭐{film['imdb']}")
    
    # Distribution by year
    years = {}
    for film in films:
        year = film.get('year', 'Unknown')
        if year:
            years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\n  Years distribution (top 10):")
        sorted_years = sorted(years.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=True)[:10]
        for year, count in sorted_years:
            print(f"    {year}: {count} films")
    
    print(f"\n{'='*70}")
    print("DONE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
