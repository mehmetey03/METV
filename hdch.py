#!/usr/bin/env python3
"""
hdfilm_nodeps.py - HDFilmCehennemi scraper with no external dependencies
"""
import urllib.request
import urllib.error
import json
import re
import time
import ssl
from datetime import datetime

BASE_URL = "https://www.hdfilmcehennemi.ws/"
CATEGORY_URL = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"

# Create an unverified SSL context to avoid certificate issues
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_html(url):
    """Fetch HTML content using only built-in modules"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        
        # Use the unverified SSL context
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            return html
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {url}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error for {url}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_films_from_html(html):
    """Extract films from HTML using regex"""
    films = []
    
    if not html:
        return films
    
    # Find all film blocks (anchor tags with class poster)
    # Pattern: <a class="poster" ...> ... </a>
    film_pattern = r'<a\s+[^>]*class="poster"[^>]*>.*?</a>'
    film_blocks = re.findall(film_pattern, html, re.DOTALL | re.IGNORECASE)
    
    print(f"Found {len(film_blocks)} potential film blocks")
    
    for block in film_blocks:
        film = parse_film_block(block)
        if film:
            films.append(film)
    
    return films

def parse_film_block(block):
    """Parse a single film block HTML"""
    try:
        # Extract URL
        url_match = re.search(r'href="([^"]*)"', block)
        if not url_match:
            return None
        url = url_match.group(1)
        
        # Extract title from title attribute
        title_match = re.search(r'title="([^"]*)"', block)
        title = title_match.group(1) if title_match else ''
        
        # Extract title from <strong class="poster-title">
        title_strong_match = re.search(r'<strong[^>]*class="poster-title"[^>]*>(.*?)</strong>', block, re.DOTALL)
        if title_strong_match:
            # Clean HTML tags from title
            strong_title = re.sub(r'<[^>]+>', '', title_strong_match.group(1)).strip()
            if strong_title:
                title = strong_title
        
        if not title:
            return None
        
        # Extract year
        year = ''
        # Look for <span>2025</span> pattern
        year_match = re.search(r'<span>\s*(\d{4})\s*</span>', block)
        if year_match:
            year = year_match.group(1)
        
        # Extract IMDB rating
        imdb = '0.0'
        # Look for imdb class
        imdb_match = re.search(r'<span[^>]*class="imdb"[^>]*>.*?(\d+\.\d+)', block, re.DOTALL)
        if imdb_match:
            imdb = imdb_match.group(1)
        
        # Extract image
        image = ''
        img_match = re.search(r'src="([^"]+\.webp)"', block)
        if img_match:
            image = img_match.group(1)
        
        # Extract comments count
        comments = '0'
        # Look for number after SVG icon
        comment_match = re.search(r'<svg[^>]*>.*?</svg>\s*(\d+)', block, re.DOTALL)
        if comment_match:
            comments = comment_match.group(1)
        
        # Determine type
        film_type = 'dizi' if '/dizi/' in url else 'film'
        
        # Extract language
        language = ''
        lang_match = re.search(r'<span class="poster-lang">.*?<span>\s*(.*?)\s*</span>', block, re.DOTALL)
        if lang_match:
            language = lang_match.group(1).strip()
        
        return {
            'url': url,
            'title': title.strip(),
            'year': year,
            'imdb': imdb,
            'image': image,
            'comments': comments,
            'language': language,
            'type': film_type,
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error parsing film block: {e}")
        return None

def main():
    print("=" * 60)
    print("HDFilmCehennemi Scraper (No Dependencies)")
    print("=" * 60)
    
    # Test with the category page
    print(f"\nFetching: {CATEGORY_URL}")
    html = get_html(CATEGORY_URL)
    
    if not html:
        print("❌ Failed to fetch the page")
        return
    
    print("✓ Page fetched successfully")
    
    # Try to save HTML for debugging
    try:
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html[:5000])  # Save first 5000 chars for debugging
        print("✓ Saved sample HTML to debug_page.html")
    except:
        pass
    
    # Extract films
    films = extract_films_from_html(html)
    
    print(f"\nFound {len(films)} films")
    
    if not films:
        print("\nNo films found. Possible reasons:")
        print("1. The website structure has changed")
        print("2. The page requires JavaScript")
        print("3. The HTML pattern doesn't match")
        
        # Try alternative extraction method
        print("\nTrying alternative extraction method...")
        
        # Look for any links to film/dizi pages
        film_links = re.findall(r'<a\s+href="([^"]*/(?:film|dizi)/[^"]*)"[^>]*>([^<]+)</a>', html)
        
        print(f"Found {len(film_links)} film/dizi links")
        
        for href, text in film_links[:10]:
            print(f"  - {text[:50]}... -> {href}")
        
        return
    
    # Save results
    result = {
        'metadata': {
            'scraped_at': datetime.now().isoformat(),
            'source_url': CATEGORY_URL,
            'total_films': len(films)
        },
        'films': films
    }
    
    output_file = 'hdfilms_nodeps.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
        return
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    # Count by type
    films_count = len([f for f in films if f['type'] == 'film'])
    diziler_count = len([f for f in films if f['type'] == 'dizi'])
    
    print(f"Total films: {len(films)}")
    print(f"Films: {films_count}")
    print(f"Diziler: {diziler_count}")
    
    # Years
    years = {}
    for film in films:
        year = film.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\nYears distribution:")
        sorted_years = sorted([(y, c) for y, c in years.items() if y != '' and y != 'Unknown'], 
                            key=lambda x: x[1], reverse=True)
        for year, count in sorted_years[:10]:
            print(f"  {year}: {count} films")
    
    # Show sample
    print(f"\nSample films (first 10):")
    for i, film in enumerate(films[:10], 1):
        title = film['title'][:40] + "..." if len(film['title']) > 40 else film['title']
        imdb = f"IMDB: {film['imdb']}" if film['imdb'] != '0.0' else ""
        year = f"({film['year']})" if film['year'] else ""
        print(f"{i:2}. {title:43} {year:8} {imdb}")
    
    print(f"\n{'='*60}")
    print("DONE!")
    print(f"{'='*60}")

def test_simple():
    """Simple test function"""
    print("Simple test - checking if we can access the site...")
    
    test_url = "https://www.hdfilmcehennemi.ws/"
    
    html = get_html(test_url)
    if html:
        print("✓ Successfully accessed the site")
        print(f"Page size: {len(html)} characters")
        print(f"Page contains 'film': {'film' in html.lower()}")
        print(f"Page contains 'dizi': {'dizi' in html.lower()}")
        
        # Save a sample
        with open('test_sample.html', 'w', encoding='utf-8') as f:
            f.write(html[:2000])
        print("✓ Saved sample to test_sample.html")
    else:
        print("✗ Failed to access the site")

if __name__ == '__main__':
    # Uncomment to run a simple test first
    # test_simple()
    
    # Run the main scraper
    main()
