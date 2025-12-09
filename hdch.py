#!/usr/bin/env python3
"""
hdch_fixed.py - Fixed HDFilmCehennemi scraper
"""
import requests
import json
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# -----------------------
# Helper Functions
# -----------------------
def get_page_html(url):
    """Get HTML content of a page"""
    try:
        logger.debug(f"Fetching: {url}")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Check if we got a valid HTML response
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            logger.warning(f"Non-HTML response from {url}: {content_type}")
            return None
            
        return response.text
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def inspect_page_structure():
    """Inspect the website structure to understand how it works"""
    print("\n" + "="*60)
    print("INSPECTING WEBSITE STRUCTURE")
    print("="*60)
    
    # First, get the homepage
    html = get_page_html(BASE_URL)
    if not html:
        print("❌ Cannot access homepage")
        return
    
    # Parse with BeautifulSoup for easier inspection
    soup = BeautifulSoup(html, 'html.parser')
    
    print(f"\n1. Page Title: {soup.title.string if soup.title else 'No title'}")
    
    # Look for film/series items
    print("\n2. Looking for film/series containers...")
    
    # Check common container classes
    container_classes = [
        'post', 'movie', 'film', 'dizi', 'item', 'card', 
        'content', 'article', 'entry', 'product'
    ]
    
    for cls in container_classes:
        elements = soup.find_all(class_=re.compile(cls, re.I))
        if elements:
            print(f"   Found {len(elements)} elements with class containing '{cls}'")
    
    # Look for pagination
    print("\n3. Checking pagination...")
    pagination = soup.find_all('a', href=True)
    pagination_links = []
    for link in pagination:
        href = link['href']
        if 'page' in href or 'sayfa' in href or 'paged' in href:
            pagination_links.append(href)
    
    if pagination_links:
        print(f"   Found {len(pagination_links)} pagination links")
        unique_links = set(pagination_links[:5])
        for link in unique_links:
            print(f"   - {link}")
    else:
        print("   No pagination links found")
    
    # Look for film links
    print("\n4. Looking for film/dizi links...")
    film_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if ('/film/' in href or '/dizi/' in href) and href.startswith('http'):
            film_links.append((href, link.get_text(strip=True)[:50]))
    
    if film_links:
        print(f"   Found {len(film_links)} film/dizi links")
        for href, text in film_links[:3]:
            print(f"   - {text}... -> {href}")
    else:
        # Try to find links in another way
        all_links = soup.find_all('a', href=True)
        print(f"   Total links on page: {len(all_links)}")
        for link in all_links[:10]:
            href = link['href']
            text = link.get_text(strip=True)[:30]
            print(f"   - {text}... -> {href}")
    
    # Check HTML structure
    print("\n5. HTML Structure Analysis...")
    
    # Find all script tags that might contain data
    scripts = soup.find_all('script')
    data_scripts = []
    for script in scripts:
        if script.string and ('film' in script.string.lower() or 'movie' in script.string.lower()):
            data_scripts.append(script.string[:200])
    
    if data_scripts:
        print(f"   Found {len(data_scripts)} scripts with film data")
        for i, script in enumerate(data_scripts[:2]):
            print(f"   Script {i+1}: {script}...")
    
    print("\n" + "="*60)
    print("END OF INSPECTION")
    print("="*60)
    
    return html

