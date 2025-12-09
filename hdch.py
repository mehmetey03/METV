#!/usr/bin/env python3
"""
hdch_final.py - Final HDFilmCehennemi scraper with multiple strategies
"""
import requests
import json
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
import argparse
import logging
import sys
from bs4 import BeautifulSoup

# -----------------------
# CONFIG
# -----------------------
BASE_URL = "https://www.hdfilmcehennemi.ws/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': BASE_URL,
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

def get_page_html(url, retries=2):
    """Get HTML content of a page with retries"""
    for attempt in range(retries + 1):
        try:
            logger.debug(f"Fetching: {url} (attempt {attempt + 1})")
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if we got a valid HTML response
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                logger.warning(f"Non-HTML response from {url}: {content_type}")
                return None
                
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Page not found: {url}")
                return None
            if attempt < retries:
                logger.warning(f"HTTP error {e.response.status_code} for {url}, retrying...")
                time.sleep(1)
                continue
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            return None
        except Exception as e:
            if attempt < retries:
                logger.warning(f"Error fetching {url}: {e}, retrying...")
                time.sleep(1)
                continue
            logger.error(f"Error fetching {url}: {e}")
            return None
    return None

def extract_films_from_soup(soup, page_num):
    """Extract films from BeautifulSoup object"""
    films = []
    
    # Strategy 1: Look for links to film/dizi pages
    film_links = soup.find_all('a', href=re.compile(r'.*/(film|dizi)/.*'))
    
    seen_urls = set()
    for link in film_links:
        try:
            url = link.get('href', '')
            if not url or url in seen_urls:
                continue
                
            if not url.startswith('http'):
                url = urljoin(BASE_URL, url)
            
            seen_urls.add(url)
            
            # Get title from link or nearby elements
            title = link.get_text(strip=True)
            
            # If title is too short, look for title in parent elements
            if len(title) < 3:
                # Check parent h2/h3
                parent = link.find_parent(['h2', 'h3', 'h4'])
                if parent:
                    title = parent.get_text(strip=True)
                else:
                    # Check sibling div with class containing title
                    sibling = link.find_previous_sibling(class_=re.compile('title', re.I))
                    if sibling:
                        title = sibling.get_text(strip=True)
            
            # Clean title
            title = re.sub(r'\s+', ' ', title).strip()
            title = re.sub(r'\s*[–\-]\s*Türkçe Dublaj\s*$', '', title, flags=re.I)
            title = re.sub(r'\s*[–\-]\s*Türkçe Altyazı\s*$', '', title, flags=re.I)
            title = re.sub(r'\s*izle\s*$', '', title, flags=re.I)
            
            if not title or len(title) < 2:
                continue
            
            # Find image
            image = ''
            
            # Look for image in the link or nearby
            img = link.find('img')
            if img:
                image = img.get('src', '') or img.get('data-src', '')
            
            # If no image found, look in parent container
            if not image:
                container = link.find_parent(['article', 'div', 'li'])
                if container:
                    container_img = container.find('img')
                    if container_img:
                        image = container_img.get('src', '') or container_img.get('data-src', '')
            
            # Determine type
            film_type = 'dizi' if '/dizi/' in url else 'film'
            
            # Extract year from URL or title
            year = ''
            year_match = re.search(r'(\b(19|20)\d{2}\b)', url + ' ' + title)
            if year_match:
                year = year_match.group(1)
            
            # Get more details by visiting the film page
            film_details = get_film_details(url)
            
            films.append({
                'page': page_num,
                'url': url,
                'title': title,
                'image': image,
                'year': year,
                'imdb': film_details.get('imdb', '0.0'),
                'description': film_details.get('description', ''),
                'genres': film_details.get('genres', []),
                'duration': film_details.get('duration', ''),
                'type': film_type,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        except Exception as e:
            logger.debug(f"Error processing link: {e}")
            continue
    
    return films

def get_film_details(url):
    """Get detailed information from individual film page"""
    details = {
        'imdb': '0.0',
        'description': '',
        'genres': [],
        'duration': ''
    }
    
    try:
        html = get_page_html(url)
        if not html:
            return details
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to find IMDB rating
        imdb_patterns = [
            r'IMDB[:\s]*([\d\.]+)/10',
            r'IMDB[:\s]*([\d\.]+)',
            r'imdb[:\s]*([\d\.]+)',
        ]
        
        page_text = soup.get_text()
        for pattern in imdb_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                try:
                    imdb_val = float(match.group(1))
                    if 1.0 <= imdb_val <= 10.0:  # Valid IMDB range
                        details['imdb'] = f"{imdb_val:.1f}"
                        break
                except:
                    pass
        
        # Try to find description
        desc_selectors = [
            '.entry-content',
            '.description',
            '.synopsis',
            'article p',
            '.content p',
            'meta[property="og:description"]',
            'meta[name="description"]',
        ]
        
        for selector in desc_selectors:
            if selector.startswith('meta'):
                meta = soup.find('meta', {'property': selector.split('[')[1].split(']')[0].split('=')[1].strip('"')})
                if meta and meta.get('content'):
                    details['description'] = meta.get('content', '')[:500]
                    break
            else:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if len(text) > 50:  # Reasonable length for description
                        details['description'] = text[:500]
                        break
        
        # Try to find genres
        genre_selectors = [
            '.genre',
            '.categories',
            '.tags',
            'a[href*="kategori"]',
            'a[href*="genre"]',
        ]
        
        for selector in genre_selectors:
            elements = soup.select(selector)
            for elem in elements:
                genre = elem.get_text(strip=True)
                if genre and len(genre) > 2 and genre.lower() not in ['film', 'dizi', 'izle']:
                    if genre not in details['genres']:
                        details['genres'].append(genre)
        
        # Try to find duration
        duration_patterns = [
            r'(\d+)\s*dk\b',
            r'(\d+)\s*min\b',
            r'Süre[:\s]*(\d+)\s*',
            r'Duration[:\s]*(\d+)\s*',
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                details['duration'] = f"{match.group(1)} dk"
                break
        
    except Exception as e:
        logger.debug(f"Error getting details from {url}: {e}")
    
    return details

def get_films_from_homepage():
    """Get films from homepage"""
    print("\n" + "="*60)
    print("SCRAPING HOMEPAGE")
    print("="*60)
    
    films = []
    
    html = get_page_html(BASE_URL)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        films = extract_films_from_soup(soup, 1)
        print(f"Found {len(films)} films on homepage")
    
    return films

def get_films_from_sitemap():
    """Try to find films from sitemap"""
    print("\n" + "="*60)
    print("CHECKING SITEMAP")
    print("="*60)
    
    films = []
    
    # Common sitemap locations
    sitemap_urls = [
        f"{BASE_URL}sitemap.xml",
        f"{BASE_URL}sitemap_index.xml",
        f"{BASE_URL}wp-sitemap.xml",
        f"{BASE_URL}sitemap-1.xml",
    ]
    
    for sitemap_url in sitemap_urls:
        print(f"Checking sitemap: {sitemap_url}")
        html = get_page_html(sitemap_url)
        if html:
            # Check if it's an XML sitemap
            if '<?xml' in html and 'sitemap' in html.lower():
                print(f"Found XML sitemap at {sitemap_url}")
                
                # Extract URLs from sitemap
                urls = re.findall(r'<loc[^>]*>([^<]+)</loc>', html)
                film_urls = [url for url in urls if '/film/' in url or '/dizi/' in url]
                
                print(f"Found {len(film_urls)} film/dizi URLs in sitemap")
                
                # Sample some URLs to get details
                for url in film_urls[:10]:  # Limit to 10 to avoid too many requests
                    try:
                        # Get basic info from URL
                        film_type = 'dizi' if '/dizi/' in url else 'film'
                        
                        # Extract title from URL
                        title = url.split('/')[-2].replace('-', ' ').title()
                        title = re.sub(r'\s*Izle\s*$', '', title, flags=re.I)
                        
                        # Get year from URL
                        year = ''
                        year_match = re.search(r'(\b(19|20)\d{2}\b)', url)
                        if year_match:
                            year = year_match.group(1)
                        
                        films.append({
                            'page': 0,
                            'url': url,
                            'title': title,
                            'image': '',
                            'year': year,
                            'imdb': '0.0',
                            'description': '',
                            'genres': [],
                            'duration': '',
                            'type': film_type,
                            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'sitemap'
                        })
                    except Exception as e:
                        print(f"Error processing URL {url}: {e}")
                
                break
            else:
                print("Not a valid XML sitemap")
        else:
            print("No sitemap found")
    
    return films

def get_films_from_search():
    """Try to find films using search functionality"""
    print("\n" + "="*60)
    print("TRYING SEARCH FUNCTIONALITY")
    print("="*60)
    
    films = []
    
    # Common search patterns
    search_terms = ['film', 'dizi', 'movie', 'series']
    
    for term in search_terms:
        print(f"Searching for: {term}")
        
        # Try different search URL patterns
        search_urls = [
            f"{BASE_URL}?s={term}",
            f"{BASE_URL}search/{term}/",
            f"{BASE_URL}ara?q={term}",
        ]
        
        for search_url in search_urls:
            html = get_page_html(search_url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                search_films = extract_films_from_soup(soup, 0)
                
                if search_films:
                    print(f"Found {len(search_films)} films searching for '{term}'")
                    films.extend(search_films)
                    break
        
        time.sleep(1)  # Be polite
    
    return films

def save_results(films, output_file):
    """Save results to JSON file"""
    if not films:
        print("\n⚠️  No films found to save")
        return False
    
    # Remove duplicates
    unique_films = []
    seen_urls = set()
    
    for film in films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\nTotal unique films: {len(unique_films)}")
    
    # Organize by type
    films_by_type = {
        'film': [],
        'dizi': []
    }
    
    for film in unique_films:
        films_by_type[film['type']].append(film)
    
    result = {
        'metadata': {
            'total_films': len(unique_films),
            'films_count': len(films_by_type['film']),
            'diziler_count': len(films_by_type['dizi']),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': BASE_URL,
            'scraping_methods': ['homepage', 'sitemap', 'search']
        },
        'films_by_type': films_by_type,
        'all_films': unique_films
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to: {output_file}")
    
    # Print summary
    print_summary(unique_films)
    
    return True

def print_summary(films):
    """Print summary of scraped films"""
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    
    films_count = len([f for f in films if f['type'] == 'film'])
    diziler_count = len([f for f in films if f['type'] == 'dizi'])
    
    print(f"Total: {len(films)}")
    print(f"Films: {films_count}")
    print(f"Diziler: {diziler_count}")
    
    # Years
    years = {}
    for film in films:
        year = film.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\nYears distribution ({len(years)} different years):")
        sorted_years = sorted([(y, c) for y, c in years.items() if y != '' and y != 'Unknown'], 
                            key=lambda x: x[1], reverse=True)
        for year, count in sorted_years[:10]:
            print(f"  {year}: {count}")
    
    # Top films by IMDB
    films_with_imdb = [f for f in films if f.get('imdb', '0.0') != '0.0']
    if films_with_imdb:
        films_with_imdb.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
        print(f"\nTop films by IMDB rating:")
        for idx, film in enumerate(films_with_imdb[:5], 1):
            print(f"  {idx}. {film['title']} ({film.get('year', 'N/A')}) - IMDB: {film['imdb']}")
    
    # Sample films
    print(f"\nSample films:")
    for idx, film in enumerate(films[:5], 1):
        print(f"  {idx}. {film['title']} ({film.get('year', 'N/A')}) - {film['type']}")

def main():
    parser = argparse.ArgumentParser(description='HDFilmCehennemi Scraper - Final Version')
    parser.add_argument('--output', default='hdfilmcehennemi_films.json', help='Output JSON file')
    parser.add_argument('--simple', action='store_true', help='Simple mode (homepage only)')
    parser.add_argument('--full', action='store_true', help='Full mode (all methods)')
    
    args = parser.parse_args()
    
    print(f"""
    HDFilmCehennemi Scraper
    ========================
    Output: {args.output}
    Mode: {'full' if args.full else 'simple' if args.simple else 'standard'}
    """)
    
    try:
        all_films = []
        
        # Always check homepage
        print("\n" + "="*60)
        print("STARTING SCRAPING PROCESS")
        print("="*60)
        
        homepage_films = get_films_from_homepage()
        all_films.extend(homepage_films)
        
        if args.full or (not args.simple and len(homepage_films) < 10):
            # Try additional methods
            sitemap_films = get_films_from_sitemap()
            all_films.extend(sitemap_films)
            
            search_films = get_films_from_search()
            all_films.extend(search_films)
        
        # Save results
        success = save_results(all_films, args.output)
        
        if success:
            print("\n" + "="*60)
            print("SCRAPING COMPLETED SUCCESSFULLY!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("NO FILMS FOUND - SITE MAY HAVE CHANGED")
            print("="*60)
            print("\nPossible reasons:")
            print("1. Website structure has changed")
            print("2. Content is loaded with JavaScript")
            print("3. Site is blocking scrapers")
            print("4. Only limited content is publicly accessible")
            print("\nTry visiting the site manually to check available content.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
