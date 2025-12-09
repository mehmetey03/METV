#!/usr/bin/env python3
"""
hdch.py - HDFilmCehennemi scraper using requests only
"""
import requests
import json
import re
import time
from urllib.parse import urljoin, urlparse
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
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def extract_films_from_html(html, page_num):
    """Extract film information from HTML"""
    films = []
    
    # Pattern to find film blocks
    # Looking for anchor tags with poster class
    poster_pattern = r'<a\s+[^>]*class="[^"]*poster[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-token="(\d+)"[^>]*>'
    
    matches = re.finditer(poster_pattern, html, re.IGNORECASE)
    
    for idx, match in enumerate(matches, 1):
        try:
            url = match.group(1)
            title = match.group(2)
            token = match.group(3)
            
            # Decode HTML entities in title
            import html
            title = html.unescape(title)
            
            # Get the full anchor tag block
            anchor_start = match.start()
            anchor_end = html.find('</a>', anchor_start)
            if anchor_end == -1:
                anchor_end = anchor_start + 2000
            
            film_block = html[anchor_start:anchor_end]
            
            # Extract image URL
            image = ''
            img_match = re.search(r'src="([^"]+\.webp)"', film_block)
            if img_match:
                image = img_match.group(1)
            
            # Extract year
            year = ''
            year_match = re.search(r'<span>\s*(\d{4})\s*</span>', film_block)
            if year_match:
                year = year_match.group(1)
            
            # Extract IMDB rating
            imdb = '0.0'
            imdb_match = re.search(r'<span[^>]*class="[^"]*imdb[^"]*"[^>]*>.*?(\d+\.\d+)', film_block, re.DOTALL)
            if imdb_match:
                imdb = imdb_match.group(1)
            
            # Extract comment count
            comments = '0'
            # Look for a number after an SVG icon
            comment_match = re.search(r'<svg[^>]*>.*?</svg>\s*(\d+)', film_block, re.DOTALL)
            if comment_match:
                comments = comment_match.group(1)
            
            # Determine type
            film_type = 'dizi' if '/dizi/' in url else 'film'
            
            films.append({
                'page': page_num,
                'position': idx,
                'url': url if url.startswith('http') else urljoin(BASE_URL, url),
                'title': title,
                'token': token,
                'image': image,
                'year': year,
                'imdb': imdb,
                'comments': comments,
                'type': film_type,
                'embed_url': ''
            })
            
        except Exception as e:
            logger.error(f"Error processing film {idx} on page {page_num}: {e}")
    
    return films

def get_total_pages():
    """Get total number of pages"""
    try:
        html = get_page_html(BASE_URL)
        if html:
            # Look for data-pages attribute
            pages_match = re.search(r'data-pages="(\d+)"', html)
            if pages_match:
                return int(pages_match.group(1))
            
            # Alternative: look for last page number in pagination
            last_page_match = re.search(r'<a[^>]*href="[^"]*page/(\d+)/"[^>]*>Son\s*Sayfa', html, re.IGNORECASE)
            if last_page_match:
                return int(last_page_match.group(1))
    except Exception as e:
        logger.error(f"Error getting total pages: {e}")
    
    return 1124  # Default fallback