def extract_films_modern(html, page_num):
    """Modern extraction using BeautifulSoup"""
    films = []
    
    if not html:
        return films
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try different selectors based on common WordPress themes
    selectors = [
        'article',  # WordPress articles
        '.post',  # WordPress posts
        '.movie',  # Movie items
        '.film-item',  # Film items
        '.dizi-item',  # Dizi items
        '.content-item',  # Content items
        '.entry',  # Entry items
        'div[class*="movie"]',  # Any div with movie in class
        'div[class*="film"]',  # Any div with film in class
        'div[class*="post-"]',  # WordPress post items
    ]
    
    film_elements = []
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements and len(elements) > 2:  # More than 2 suggests we found the right selector
            logger.debug(f"Found {len(elements)} elements with selector '{selector}'")
            film_elements = elements
            break
    
    # If no specific selector worked, look for any container that might have a film link
    if not film_elements:
        # Look for links to film/dizi pages
        film_links = soup.find_all('a', href=re.compile(r'.*/(film|dizi)/.*'))
        for link in film_links:
            # Get the parent container
            parent = link.find_parent(['article', 'div', 'li'])
            if parent and parent not in film_elements:
                film_elements.append(parent)
    
    logger.info(f"Found {len(film_elements)} potential film containers on page {page_num}")
    
    for idx, element in enumerate(film_elements[:50], 1):  # Limit to avoid noise
        try:
            # Find the link
            link_elem = element.find('a', href=re.compile(r'.*/(film|dizi)/.*'))
            if not link_elem:
                continue
            
            url = link_elem.get('href', '')
            if not url.startswith('http'):
                url = urljoin(BASE_URL, url)
            
            # Extract title
            title = ''
            
            # Try multiple ways to get title
            title_elem = element.find(['h2', 'h3', 'h4', '.title', '.entry-title'])
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if not title:
                # Try alt text of image
                img_elem = element.find('img')
                if img_elem and img_elem.get('alt'):
                    title = img_elem.get('alt', '')
            
            if not title:
                # Use link text
                title = link_elem.get_text(strip=True)
            
            if not title or len(title) < 2:
                continue
            
            # Clean up title
            title = re.sub(r'\s+', ' ', title).strip()
            title = re.sub(r'\s*izle\s*$', '', title, flags=re.I)
            
            # Extract image
            image = ''
            img_elem = element.find('img')
            if img_elem:
                image = img_elem.get('src', '')
                if not image:
                    image = img_elem.get('data-src', '')
            
            # Extract year
            year = ''
            
            # Look for year in various places
            year_pattern = r'\b(19|20)\d{2}\b'
            
            # Check element text
            element_text = element.get_text()
            year_match = re.search(year_pattern, element_text)
            if year_match:
                year = year_match.group(0)
            
            # Extract IMDB rating
            imdb = '0.0'
            
            # Look for IMDB in text
            imdb_patterns = [
                r'imdb[:\s]*([\d\.]+)',
                r'IMDB[:\s]*([\d\.]+)',
                r'([\d\.]+)/10',
            ]
            
            for pattern in imdb_patterns:
                imdb_match = re.search(pattern, element_text, re.I)
                if imdb_match:
                    try:
                        imdb_val = float(imdb_match.group(1))
                        if 0 <= imdb_val <= 10:
                            imdb = f"{imdb_val:.1f}"
                            break
                    except:
                        pass
            
            # Determine type
            film_type = 'dizi' if '/dizi/' in url else 'film'
            
            films.append({
                'page': page_num,
                'position': idx,
                'url': url,
                'title': title,
                'image': image,
                'year': year,
                'imdb': imdb,
                'type': film_type,
                'embed_url': ''
            })
            
        except Exception as e:
            logger.debug(f"Error processing element {idx}: {e}")
            continue
    
    return films

def get_pagination_urls():
    """Get pagination URLs by inspecting the site"""
    html = get_page_html(BASE_URL)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for pagination
    pagination_urls = []
    
    # Check pagination links
    pagination_selectors = [
        '.pagination a',
        '.page-numbers a',
        '.pager a',
        '.nav-links a',
        'a[href*="page"]',
        'a[href*="sayfa"]',
        'a[href*="paged"]',
    ]
    
    for selector in pagination_selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href', '')
            if href and href not in pagination_urls:
                pagination_urls.append(href)
    
    # Also check if there's JavaScript-based pagination
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Look for URLs in JavaScript
            url_matches = re.findall(r'["\'](https?://[^"\']*page[^"\']*)["\']', script.string)
            pagination_urls.extend(url_matches)
    
    return list(set(pagination_urls))  # Remove duplicates

