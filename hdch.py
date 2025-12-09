#!/usr/bin/env python3
"""
hdch.py - HDFilmCehennemi scraper using requests only (Updated Version)
"""
import requests
import json
import re
import time
from urllib.parse import urljoin, urlparse, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import logging

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
    'Referer': 'https://www.hdfilmcehennemi.ws/',
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
        if 'text/html' not in response.headers.get('content-type', ''):
            logger.warning(f"Non-HTML response from {url}")
            return None
            
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Page not found: {url}")
        else:
            logger.error(f"HTTP error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def extract_films_from_html(html, page_num):
    """Extract film information from HTML"""
    films = []
    
    if not html:
        return films
    
    # Try different patterns for finding film blocks
    patterns = [
        # Pattern 1: Look for article containers with movie data
        r'<article[^>]*class="[^"]*post-[^"]*"[^>]*>(.*?)</article>',
        # Pattern 2: Look for div containers with movie data
        r'<div[^>]*class="[^"]*movie-poster[^"]*"[^>]*>(.*?)</div>',
        # Pattern 3: Look for film items
        r'<div[^>]*class="[^"]*film-item[^"]*"[^>]*>(.*?)</div>',
    ]
    
    all_film_blocks = []
    
    for pattern in patterns:
        blocks = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        if blocks:
            logger.debug(f"Found {len(blocks)} blocks with pattern")
            all_film_blocks.extend(blocks)
            break
    
    # If no blocks found with specific patterns, try to find anchor tags with movie data
    if not all_film_blocks:
        # Look for any anchor tag that might contain movie info
        anchor_pattern = r'<a\s+[^>]*href="([^"]*/(?:film|dizi)/[^"]*)"[^>]*>(.*?)</a>'
        anchors = re.findall(anchor_pattern, html, re.DOTALL | re.IGNORECASE)
        for href, content in anchors:
            if 'poster' in content.lower() or 'movie' in content.lower():
                all_film_blocks.append(f'<a href="{href}">{content}</a>')
    
    logger.info(f"Found {len(all_film_blocks)} potential film blocks on page {page_num}")
    
    for idx, block in enumerate(all_film_blocks[:50], 1):  # Limit to 50 to avoid noise
        try:
            # Extract URL
            url_match = re.search(r'href="([^"]*/(?:film|dizi)/[^"]*)"', block, re.IGNORECASE)
            if not url_match:
                continue
                
            url = url_match.group(1)
            if not url.startswith('http'):
                url = urljoin(BASE_URL, url)
            
            # Extract title
            title = ''
            title_match = re.search(r'title="([^"]*)"', block, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
            else:
                # Try to find title in alt text of image
                alt_match = re.search(r'alt="([^"]*)"', block, re.IGNORECASE)
                if alt_match:
                    title = alt_match.group(1)
                else:
                    # Try to find in h2/h3 tags
                    h_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', block, re.DOTALL | re.IGNORECASE)
                    if h_match:
                        title = re.sub(r'<[^>]+>', '', h_match.group(1)).strip()
            
            if not title:
                continue
            
            # Decode HTML entities in title
            import html
            title = html.unescape(title.strip())
            
            # Extract image
            image = ''
            img_match = re.search(r'src="([^"]+\.(?:jpg|jpeg|png|webp))"', block, re.IGNORECASE)
            if img_match:
                image = img_match.group(1)
            
            # Extract year
            year = ''
            year_match = re.search(r'<span[^>]*>\s*(\d{4})\s*</span>', block)
            if not year_match:
                year_match = re.search(r'(\b\d{4}\b)', block)
            if year_match:
                year = year_match.group(1)
            
            # Extract IMDB rating
            imdb = '0.0'
            imdb_match = re.search(r'imdb.*?(\d+\.\d+)', block, re.IGNORECASE)
            if imdb_match:
                imdb = imdb_match.group(1)
            
            # Determine type
            film_type = 'dizi' if '/dizi/' in url else 'film'
            
            # Extract token if available
            token = ''
            token_match = re.search(r'data-token="(\d+)"', block)
            if token_match:
                token = token_match.group(1)
            
            films.append({
                'page': page_num,
                'position': idx,
                'url': url,
                'title': title,
                'token': token,
                'image': image,
                'year': year,
                'imdb': imdb,
                'type': film_type,
                'embed_url': ''
            })
            
        except Exception as e:
            logger.debug(f"Error processing block {idx} on page {page_num}: {e}")
            continue
    
    return films

def get_total_pages():
    """Get total number of pages by checking pagination"""
    try:
        html = get_page_html(BASE_URL)
        if not html:
            return 1  # Default if can't fetch
        
        # Try multiple patterns for pagination
        patterns = [
            r'<a[^>]*href="[^"]*page/(\d+)/"[^>]*>\s*Son\s*</a>',
            r'<a[^>]*href="[^"]*page/(\d+)/"[^>]*>\s*Last\s*</a>',
            r'data-pages="(\d+)"',
            r'class="last".*?href="[^"]*page/(\d+)/"',
            r'<span[^>]*>\s*(\d+)\s*</span>\s*</a>\s*</li>\s*</ul>',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            if match:
                pages = int(match.group(1))
                logger.info(f"Found total pages: {pages}")
                return pages
        
        # If no pagination found, check if we have next page links
        if 'page/2/' in html:
            # Try to find the highest page number
            page_numbers = re.findall(r'page/(\d+)/', html)
            if page_numbers:
                return max(map(int, page_numbers))
        
        return 1  # Only one page if no pagination found
        
    except Exception as e:
        logger.error(f"Error getting total pages: {e}")
        return 1

def scrape_pages(start_page, end_page, output_file, get_embeds=False, max_workers=4, delay=1):
    """Main scraping function"""
    logger.info(f"Starting scrape from page {start_page} to {end_page}")
    
    all_films = []
    
    # Get total pages
    total_pages = get_total_pages()
    logger.info(f"Total pages available: {total_pages}")
    
    # Adjust end page if necessary
    end_page = min(end_page, total_pages)
    
    # Scrape each page
    for page in range(start_page, end_page + 1):
        logger.info(f"Scraping page {page}/{end_page}")
        
        # Construct URL (handle pagination)
        if page == 1:
            url = BASE_URL
        else:
            # Try different pagination formats
            pagination_formats = [
                f"{BASE_URL}page/{page}/",
                f"{BASE_URL}sayfa/{page}/",
                f"{BASE_URL}?page={page}",
                f"{BASE_URL}?sayfa={page}",
                f"{BASE_URL}index.php?page={page}",
            ]
            
            url = None
            for format_url in pagination_formats:
                test_html = get_page_html(format_url)
                if test_html and len(test_html) > 1000:  # Valid HTML
                    url = format_url
                    logger.debug(f"Using pagination format: {format_url}")
                    break
            
            if not url:
                url = pagination_formats[0]  # Default to first format
        
        # Get page HTML
        html = get_page_html(url)
        if not html:
            logger.warning(f"Failed to get page {page}")
            
            # Try alternative URL
            if page != 1:
                alt_url = f"{BASE_URL}?s=&paged={page}"
                logger.info(f"Trying alternative URL: {alt_url}")
                html = get_page_html(alt_url)
                
            if not html:
                logger.warning(f"Completely failed to get page {page}")
                continue
        
        # Extract films
        films = extract_films_from_html(html, page)
        all_films.extend(films)
        
        logger.info(f"Found {len(films)} films on page {page}")
        
        # Delay between pages to be polite
        if page < end_page:
            time.sleep(delay)
    
    logger.info(f"Total films collected: {len(all_films)}")
    
    # Remove duplicates by URL
    unique_films = []
    seen_urls = set()
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    logger.info(f"Unique films after deduplication: {len(unique_films)}")
    
    # Save results even if no films found
    result = {
        'metadata': {
            'total_pages_scraped': end_page - start_page + 1,
            'start_page': start_page,
            'end_page': end_page,
            'total_films': len(unique_films),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'embeds_included': get_embeds,
            'base_url': BASE_URL
        },
        'films': unique_films
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
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
    films_with_imdb = [f for f in films if f.get('imdb', '0.0') not in ['0.0', '0', '']]
    films_with_imdb.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
    summary['top_imdb'] = [
        {
            'title': f.get('title', 'Unknown'),
            'imdb': f.get('imdb', '0.0'),
            'year': f.get('year', 'Unknown'),
            'type': f.get('type', 'film')
        }
        for f in films_with_imdb[:10]
    ]
    
    # Save summary
    summary_file = output_file.replace('.json', '_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Summary saved to {summary_file}")
    
    # Print summary to console
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    print(f"Total films: {summary['total_films']}")
    print(f"Films: {summary['by_type'].get('film', 0)}")
    print(f"Diziler: {summary['by_type'].get('dizi', 0)}")
    print(f"Years distribution: {len(summary['by_year'])} different years")
    
    if summary['by_year']:
        print("\nTop 5 years:")
        sorted_years = sorted(summary['by_year'].items(), key=lambda x: x[1], reverse=True)
        for year, count in sorted_years[:5]:
            print(f"  {year}: {count} films")
    
    if summary['top_imdb']:
        print("\nTop 5 by IMDB rating:")
        for idx, film in enumerate(summary['top_imdb'][:5], 1):
            print(f"  {idx}. {film['title']} ({film['year']}) - {film['imdb']}")

# -----------------------
# Main Function
# -----------------------
def main():
    parser = argparse.ArgumentParser(description='HDFilmCehennemi Scraper (Updated)')
    parser.add_argument('--start', type=int, default=1, help='Start page (default: 1)')
    parser.add_argument('--end', type=int, default=5, help='End page (default: 5)')
    parser.add_argument('--output', default='films.json', help='Output JSON file')
    parser.add_argument('--embeds', action='store_true', help='Extract embed URLs')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between page requests in seconds')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    print(f"""
    HDFilmCehennemi Scraper (Updated)
    ==================================
    Pages: {args.start} to {args.end}
    Output: {args.output}
    Extract embeds: {args.embeds}
    Workers: {args.workers}
    Delay: {args.delay}s
    """)
    
    try:
        success = scrape_pages(
            start_page=args.start,
            end_page=args.end,
            output_file=args.output,
            get_embeds=args.embeds,
            max_workers=args.workers,
            delay=args.delay
        )
        
        if success:
            print(f"\n✅ Successfully scraped pages {args.start}-{args.end}")
            print(f"📁 Output saved to: {args.output}")
        else:
            print(f"\n⚠️  No films found. Check website structure or try different pages.")
            print(f"📁 Output saved to: {args.output}")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

# -----------------------
# Quick Test
# -----------------------
def quick_test():
    """Quick test function"""
    print("Running quick test (page 1 only)...")
    
    try:
        # Test only page 1
        success = scrape_pages(
            start_page=1,
            end_page=1,
            output_file='test_output.json',
            get_embeds=False,
            max_workers=1,
            delay=0.5
        )
        
        if success:
            # Load and show results
            with open('test_output.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"\nTest successful!")
                print(f"Total films: {len(data['films'])}")
                if data['films']:
                    print("\nSample films:")
                    for film in data['films'][:3]:
                        print(f"  • {film.get('title', 'Unknown')} ({film.get('year', 'N/A')}) - {film.get('type', 'N/A')}")
                else:
                    print("No films found. The website structure may have changed.")
        else:
            print("Test failed - no films found!")
            
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Uncomment for quick testing
    # quick_test()
    
    # Run main function
    main()
