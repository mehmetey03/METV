#!/usr/bin/env python3
"""
hdch_fixed.py - Fixed HDFilmCehennemi scraper
"""
import urllib.request
import urllib.error
import json
import re
import time
import ssl
import html
from datetime import datetime

BASE_URL = "https://www.hdfilmcehennemi.ws/"
CATEGORY_URL = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"

# Create an unverified SSL context
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def get_html(url):
    """Fetch HTML content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def clean_text(text):
    """Clean and decode HTML entities in text"""
    if not text:
        return ""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_films_from_html(html_content):
    """Extract films from HTML with improved parsing"""
    films = []
    
    if not html_content:
        return films
    
    # Find the posters container
    container_match = re.search(r'<div class="posters-[^"]*"[^>]*>(.*?)</div>\s*</div>', html_content, re.DOTALL)
    if not container_match:
        # Try alternative pattern
        container_match = re.search(r'<div[^>]*class="[^"]*posters[^"]*"[^>]*>(.*?)</div>\s*</div>', html_content, re.DOTALL)
    
    container_html = container_match.group(1) if container_match else html_content
    
    # Find all poster links - improved pattern
    film_blocks = re.findall(r'<a\s+[^>]*class="[^"]*poster[^"]*"[^>]*>.*?</a>', container_html, re.DOTALL)
    
    print(f"Found {len(film_blocks)} film blocks")
    
    for block in film_blocks:
        film = parse_film_block_improved(block)
        if film:
            films.append(film)
    
    return films

def parse_film_block_improved(block):
    """Improved film block parsing"""
    try:
        # Extract URL
        url_match = re.search(r'href="([^"]*)"', block)
        if not url_match:
            return None
        url = url_match.group(1)
        
        # Extract title from title attribute first
        title = ''
        title_attr_match = re.search(r'title="([^"]*)"', block)
        if title_attr_match:
            title = clean_text(title_attr_match.group(1))
        
        # Also try to get title from poster-title class
        if not title:
            title_match = re.search(r'<strong[^>]*class="[^"]*poster-title[^"]*"[^>]*>(.*?)</strong>', block, re.DOTALL)
            if title_match:
                title = clean_text(title_match.group(1))
        
        if not title:
            return None
        
        # Extract year - look for 4-digit number in a span
        year = ''
        year_match = re.search(r'<span>\s*(\d{4})\s*</span>', block)
        if year_match:
            year = year_match.group(1)
        
        # Fix IMDB rating extraction - look for the actual rating
        imdb = '0.0'
        # Pattern 1: Look for imdb class with rating
        imdb_match = re.search(r'<span[^>]*class="[^"]*imdb[^"]*"[^>]*>.*?(\d+\.\d+|\d+)', block, re.DOTALL)
        if imdb_match:
            imdb_val = imdb_match.group(1)
            try:
                # Validate it's a reasonable IMDB rating (0-10)
                imdb_float = float(imdb_val)
                if 0 <= imdb_float <= 10:
                    imdb = f"{imdb_float:.1f}"
            except:
                pass
        
        # Pattern 2: Look for SVG star icon followed by rating
        if imdb == '0.0':
            svg_imdb_match = re.search(r'<svg[^>]*><path d="[^"]*"></path></svg>\s*<p>\s*(\d+\.\d+)\s*</p>', block, re.DOTALL)
            if svg_imdb_match:
                imdb_val = svg_imdb_match.group(1)
                try:
                    imdb_float = float(imdb_val)
                    if 0 <= imdb_float <= 10:
                        imdb = f"{imdb_float:.1f}"
                except:
                    pass
        
        # Extract image
        image = ''
        img_match = re.search(r'src="([^"]+\.webp)"', block)
        if img_match:
            image = img_match.group(1)
        
        # Extract comments count
        comments = '0'
        comment_match = re.search(r'<svg[^>]*>.*?</svg>\s*(\d+)', block, re.DOTALL)
        if comment_match:
            comments = comment_match.group(1)
        
        # Extract language
        language = ''
        lang_match = re.search(r'<span[^>]*class="[^"]*poster-lang[^"]*"[^>]*>.*?<span>\s*(.*?)\s*</span>', block, re.DOTALL)
        if lang_match:
            language = clean_text(lang_match.group(1))
        
        # Determine type
        film_type = 'dizi' if '/dizi/' in url else 'film'
        
        # Extract token if available
        token = ''
        token_match = re.search(r'data-token="(\d+)"', block)
        if token_match:
            token = token_match.group(1)
        
        # Clean up title (remove common suffixes)
        title = re.sub(r'\s*(?:izle|türkçe|dublaj|altyazı|yabancı|dizi|film)\s*$', '', title, flags=re.IGNORECASE)
        title = title.strip()
        
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
            'scraped_at': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error parsing film: {e}")
        return None

def scrape_multiple_pages(base_url, max_pages=3):
    """Scrape multiple pages with pagination"""
    all_films = []
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page}/"
        
        print(f"\nScraping page {page}: {url}")
        html_content = get_html(url)
        
        if not html_content:
            print(f"  Failed to fetch page {page}")
            break
        
        films = extract_films_from_html(html_content)
        
        if not films:
            print(f"  No films found on page {page}")
            break
        
        all_films.extend(films)
        print(f"  Found {len(films)} films on page {page}")
        
        # Check if we should continue (look for next page)
        if page == 1:
            next_page_match = re.search(r'href="[^"]*page/2/', html_content)
            if not next_page_match:
                print("  No more pages found")
                break
        
        time.sleep(1)  # Be polite
    
    return all_films

def main():
    print("=" * 70)
    print("HDFilmCehennemi Scraper - Fixed Version")
    print("=" * 70)
    
    # Scrape the category
    print(f"\nScraping category: {CATEGORY_URL}")
    films = scrape_multiple_pages(CATEGORY_URL, max_pages=2)
    
    if not films:
        print("\n❌ No films found!")
        return
    
    # Remove duplicates by URL
    unique_films = []
    seen_urls = set()
    
    for film in films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\nTotal unique films: {len(unique_films)}")
    
    # Save results
    result = {
        'metadata': {
            'scraped_at': datetime.now().isoformat(),
            'source_url': CATEGORY_URL,
            'total_films': len(unique_films),
            'films_count': len([f for f in unique_films if f['type'] == 'film']),
            'diziler_count': len([f for f in unique_films if f['type'] == 'dizi'])
        },
        'films': unique_films
    }
    
    output_file = 'hdfilms_fixed.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
        return
    
    # Print detailed summary
    print("\n" + "=" * 70)
    print("DETAILED SUMMARY")
    print("=" * 70)
    
    # Count by type
    films_count = len([f for f in unique_films if f['type'] == 'film'])
    diziler_count = len([f for f in unique_films if f['type'] == 'dizi'])
    
    print(f"Total: {len(unique_films)}")
    print(f"Films: {films_count}")
    print(f"Diziler: {diziler_count}")
    
    # Years distribution
    years = {}
    for film in unique_films:
        year = film.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\nYears distribution ({len(years)} different years):")
        sorted_years = sorted([(y, c) for y, c in years.items() if y != '' and y != 'Unknown'], 
                            key=lambda x: x[1], reverse=True)
        for year, count in sorted_years:
            print(f"  {year}: {count} films")
    
    # IMDB statistics
    films_with_imdb = [f for f in unique_films if f.get('imdb', '0.0') not in ['0.0', '0', '', '316.9']]
    print(f"\nFilms with valid IMDB ratings: {len(films_with_imdb)}")
    
    if films_with_imdb:
        # Sort by IMDB
        films_with_imdb.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
        
        print("\nTop films by IMDB rating:")
        for idx, film in enumerate(films_with_imdb[:10], 1):
            print(f"{idx:2}. {film['title'][:40]:40} ({film.get('year', 'N/A'):4}) - IMDB: {film['imdb']}")
    
    # Show all films with corrected data
    print(f"\nAll films ({len(unique_films)} total):")
    print("-" * 80)
    print(f"{'No.':3} {'Title':40} {'Year':6} {'IMDB':6} {'Type':6} {'Lang':10}")
    print("-" * 80)
    
    for i, film in enumerate(unique_films, 1):
        title = film['title'][:38] + "..." if len(film['title']) > 38 else film['title']
        year = film.get('year', 'N/A')
        imdb = film.get('imdb', '0.0')
        # Highlight suspicious IMDB ratings
        if imdb == '316.9':
            imdb = 'N/A*'
        film_type = film.get('type', 'film')[:6]
        lang = film.get('language', '')[:8]
        
        print(f"{i:3} {title:40} {year:6} {imdb:6} {film_type:6} {lang:10}")
    
    print("-" * 80)
    if any(f.get('imdb') == '316.9' for f in unique_films):
        print("* IMDB ratings marked as 'N/A*' are showing incorrect values (316.9)")
    
    print(f"\n{'='*70}")
    print("SCRAPING COMPLETE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
