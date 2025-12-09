#!/usr/bin/env python3
"""
hdch_final.py - HDFilmCehennemi scraper with embed URLs
"""
import urllib.request
import urllib.parse
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.hdfilmcehennemi.ws/"
EMBED_BASE_URL = "https://hdfilmcehennemi.mobi/video/embed/"

CATEGORIES = {
    'film': 'https://www.hdfilmcehennemi.ws/category/film-izle-2/',
    'dizi': 'https://www.hdfilmcehennemi.ws/category/dizi-izle-2/',
    'yerli-film': 'https://www.hdfilmcehennemi.ws/category/yerli-film-izle/',
    'yabanci-dizi': 'https://www.hdfilmcehennemi.ws/category/yabanci-dizi-izle/',
}

def get_html(url):
    """Get HTML content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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

def extract_embed_url(film_url, token):
    """Extract embed URL from film detail page"""
    print(f"    Fetching embed for: {film_url}")
    
    html_content = get_html(film_url)
    if not html_content:
        return None
    
    embed_url = None
    
    # Method 1: Look for iframe embed
    iframe_pattern = r'<iframe[^>]*src="([^"]*)"[^>]*>'
    iframe_matches = re.findall(iframe_pattern, html_content, re.IGNORECASE)
    
    for iframe_src in iframe_matches:
        if 'hdfilmcehennemi.mobi/video/embed/' in iframe_src:
            embed_url = iframe_src
            break
    
    # Method 2: Look for GKsnOLw2hsT pattern in script tags
    if not embed_url:
        script_pattern = r'<script[^>]*>.*?(GKsnOLw2hsT[^"\']*).*?</script>'
        script_matches = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in script_matches:
            if 'GKsnOLw2hsT' in match:
                # Extract the embed code
                embed_code_match = re.search(r'([A-Za-z0-9_\-]+)/\?rapidrame_id=([A-Za-z0-9]+)', match)
                if embed_code_match:
                    embed_path = embed_code_match.group(1)
                    rapidrame_id = embed_code_match.group(2)
                    embed_url = f"{EMBED_BASE_URL}{embed_path}/?rapidrame_id={rapidrame_id}"
                    break
    
    # Method 3: Try to construct from token
    if not embed_url and token:
        # Try common embed patterns
        possible_embeds = [
            f"{EMBED_BASE_URL}GKsnOLw2hsT/?rapidrame_id={token}",
            f"{EMBED_BASE_URL}{token}/",
            f"https://hdfilmcehennemi.mobi/embed/{token}",
        ]
        
        for test_embed in possible_embeds:
            # Quick check if the URL might exist
            if 'GKsnOLw2hsT' in test_embed or token in test_embed:
                embed_url = test_embed
                break
    
    return embed_url

def extract_films(html_content, source_url):
    """Extract films from HTML"""
    films = []
    
    if not html_content:
        return films
    
    # Pattern for film items - more comprehensive
    film_pattern = r'<article[^>]*>.*?</article>'
    articles = re.findall(film_pattern, html_content, re.DOTALL)
    
    print(f"  Found {len(articles)} articles")
    
    for article in articles:
        film = parse_film_article(article, source_url)
        if film:
            films.append(film)
    
    return films

def parse_film_article(article, source_url):
    """Parse a film article"""
    try:
        # URL
        url_match = re.search(r'href="([^"]+)"', article)
        if not url_match:
            return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # Title from h2/h3
        title = ''
        title_match = re.search(r'<h[23][^>]*>\s*<a[^>]*>(.*?)</a>\s*</h[23]>', article, re.DOTALL)
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            title = html.unescape(title)
        
        # Alternative: title from alt attribute
        if not title:
            img_match = re.search(r'<img[^>]*alt="([^"]+)"[^>]*>', article)
            if img_match:
                title = html.unescape(img_match.group(1)).strip()
        
        if not title:
            return None
        
        # Clean title
        title = re.sub(r'\s*\(?\d{4}\)?\s*$', '', title)
        title = re.sub(r'\s*(?:izle|türkçe|dublaj|altyazı|yabancı|dizi|film|hd|full)\s*$', '', title, flags=re.IGNORECASE)
        title = title.strip()
        
        # Year
        year = ''
        year_match = re.search(r'<span[^>]*>\s*(\d{4})\s*</span>', article)
        if year_match:
            year = year_match.group(1)
        else:
            # Try to extract year from title
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                year = year_match.group(1)
        
        # IMDB rating
        imdb = '0.0'
        imdb_match = re.search(r'imdb[^>]*>.*?(\d+\.\d+)', article, re.IGNORECASE | re.DOTALL)
        if not imdb_match:
            imdb_match = re.search(r'(\d+\.\d+)\s*/?\s*10', article)
        
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    imdb = f"{rating:.1f}"
            except:
                pass
        
        # Image
        image = ''
        img_match = re.search(r'<img[^>]*src="([^"]+\.(?:webp|jpg|jpeg|png))"[^>]*>', article)
        if img_match:
            image = img_match.group(1)
            if not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', article)
        if token_match:
            token = token_match.group(1)
        else:
            # Extract token from URL
            token_match = re.search(r'/(\d+)(?:-|$|/)', url)
            if token_match:
                token = token_match.group(1)
        
        # Type
        film_type = 'dizi' if '/dizi/' in url or 'dizi' in source_url.lower() else 'film'
        
        # Language
        language = ''
        if 'türkçe' in article.lower() or 'dublaj' in article.lower():
            language = 'Türkçe Dublaj'
        elif 'altyazı' in article.lower():
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
        print(f"    Error parsing article: {e}")
        return None

def scrape_category(category_url, category_name, max_pages=2):
    """Scrape a category with pagination"""
    all_films = []
    
    print(f"\nScraping category: {category_name}")
    print(f"URL: {category_url}")
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = category_url
        else:
            url = f"{category_url}page/{page}/"
        
        print(f"  Page {page}: {url}")
        
        html_content = get_html(url)
        if not html_content:
            print(f"    Failed to fetch page {page}")
            break
        
        films = extract_films(html_content, url)
        
        if not films:
            print(f"    No films found on page {page}")
            if page == 1:
                continue  # Try next page
            else:
                break
        
        all_films.extend(films)
        print(f"    Found {len(films)} films")
        
        # Be polite
        time.sleep(1.5)
    
    print(f"  Total from {category_name}: {len(all_films)} films")
    return all_films

def main():
    print("=" * 70)
    print("HDFilmCehennemi Scraper with Embed URLs")
    print("=" * 70)
    
    all_films = []
    
    # Scrape each category
    for cat_name, cat_url in CATEGORIES.items():
        category_films = scrape_category(cat_url, cat_name, max_pages=2)
        all_films.extend(category_films)
        time.sleep(2)
    
    if not all_films:
        print("\n❌ No films found!")
        return
    
    # Remove duplicates by URL
    unique_films = []
    seen_urls = set()
    
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\n{'='*70}")
    print(f"Fetching embed URLs for {len(unique_films)} films...")
    print(f"{'='*70}")
    
    # Fetch embed URLs for each film
    films_with_embeds = []
    for i, film in enumerate(unique_films, 1):
        print(f"  [{i}/{len(unique_films)}] {film['title'][:40]}...")
        
        embed_url = extract_embed_url(film['url'], film.get('token', ''))
        
        if embed_url:
            film['embed_url'] = embed_url
            print(f"    ✓ Found embed: {embed_url[:60]}...")
        else:
            film['embed_url'] = None
            print(f"    ✗ No embed found")
        
        films_with_embeds.append(film)
        
        # Be polite when fetching embeds
        if i < len(unique_films):
            time.sleep(0.5)
    
    # Count films with embeds
    films_with_embeds_count = sum(1 for f in films_with_embeds if f.get('embed_url'))
    
    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Total unique films: {len(films_with_embeds)}")
    print(f"Films with embed URLs: {films_with_embeds_count}")
    
    # Save complete results
    output_file = 'hdfilms_with_embeds.json'
    try:
        result = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(films_with_embeds),
                'films_with_embeds': films_with_embeds_count,
                'source': 'hdfilmcehennemi.ws',
                'categories': list(CATEGORIES.keys())
            },
            'films': films_with_embeds
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
    
    # Save simple version for GitHub Actions
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
                'image': film.get('image', '')
            })
        
        with open('hdceh_embeds.json', 'w', encoding='utf-8') as f:
            json.dump(simple_data, f, ensure_ascii=False, indent=2)
        print(f"✅ GitHub Actions file saved to: hdceh_embeds.json")
    except Exception as e:
        print(f"❌ Error saving GitHub Actions file: {e}")
    
    # Print summary
    if films_with_embeds:
        print(f"\nSample of films with embeds:")
        print("-" * 80)
        
        films_with_embeds_list = [f for f in films_with_embeds if f.get('embed_url')]
        if films_with_embeds_list:
            for i, film in enumerate(films_with_embeds_list[:15], 1):
                title = film['title'][:40] + "..." if len(film['title']) > 40 else film['title']
                year = film.get('year', 'N/A')
                embed_short = film['embed_url'][:50] + "..." if len(film['embed_url']) > 50 else film['embed_url']
                print(f"{i:2}. {title:45} {year:6}")
                print(f"    {embed_short}")
        else:
            print("No films with embed URLs found")
        
        print(f"\n{'='*70}")
        print("DONE!")
        print(f"{'='*70}")

if __name__ == '__main__':
    main()
