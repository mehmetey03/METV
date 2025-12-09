#!/usr/bin/env python3
"""
hdch_final.py - Final HDFilmCehennemi scraper with pagination
"""
import urllib.request
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://www.hdfilmcehennemi.ws/"
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
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None

def extract_films(html_content, source_url):
    """Extract films from HTML"""
    films = []
    
    if not html_content:
        return films
    
    # Look for film blocks with data-token attribute
    film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
    film_blocks = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    print(f"  Found {len(film_blocks)} film blocks")
    
    for block in film_blocks:
        film = parse_film_block(block, source_url)
        if film:
            films.append(film)
    
    return films

def parse_film_block(block, source_url):
    """Parse a film block"""
    try:
        # URL
        url_match = re.search(r'href="([^"]*)"', block)
        if not url_match:
            return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # Title from title attribute
        title = ''
        title_match = re.search(r'title="([^"]*)"', block)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
        
        # Also try to get title from poster-title
        if not title:
            title_match = re.search(r'<strong[^>]*class="[^"]*poster-title[^"]*"[^>]*>(.*?)</strong>', block, re.DOTALL)
            if title_match:
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                title = html.unescape(title)
        
        if not title:
            return None
        
        # Clean title
        title = re.sub(r'\s*(?:izle|türkçe|dublaj|altyazı|yabancı|dizi|film|hd)\s*$', '', title, flags=re.IGNORECASE)
        title = title.strip()
        
        # Year
        year = ''
        year_match = re.search(r'<span>\s*(\d{4})\s*</span>', block)
        if year_match:
            year = year_match.group(1)
        
        # IMDB - try multiple patterns
        imdb = '0.0'
        
        # Pattern 1: Look in imdb class
        imdb_match = re.search(r'<span[^>]*class="[^"]*imdb[^"]*"[^>]*>.*?(\d+\.\d+|\d+)', block, re.DOTALL)
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    imdb = f"{rating:.1f}"
            except:
                pass
        
        # Pattern 2: Look for SVG pattern with rating
        if imdb == '0.0':
            svg_pattern = r'<svg[^>]*><path[^>]*></path></svg>\s*<p>\s*(\d+\.\d+)\s*</p>'
            svg_match = re.search(svg_pattern, block, re.DOTALL)
            if svg_match:
                try:
                    rating = float(svg_match.group(1))
                    if 1.0 <= rating <= 10.0:
                        imdb = f"{rating:.1f}"
                except:
                    pass
        
        # Image
        image = ''
        img_match = re.search(r'src="([^"]+\.(?:webp|jpg|jpeg|png))"', block)
        if img_match:
            image = img_match.group(1)
            if not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
        # Comments
        comments = '0'
        comment_match = re.search(r'<svg[^>]*>.*?</svg>\s*(\d+)', block, re.DOTALL)
        if comment_match:
            comments = comment_match.group(1)
        
        # Language
        language = ''
        lang_match = re.search(r'<span[^>]*class="[^"]*poster-lang[^"]*"[^>]*>.*?<span>\s*(.*?)\s*</span>', block, re.DOTALL)
        if lang_match:
            language = html.unescape(lang_match.group(1)).strip()
        
        # Type
        film_type = 'dizi' if '/dizi/' in url else 'film'
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', block)
        if token_match:
            token = token_match.group(1)
        
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
        print(f"    Error parsing block: {e}")
        return None

def scrape_category(category_url, category_name, max_pages=3):
    """Scrape a category with pagination"""
    all_films = []
    
    print(f"\nScraping category: {category_name}")
    print(f"URL: {category_url}")
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = category_url
        else:
            # Try different pagination formats
            url = f"{category_url}page/{page}/"
        
        print(f"  Page {page}: {url}")
        
        html_content = get_html(url)
        if not html_content:
            print(f"    Failed to fetch page {page}")
            break
        
        films = extract_films(html_content, url)
        
        if not films:
            print(f"    No films found on page {page}")
            break
        
        all_films.extend(films)
        print(f"    Found {len(films)} films")
        
        # Check if there are more pages
        if page == 1:
            # Look for pagination links
            if f'page/{page + 1}/' not in html_content:
                print(f"    No more pages found")
                break
        
        # Be polite
        if page < max_pages:
            time.sleep(1)
    
    print(f"  Total from {category_name}: {len(all_films)} films")
    return all_films

def main():
    print("=" * 70)
    print("HDFilmCehennemi Complete Scraper")
    print("=" * 70)
    
    all_films = []
    
    # Scrape each category
    for cat_name, cat_url in CATEGORIES.items():
        category_films = scrape_category(cat_url, cat_name, max_pages=2)
        all_films.extend(category_films)
        
        # Be polite between categories
        time.sleep(2)
    
    if not all_films:
        print("\n❌ No films found at all!")
        return
    
    # Remove duplicates by URL
    unique_films = []
    seen_urls = set()
    
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Total films collected: {len(all_films)}")
    print(f"Unique films: {len(unique_films)}")
    
    # Organize by type
    films_by_type = {'film': [], 'dizi': []}
    for film in unique_films:
        films_by_type[film['type']].append(film)
    
    # Save detailed results
    result = {
        'metadata': {
            'scraped_at': datetime.now().isoformat(),
            'total_films': len(unique_films),
            'films_count': len(films_by_type['film']),
            'diziler_count': len(films_by_type['dizi']),
            'categories_scraped': list(CATEGORIES.keys())
        },
        'films_by_type': films_by_type,
        'all_films': unique_films
    }
    
    output_file = 'hdfilms_complete.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
        return
    
    # Also save a simpler version
    simple_output = []
    for film in unique_films:
        simple_output.append({
            'title': film['title'],
            'year': film['year'],
            'type': film['type'],
            'url': film['url'],
            'imdb': film['imdb']
        })
    
    with open('films_simple.json', 'w', encoding='utf-8') as f:
        json.dump(simple_output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Simple results saved to: films_simple.json")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    print(f"Total unique films: {len(unique_films)}")
    print(f"Films: {len(films_by_type['film'])}")
    print(f"Diziler: {len(films_by_type['dizi'])}")
    
    # Years distribution
    years = {}
    for film in unique_films:
        year = film.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\nYears distribution:")
        sorted_years = sorted([(y, c) for y, c in years.items() if y != '' and y != 'Unknown'], 
                            key=lambda x: x[1], reverse=True)
        for year, count in sorted_years[:10]:
            print(f"  {year}: {count} films")
    
    # Films with IMDB ratings
    films_with_imdb = [f for f in unique_films if f.get('imdb', '0.0') not in ['0.0', '0', '']]
    print(f"\nFilms with IMDB ratings: {len(films_with_imdb)}")
    
    if films_with_imdb:
        films_with_imdb.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
        print("\nTop films by IMDB:")
        for idx, film in enumerate(films_with_imdb[:10], 1):
            print(f"{idx:2}. {film['title'][:40]:40} ({film.get('year', 'N/A'):4}) - {film['imdb']}")
    
    # Show sample
    print(f"\nSample films (first 15):")
    print("-" * 80)
    for i, film in enumerate(unique_films[:15], 1):
        title = film['title'][:45] + "..." if len(film['title']) > 45 else film['title']
        year = film.get('year', 'N/A')
        imdb = f"IMDB: {film['imdb']}" if film['imdb'] != '0.0' else ""
        type_icon = "🎬" if film['type'] == 'film' else "📺"
        print(f"{i:2}. {type_icon} {title:48} {year:6} {imdb}")
    
    print(f"\n{'='*70}")
    print("DONE! Check the JSON files for complete results.")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
