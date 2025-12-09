#!/usr/bin/env python3
"""
hdfilm_simple.py - Simple but effective HDFilmCehennemi scraper
"""
import requests
import json
import re
import time
from urllib.parse import urljoin
import argparse
import logging

# -----------------------
# CONFIG
# -----------------------
BASE_URL = "https://www.hdfilmcehennemi.ws/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
}

# -----------------------
# Setup
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

session = requests.Session()
session.headers.update(HEADERS)

def get_page_html(url):
    """Get HTML content of a page"""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def extract_films_smartly(html):
    """Smart extraction using regex patterns"""
    films = []
    
    if not html:
        return films
    
    # Pattern 1: Look for film/dizi links with basic info
    # This pattern looks for links to film/dizi pages
    link_pattern = r'<a\s+[^>]*href="(https?://[^"]*/(?:film|dizi)/[^"]*)"[^>]*>([\s\S]*?)</a>'
    
    matches = re.finditer(link_pattern, html, re.IGNORECASE)
    
    for match in matches:
        try:
            url = match.group(1)
            content = match.group(2)
            
            # Skip if it's just an image link
            if '<img' in content and len(content.strip()) < 100:
                continue
            
            # Extract title - clean up HTML tags
            title = re.sub(r'<[^>]+>', ' ', content)
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Remove common suffixes
            title = re.sub(r'\s*(?:izle|türkçe|dublaj|altyazı|yabancı|dizi|film)\s*$', '', title, flags=re.IGNORECASE)
            title = title.strip()
            
            if not title or len(title) < 2:
                continue
            
            # Extract image
            image = ''
            img_match = re.search(r'src="([^"]+\.(?:jpg|jpeg|png|webp))"', content)
            if img_match:
                image = img_match.group(1)
            
            # Extract year from URL or title
            year = ''
            year_match = re.search(r'/(\d{4})/', url)
            if not year_match:
                year_match = re.search(r'\b(19|20)\d{2}\b', title)
            if year_match:
                year = year_match.group(1)
            
            # Determine type
            film_type = 'dizi' if '/dizi/' in url else 'film'
            
            # Simple IMDB extraction
            imdb = '0.0'
            imdb_match = re.search(r'IMDB\s*[:]?\s*([\d\.]+)', content, re.IGNORECASE)
            if imdb_match:
                try:
                    imdb_val = float(imdb_match.group(1))
                    if 1.0 <= imdb_val <= 10.0:
                        imdb = f"{imdb_val:.1f}"
                except:
                    pass
            
            films.append({
                'url': url,
                'title': title[:200],  # Limit title length
                'image': image,
                'year': year,
                'imdb': imdb,
                'type': film_type,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            logger.debug(f"Error processing match: {e}")
            continue
    
    # If we didn't find enough films, try another approach
    if len(films) < 3:
        # Look for JSON-LD data (structured data)
        jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>'
        jsonld_matches = re.findall(jsonld_pattern, html)
        
        for jsonld in jsonld_matches:
            try:
                data = json.loads(jsonld)
                if isinstance(data, dict) and data.get('@type') in ['Movie', 'TVSeries']:
                    film = {
                        'url': data.get('url', ''),
                        'title': data.get('name', ''),
                        'image': data.get('image', ''),
                        'year': data.get('dateCreated', '')[:4] if data.get('dateCreated') else '',
                        'imdb': str(data.get('aggregateRating', {}).get('ratingValue', '0.0')),
                        'type': 'dizi' if data.get('@type') == 'TVSeries' else 'film',
                        'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    if film['url'] and film['title']:
                        films.append(film)
            except:
                pass
    
    return films

def get_category_links():
    """Get links from category pages"""
    categories = []
    
    # Try to find category links in homepage
    html = get_page_html(BASE_URL)
    if html:
        # Look for category links
        cat_pattern = r'<a\s+[^>]*href="(https?://[^"]*/kategori/[^"]*)"[^>]*>([^<]+)</a>'
        cat_matches = re.findall(cat_pattern, html, re.IGNORECASE)
        
        for url, name in cat_matches:
            if 'film' in name.lower() or 'dizi' in name.lower():
                categories.append((url, name.strip()))
    
    return categories[:5]  # Limit to 5 categories

def scrape_category(url, category_name):
    """Scrape films from a category page"""
    films = []
    
    html = get_page_html(url)
    if html:
        films = extract_films_smartly(html)
        logger.info(f"Found {len(films)} films in category: {category_name}")
    
    return films

def main():
    parser = argparse.ArgumentParser(description='Simple HDFilmCehennemi Scraper')
    parser.add_argument('--output', default='hdfilms.json', help='Output JSON file')
    parser.add_argument('--categories', action='store_true', help='Also scrape category pages')
    
    args = parser.parse_args()
    
    print(f"""
    Simple HDFilmCehennemi Scraper
    ==============================
    Output: {args.output}
    Scrape categories: {args.categories}
    """)
    
    all_films = []
    
    # 1. Scrape homepage
    print("\n1. Scraping homepage...")
    html = get_page_html(BASE_URL)
    if html:
        homepage_films = extract_films_smartly(html)
        all_films.extend(homepage_films)
        print(f"   Found {len(homepage_films)} films on homepage")
    
    # 2. Scrape category pages if requested
    if args.categories and all_films:
        print("\n2. Scraping category pages...")
        categories = get_category_links()
        
        for url, name in categories:
            print(f"   Scraping: {name}")
            category_films = scrape_category(url, name)
            all_films.extend(category_films)
            time.sleep(1)  # Be polite
    
    # Remove duplicates
    unique_films = []
    seen_urls = set()
    
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\nTotal unique films: {len(unique_films)}")
    
    if not unique_films:
        print("\n❌ No films found!")
        return
    
    # Organize data
    result = {
        'metadata': {
            'total_films': len(unique_films),
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': BASE_URL
        },
        'films': unique_films
    }
    
    # Save to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to: {args.output}")
    
    # Print nice summary
    print("\n" + "="*60)
    print("FILMS FOUND")
    print("="*60)
    
    films_count = len([f for f in unique_films if f['type'] == 'film'])
    diziler_count = len([f for f in unique_films if f['type'] == 'dizi'])
    
    print(f"Total: {len(unique_films)}")
    print(f"Films: {films_count}")
    print(f"Diziler: {diziler_count}")
    
    # Group by year
    years = {}
    for film in unique_films:
        year = film.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\nBy year:")
        for year, count in sorted(years.items()):
            if year and year != 'Unknown':
                print(f"  {year}: {count}")
    
    # Show sample
    print(f"\nSample films ({min(5, len(unique_films))} of {len(unique_films)}):")
    for i, film in enumerate(unique_films[:5], 1):
        title = film['title'][:50] + "..." if len(film['title']) > 50 else film['title']
        imdb = f"IMDB: {film['imdb']}" if film['imdb'] != '0.0' else ""
        year = f"({film['year']})" if film['year'] else ""
        print(f"  {i}. {title} {year} {imdb}")

if __name__ == '__main__':
    main()