def extract_embed_url(film):
    """Extract embed URL from film detail page"""
    try:
        response = session.get(film['url'], timeout=15)
        if response.status_code == 200:
            html = response.text
            
            # Pattern 1: iframe src
            iframe_match = re.search(r'<iframe[^>]*src="([^"]*hdfilmcehennemi[^"]*embed[^"]+)"', html, re.IGNORECASE)
            if iframe_match:
                return iframe_match.group(1)
            
            # Pattern 2: data-player attribute
            player_match = re.search(r'data-player="([^"]+)"', html)
            if player_match:
                return player_match.group(1)
            
            # Pattern 3: rapidrame links
            rapidrame_match = re.search(r'(https?://[^"\']+rapidrame[^"\']+)', html)
            if rapidrame_match:
                return rapidrame_match.group(1)
            
            # Pattern 4: data-embed attribute
            embed_match = re.search(r'data-embed="([^"]+)"', html)
            if embed_match:
                return embed_match.group(1)
    
    except Exception as e:
        logger.error(f"Error extracting embed for {film['title']}: {e}")
    
    return ''

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
        
        # Construct URL
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}page/{page}/"
        
        # Get page HTML
        html = get_page_html(url)
        if not html:
            logger.warning(f"Failed to get page {page}")
            continue
        
        # Extract films
        films = extract_films_from_html(html, page)
        all_films.extend(films)
        
        logger.info(f"Found {len(films)} films on page {page}")
        
        # Delay between pages to be polite
        if page < end_page:
            time.sleep(delay)
    
    logger.info(f"Total films collected: {len(all_films)}")
    
    # Extract embed URLs if requested
    if get_embeds and all_films:
        logger.info(f"Extracting embed URLs for {len(all_films)} films...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_film = {
                executor.submit(extract_embed_url, film): film 
                for film in all_films
            }
            
            for idx, future in enumerate(as_completed(future_to_film), 1):
                film = future_to_film[future]
                try:
                    embed_url = future.result(timeout=20)
                    film['embed_url'] = embed_url
                    
                    if idx % 10 == 0:
                        logger.info(f"Processed {idx}/{len(all_films)} embed URLs")
                        
                except Exception as e:
                    logger.error(f"Error getting embed for {film['title']}: {e}")
                    film['embed_url'] = ''
    
    # Prepare result
    result = {
        'metadata': {
            'total_pages_scraped': end_page - start_page + 1,
            'start_page': start_page,
            'end_page': end_page,
            'total_films': len(all_films),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'embeds_included': get_embeds,
            'base_url': BASE_URL
        },
        'films': all_films
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    # Generate summary
    generate_summary(all_films, output_file)
    
    return True

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
        summary['by_type'][film['type']] = summary['by_type'].get(film['type'], 0) + 1
        
        # Count by year
        year = film.get('year', 'Unknown')
        summary['by_year'][year] = summary['by_year'].get(year, 0) + 1
    
    # Get top 10 by IMDB rating
    films_with_imdb = [f for f in films if f['imdb'] != '0.0']
    films_with_imdb.sort(key=lambda x: float(x['imdb']), reverse=True)
    summary['top_imdb'] = [
        {
            'title': f['title'],
            'imdb': f['imdb'],
            'year': f['year'],
            'type': f['type']
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
    print(f"Films: {summary['by_type']['film']}")
    print(f"Diziler: {summary['by_type']['dizi']}")
    print(f"Years distribution: {len(summary['by_year'])} different years")
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
    parser = argparse.ArgumentParser(description='HDFilmCehennemi Scraper')
    parser.add_argument('--start', type=int, default=1, help='Start page (default: 1)')
    parser.add_argument('--end', type=int, default=5, help='End page (default: 5)')
    parser.add_argument('--output', default='films.json', help='Output JSON file')
    parser.add_argument('--embeds', action='store_true', help='Extract embed URLs')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between page requests in seconds')
    
    args = parser.parse_args()
    
    print(f"""
    HDFilmCehennemi Scraper
    ========================
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
            print("\n❌ Scraping failed!")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)

# -----------------------
# Quick Test
# -----------------------
def quick_test():
    """Quick test function"""
    print("Running quick test (pages 1-2)...")
    
    try:
        # Test first 2 pages
        success = scrape_pages(
            start_page=1,
            end_page=2,
            output_file='test_output.json',
            get_embeds=False,
            max_workers=2,
            delay=0.5
        )
        
        if success:
            # Load and show results
            with open('test_output.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"\nTest successful!")
                print(f"Total films: {len(data['films'])}")
                print("\nSample films:")
                for film in data['films'][:5]:
                    print(f"  • {film['title']} ({film['year']}) - {film['type']}")
        else:
            print("Test failed!")
            
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == '__main__':
    # For quick testing
    # quick_test()
    
    # Run main function
    main()
