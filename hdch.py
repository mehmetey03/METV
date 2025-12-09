#!/usr/bin/env python3
"""
hdch_simple.py - Simple but reliable HDFilmCehennemi scraper
"""
import urllib.request
import json
import re
import html
from datetime import datetime

def get_html(url):
    """Get HTML with minimal dependencies"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    except:
        return None

def extract_films_directly(html_content):
    """Direct extraction using simpler patterns"""
    films = []
    
    if not html_content:
        return films
    
    # Save HTML for debugging
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(html_content[:10000])  # First 10k chars
    
    # METHOD 1: Look for film blocks with data-token attribute
    # Pattern: <a ... data-token="..." ...> ... </a>
    film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
    film_blocks = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    print(f"Method 1: Found {len(film_blocks)} blocks with data-token")
    
    if film_blocks:
        for block in film_blocks:
            film = parse_film_simple(block)
            if film:
                films.append(film)
    
    # METHOD 2: If first method fails, look for links to film pages
    if not films:
        print("Trying Method 2...")
        # Look for links containing /film/ or /dizi/
        link_pattern = r'<a\s+href="([^"]*/(?:film|dizi)/[^"]*)"[^>]*>(.*?)</a>'
        links = re.findall(link_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"Method 2: Found {len(links)} film/dizi links")
        
        for href, content in links:
            film = parse_from_link(href, content)
            if film:
                films.append(film)
    
    # METHOD 3: Look for any anchor with class containing "poster"
    if not films:
        print("Trying Method 3...")
        poster_pattern = r'<a\s+[^>]*class="[^"]*poster[^"]*"[^>]*>.*?</a>'
        poster_blocks = re.findall(poster_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"Method 3: Found {len(poster_blocks)} poster blocks")
        
        for block in poster_blocks:
            film = parse_film_simple(block)
            if film:
                films.append(film)
    
    return films

def parse_film_simple(block):
    """Simple parsing of film block"""
    try:
        # URL
        url_match = re.search(r'href="([^"]*)"', block)
        if not url_match:
            return None
        url = url_match.group(1)
        
        # Title from title attribute
        title = ''
        title_match = re.search(r'title="([^"]*)"', block)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
        
        # Alternative: get title from text content
        if not title:
            # Remove all HTML tags
            text = re.sub(r'<[^>]+>', ' ', block)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 5 and len(text) < 100:
                title = text
        
        if not title:
            return None
        
        # Year - look for 4-digit number
        year = ''
        year_match = re.search(r'\b(19|20)\d{2}\b', block)
        if year_match:
            year = year_match.group(0)
        
        # IMDB - look for pattern like 8.0 or 7.5
        imdb = '0.0'
        imdb_match = re.search(r'(\d+\.\d+)\s*(?:/10)?', block)
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    imdb = f"{rating:.1f}"
            except:
                pass
        
        # Image
        image = ''
        img_match = re.search(r'src="([^"]+\.(?:webp|jpg|jpeg|png))"', block)
        if img_match:
            image = img_match.group(1)
        
        # Type
        film_type = 'dizi' if '/dizi/' in url else 'film'
        
        return {
            'url': url,
            'title': title,
            'year': year,
            'imdb': imdb,
            'image': image,
            'type': film_type,
            'scraped_at': datetime.now().isoformat()
        }
    except:
        return None

def parse_from_link(href, content):
    """Parse film from link and its content"""
    try:
        # Clean content
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text or len(text) < 3:
            return None
        
        # Title is the link text
        title = html.unescape(text).strip()
        
        # Year from URL or text
        year = ''
        year_match = re.search(r'\b(19|20)\d{2}\b', href + ' ' + text)
        if year_match:
            year = year_match.group(0)
        
        # Type
        film_type = 'dizi' if '/dizi/' in href else 'film'
        
        return {
            'url': href,
            'title': title[:100],  # Limit title length
            'year': year,
            'imdb': '0.0',
            'image': '',
            'type': film_type,
            'scraped_at': datetime.now().isoformat()
        }
    except:
        return None

def main():
    print("HDFilmCehennemi Simple Scraper")
    print("=" * 60)
    
    url = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"
    print(f"\nFetching: {url}")
    
    html_content = get_html(url)
    if not html_content:
        print("❌ Failed to fetch page")
        return
    
    print(f"✓ Page fetched ({len(html_content)} characters)")
    
    films = extract_films_directly(html_content)
    
    print(f"\nFound {len(films)} films")
    
    if not films:
        print("\nNo films found. Debugging info:")
        print("1. Check debug_page.html to see the actual HTML")
        print("2. The site might have changed its structure")
        print("3. Try a different approach")
        return
    
    # Remove duplicates
    unique_films = []
    seen = set()
    for film in films:
        if film['url'] not in seen:
            seen.add(film['url'])
            unique_films.append(film)
    
    print(f"Unique films: {len(unique_films)}")
    
    # Save results
    result = {
        'metadata': {
            'scraped_at': datetime.now().isoformat(),
            'url': url,
            'total_films': len(unique_films)
        },
        'films': unique_films
    }
    
    with open('films.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved to films.json")
    
    # Display results
    print("\n" + "=" * 60)
    print("FILMS FOUND")
    print("=" * 60)
    
    for i, film in enumerate(unique_films[:20], 1):
        title = film['title'][:50] + "..." if len(film['title']) > 50 else film['title']
        year = f"({film['year']})" if film['year'] else ""
        imdb = f"IMDB: {film['imdb']}" if film['imdb'] != '0.0' else ""
        print(f"{i:2}. {title:53} {year:8} {imdb}")
    
    if len(unique_films) > 20:
        print(f"... and {len(unique_films) - 20} more")

if __name__ == '__main__':
    main()