def scrape_with_ajax(start_page, end_page, output_file):
    """Try to scrape using AJAX-like requests if available"""
    films = []
    
    # Some sites use AJAX for pagination with URLs like:
    # /wp-json/... or /ajax/... or ?action=load_more
    
    ajax_patterns = [
        f"{BASE_URL}wp-json/wp/v2/posts?page={{page}}",
        f"{BASE_URL}?action=load_more&page={{page}}",
        f"{BASE_URL}ajax.php?page={{page}}",
        f"{BASE_URL}index.php?page={{page}}",
    ]
    
    for page in range(start_page, end_page + 1):
        logger.info(f"Trying AJAX method for page {page}")
        
        for pattern in ajax_patterns:
            url = pattern.format(page=page)
            html = get_page_html(url)
            
            if html and len(html) > 100:
                logger.info(f"Found working AJAX URL: {url}")
                page_films = extract_films_modern(html, page)
                films.extend(page_films)
                break
        
        time.sleep(1)
    
    return films

def manual_scrape(output_file):
    """Manual scraping approach - try different methods"""
    print("\n" + "="*60)
    print("MANUAL SCRAPING MODE")
    print("="*60)
    
    all_films = []
    
    # Method 1: Direct homepage scrape
    print("\n1. Scraping homepage...")
    html = get_page_html(BASE_URL)
    if html:
        films = extract_films_modern(html, 1)
        all_films.extend(films)
        print(f"   Found {len(films)} films on homepage")
    
    # Method 2: Try category pages
    print("\n2. Trying category pages...")
    categories = [
        'film-izle',
        'dizi-izle',
        'film',
        'dizi',
        'movies',
        'series',
    ]
    
    for category in categories:
        url = f"{BASE_URL}kategori/{category}/"
        html = get_page_html(url)
        if html:
            films = extract_films_modern(html, 2)
            all_films.extend(films)
            print(f"   Found {len(films)} films in category '{category}'")
            time.sleep(1)
    
    # Method 3: Try AJAX if available
    print("\n3. Trying AJAX endpoints...")
    ajax_films = scrape_with_ajax(1, 3, output_file)
    all_films.extend(ajax_films)
    print(f"   Found {len(ajax_films)} films via AJAX")
    
    # Remove duplicates
    unique_films = []
    seen_urls = set()
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\nTotal unique films found: {len(unique_films)}")
    
    # Save results
    result = {
        'metadata': {
            'scrape_method': 'manual',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_films': len(unique_films),
            'base_url': BASE_URL
        },
        'films': unique_films
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Generate summary
    generate_summary(unique_films, output_file)
    
    return len(unique_films) > 0

def generate_summary(films, output_file):
    """Generate summary statistics"""
    summary = {
        'total_films': len(films),
        'by_type': {
            'film': 0,
            'dizi': 0
        },
        'by_year': {},
        'top_imdb': []
    }
    
    for film in films:
        # Count by type
        film_type = film.get('type', 'film')
        summary['by_type'][film_type] = summary['by_type'].get(film_type, 0) + 1
        
        # Count by year
        year = film.get('year', 'Unknown')
        summary['by_year'][year] = summary['by_year'].get(year, 0) + 1
    
    # Get top 10 by IMDB rating
    films_with_imdb = []
    for f in films:
        imdb = f.get('imdb', '0.0')
        if imdb and imdb != '0.0':
            try:
                if 0 <= float(imdb) <= 10:
                    films_with_imdb.append(f)
            except:
                pass
    
    films_with_imdb.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
    summary['top_imdb'] = [
        {
            'title': f.get('title', 'Unknown'),
            'imdb': f.get('imdb', '0.0'),
            'year': f.get('year', 'Unknown'),
            'type': f.get('type', 'film'),
            'url': f.get('url', '')
        }
        for f in films_with_imdb[:10]
    ]
    
    # Save summary
    summary_file = output_file.replace('.json', '_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    print(f"Total films: {summary['total_films']}")
    print(f"Films: {summary['by_type'].get('film', 0)}")
    print(f"Diziler: {summary['by_type'].get('dizi', 0)}")
    
    if summary['by_year']:
        print(f"\nYears distribution: {len(summary['by_year'])} different years")
        sorted_years = sorted([(y, c) for y, c in summary['by_year'].items() if y != 'Unknown'], 
                            key=lambda x: x[1], reverse=True)
        if sorted_years:
            print("\nTop years:")
            for year, count in sorted_years[:5]:
                print(f"  {year}: {count} films")
    
    if summary['top_imdb']:
        print("\nTop by IMDB rating:")
        for idx, film in enumerate(summary['top_imdb'][:5], 1):
            print(f"  {idx}. {film['title']} ({film['year']}) - {film['imdb']}")

def test_single_page():
    """Test scraping a single film page to understand structure"""
    test_urls = [
        "https://www.hdfilmcehennemi.ws/film/joker-folie-a-deux-izle-6/",
        "https://www.hdfilmcehennemi.ws/dizi/stranger-things-izle-4/",
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        html = get_page_html(url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Get title
            title = soup.title.string if soup.title else 'No title'
            print(f"Title: {title}")
            
            # Look for movie info
            info_selectors = ['.movie-info', '.film-info', '.entry-content', 'article']
            for selector in info_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"\nFound {len(elements)} elements with selector '{selector}'")
                    for elem in elements[:1]:
                        text = elem.get_text()[:300]
                        print(f"Text preview: {text}...")
                        break
            
            # Look for meta tags
            print("\nMeta tags:")
            for meta in soup.find_all('meta'):
                if meta.get('property') in ['og:title', 'og:description', 'og:image']:
                    print(f"  {meta.get('property')}: {meta.get('content', '')[:100]}")

# -----------------------
# Main Function
# -----------------------
def main():
    parser = argparse.ArgumentParser(description='HDFilmCehennemi Scraper (Fixed)')
    parser.add_argument('--mode', choices=['inspect', 'scrape', 'test', 'manual'], 
                       default='scrape', help='Operation mode')
    parser.add_argument('--output', default='films.json', help='Output JSON file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    print(f"""
    HDFilmCehennemi Scraper (Fixed Version)
    ========================================
    Mode: {args.mode}
    Output: {args.output}
    """)
    
    try:
        if args.mode == 'inspect':
            inspect_page_structure()
            
        elif args.mode == 'test':
            test_single_page()
            
        elif args.mode == 'manual':
            success = manual_scrape(args.output)
            if success:
                print(f"\n✅ Manual scraping completed")
                print(f"📁 Output saved to: {args.output}")
            else:
                print(f"\n⚠️  No films found")
                
        elif args.mode == 'scrape':
            # Try to scrape first 2 pages
            print("Attempting to scrape pages 1-2...")
            
            all_films = []
            for page in [1, 2]:
                if page == 1:
                    url = BASE_URL
                else:
                    # Try to find correct pagination
                    url = f"{BASE_URL}?page={page}"
                
                html = get_page_html(url)
                if html:
                    films = extract_films_modern(html, page)
                    all_films.extend(films)
                    print(f"Page {page}: Found {len(films)} films")
                time.sleep(1)
            
            if all_films:
                # Remove duplicates
                unique_films = []
                seen_urls = set()
                for film in all_films:
                    if film['url'] not in seen_urls:
                        seen_urls.add(film['url'])
                        unique_films.append(film)
                
                # Save results
                result = {
                    'metadata': {
                        'pages_scraped': [1, 2],
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'total_films': len(unique_films),
                        'base_url': BASE_URL
                    },
                    'films': unique_films
                }
                
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                generate_summary(unique_films, args.output)
                
                print(f"\n✅ Successfully scraped {len(unique_films)} films")
                print(f"📁 Output saved to: {args.output}")
            else:
                print("\n⚠️  No films found. Try --mode=manual or --mode=inspect")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
