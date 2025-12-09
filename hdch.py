#!/usr/bin/env python3
"""
scrape.py - HDFilmCehennemi scraper with Selenium for AJAX pages
"""
import json
import time
import argparse
import logging
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# -----------------------
# CONFIG
# -----------------------
BASE_URL = "https://www.hdfilmcehennemi.ws/"
DEFAULT_OUTFILE = "films.json"
DEFAULT_WORKERS = 4
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("scraper")

# -----------------------
# Selenium Setup
# -----------------------
def create_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={USER_AGENT}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

# -----------------------
# Page Navigation
# -----------------------
def navigate_to_page(driver, page):
    """Navigate to specific page"""
    if page == 1:
        driver.get(BASE_URL)
    else:
        url = f"{BASE_URL}page/{page}/"
        driver.get(url)
    
    # Wait for content to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".posters-4-col, .poster, .poster-title"))
        )
        time.sleep(2)  # Extra wait for AJAX
    except TimeoutException:
        log.warning(f"Timeout waiting for page {page}")
    
    return driver.page_source

# -----------------------
# Extract Films from Page
# -----------------------
def extract_films_from_html(html, page):
    """Extract film data from HTML"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    films = []
    
    # Find all film elements
    film_elements = soup.select('a.poster')
    
    for idx, element in enumerate(film_elements, 1):
        try:
            # URL
            url = element.get('href', '')
            if not url.startswith('http'):
                url = urljoin(BASE_URL, url)
            
            # Title
            title = element.get('title', '')
            if not title:
                title_elem = element.select_one('.poster-title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Token
            token = element.get('data-token', '')
            
            # Image
            img = element.select_one('img.lazyload')
            image = ''
            if img:
                image = img.get('src') or img.get('data-src') or ''
            
            # Year, IMDB, Comments from poster-meta
            year = ''
            imdb = '0.0'
            comments = '0'
            
            meta = element.select_one('.poster-meta')
            if meta:
                # Find year (first 4-digit number)
                import re
                meta_text = meta.get_text()
                year_match = re.search(r'\b(19|20)\d{2}\b', meta_text)
                if year_match:
                    year = year_match.group(0)
                
                # Find IMDB score
                imdb_elem = meta.select_one('.imdb')
                if imdb_elem:
                    imdb_text = imdb_elem.get_text(strip=True)
                    imdb_match = re.search(r'(\d+\.\d+)', imdb_text)
                    if imdb_match:
                        imdb = imdb_match.group(1)
                
                # Find comment count (look for number after svg)
                svg_spans = meta.find_all('span')
                for span in svg_spans:
                    if span.find('svg'):
                        span_text = span.get_text(strip=True)
                        num_match = re.search(r'(\d+)', span_text)
                        if num_match and num_match.group(1) != year:
                            comments = num_match.group(1)
            
            # Type
            film_type = 'dizi' if '/dizi/' in url else 'film'
            
            films.append({
                'page': page,
                'position': idx,
                'url': url,
                'title': title.strip(),
                'token': token,
                'image': image,
                'year': year,
                'imdb': imdb,
                'comments': comments,
                'type': film_type,
                'embed_url': ''
            })
            
        except Exception as e:
            log.error(f"Error extracting film {idx} on page {page}: {e}")
    
    return films

# -----------------------
# Extract Total Pages
# -----------------------
def get_total_pages(driver):
    """Get total number of pages from pagination"""
    try:
        # Try to find pagination element
        pagination = driver.find_element(By.CSS_SELECTOR, '.pagination-container')
        data_pages = pagination.get_attribute('data-pages')
        if data_pages:
            return int(data_pages)
        
        # Alternative: find last page number
        page_buttons = driver.find_elements(By.CSS_SELECTOR, '.page-number')
        if page_buttons:
            return int(page_buttons[-1].text)
        
    except (NoSuchElementException, ValueError):
        pass
    
    # Default fallback
    return 1

# -----------------------
# Extract Embed URLs
# -----------------------
def extract_embed_url(film):
    """Extract embed URL from film detail page"""
    try:
        response = requests.get(
            film['url'],
            headers={'User-Agent': USER_AGENT},
            timeout=10
        )
        
        if response.status_code == 200:
            import re
            # Look for iframe src
            iframe_match = re.search(r'<iframe[^>]*src="([^"]+hdfilmcehennemi[^"]+embed[^"]+)"', response.text)
            if iframe_match:
                return iframe_match.group(1)
            
            # Look for data-player
            player_match = re.search(r'data-player="([^"]+)"', response.text)
            if player_match:
                return player_match.group(1)
    
    except Exception as e:
        log.error(f"Error fetching embed for {film['title']}: {e}")
    
    return ''

# -----------------------
# Main Scraping Function
# -----------------------
def scrape_pages(start_page, end_page, output_file, get_embeds=False, max_workers=4):
    """Main scraping function"""
    log.info(f"Starting scrape from page {start_page} to {end_page}")
    
    all_films = []
    driver = None
    
    try:
        # Setup driver
        driver = create_driver(headless=True)
        
        # Go to first page to get total pages
        log.info("Loading first page...")
        html = navigate_to_page(driver, start_page)
        total_pages = get_total_pages(driver)
        
        log.info(f"Total pages detected: {total_pages}")
        end_page = min(end_page, total_pages)
        
        # Scrape each page
        for page in range(start_page, end_page + 1):
            log.info(f"Scraping page {page}/{end_page}")
            
            if page != start_page:
                html = navigate_to_page(driver, page)
            
            films = extract_films_from_html(html, page)
            all_films.extend(films)
            
            log.info(f"Found {len(films)} films on page {page}")
            
            # Small delay between pages
            if page < end_page:
                time.sleep(2)
        
        # Extract embed URLs if requested
        if get_embeds and all_films:
            log.info(f"Extracting embed URLs for {len(all_films)} films...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_film = {
                    executor.submit(extract_embed_url, film): film 
                    for film in all_films
                }
                
                for future in as_completed(future_to_film):
                    film = future_to_film[future]
                    try:
                        embed_url = future.result(timeout=15)
                        film['embed_url'] = embed_url
                    except Exception as e:
                        log.error(f"Error getting embed for {film['title']}: {e}")
                        film['embed_url'] = ''
        
        # Save results
        result = {
            'metadata': {
                'total_pages_scraped': end_page - start_page + 1,
                'start_page': start_page,
                'end_page': end_page,
                'total_films': len(all_films),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'embeds_included': get_embeds
            },
            'films': all_films
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)
        
        log.info(f"Successfully saved {len(all_films)} films to {output_file}")
        
        # Also create a summary file
        summary = {
            'total_films': len(all_films),
            'by_type': {
                'film': len([f for f in all_films if f['type'] == 'film']),
                'dizi': len([f for f in all_films if f['type'] == 'dizi'])
            },
            'by_year': {},
            'output_file': output_file
        }
        
        # Count by year
        for film in all_films:
            year = film.get('year', 'Unknown')
            summary['by_year'][year] = summary['by_year'].get(year, 0) + 1
        
        summary_file = output_file.replace('.json', '_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        log.info(f"Summary saved to {summary_file}")
        
        return True
        
    except Exception as e:
        log.error(f"Error during scraping: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

# -----------------------
# CLI Interface
# -----------------------
def main():
    parser = argparse.ArgumentParser(description='HDFilmCehennemi Scraper with Selenium')
    parser.add_argument('--start', type=int, default=1, help='Start page (default: 1)')
    parser.add_argument('--end', type=int, default=5, help='End page (default: 5)')
    parser.add_argument('--output', default=DEFAULT_OUTFILE, help='Output JSON file')
    parser.add_argument('--embeds', action='store_true', help='Extract embed URLs')
    parser.add_argument('--workers', type=int, default=DEFAULT_WORKERS, help='Number of workers for embed extraction')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    print(f"""
    HDFilmCehennemi Scraper
    ========================
    Pages: {args.start} to {args.end}
    Output: {args.output}
    Extract embeds: {args.embeds}
    Workers: {args.workers}
    Headless: {args.headless}
    """)
    
    success = scrape_pages(
        start_page=args.start,
        end_page=args.end,
        output_file=args.output,
        get_embeds=args.embeds,
        max_workers=args.workers
    )
    
    if success:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📁 Output saved to: {args.output}")
    else:
        print(f"\n❌ Scraping failed!")
        exit(1)

# -----------------------
# Quick test function
# -----------------------
def test_scrape():
    """Quick test - scrape first 2 pages"""
    print("Testing scraper with first 2 pages...")
    success = scrape_pages(
        start_page=1,
        end_page=2,
        output_file='test_output.json',
        get_embeds=False
    )
    
    if success:
        # Read and display sample
        with open('test_output.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\nTotal films: {len(data['films'])}")
            print("\nSample films:")
            for film in data['films'][:3]:
                print(f"  • {film['title']} ({film['year']}) - {film['type']}")

if __name__ == '__main__':
    # Uncomment for quick test
    # test_scrape()
    
    # Run main CLI
    main()
