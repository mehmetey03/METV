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
    
    # Alternative: Look for article containers which might be more reliable
    article_pattern = r'<article[^>]*>.*?</article>'
    articles = re.findall(article_pattern, html_content, re.DOTALL)
    
    print(f"  Found {len(articles)} article blocks")
    
    for article in articles:
        film = parse_article_block(article, source_url)
        if film:
            films.append(film)
    
    # Fallback to old pattern if no articles found
    if not films:
        print("  No articles found, trying data-token pattern...")
        film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
        film_blocks = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"  Found {len(film_blocks)} film blocks with data-token")
        
        for block in film_blocks:
            film = parse_film_block(block, source_url)
            if film:
                films.append(film)
    
    return films

def parse_article_block(article, source_url):
    """Parse an article block - more reliable method"""
    try:
        # URL
        url_match = re.search(r'href="([^"]*)"', article)
        if not url_match:
            return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # Title from h2 or h3
        title = ''
        title_match = re.search(r'<h[23][^>]*>\s*<a[^>]*>(.*?)</a>\s*</h[23]>', article, re.DOTALL)
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            title = html.unescape(title)
        
        # Alternative: title from alt attribute of image
        if not title:
            img_match = re.search(r'<img[^>]*alt="([^"]*)"[^>]*>', article)
            if img_match:
                title = html.unescape(img_match.group(1)).strip()
        
        if not title:
            return None
        
        # Clean title
        title = re.sub(r'\s*(?:izle|türkçe|dublaj|altyazı|yabancı|dizi|film|hd)\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^\s*[♪♫★☆♥♦♣♠■□▪▫●○◆◇]+\s*', '', title)
        title = title.strip()
        
        # Year - look for 4-digit year
        year = ''
        year_match = re.search(r'<span[^>]*>\s*(\d{4})\s*</span>', article)
        if not year_match:
            year_match = re.search(r'\((\d{4})\)', title)
            if year_match:
                year = year_match.group(1)
                # Remove year from title
                title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
        
        if year_match and not year:
            year = year_match.group(1)
        
        # IMDB
        imdb = '0.0'
        imdb_match = re.search(r'imdb\s*[^>]*>\s*(\d+\.\d+)', article, re.IGNORECASE)
        if not imdb_match:
            imdb_match = re.search(r'(\d+\.\d+)\s*/?\s*10', article)
        
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    imdb = f"{rating:.1f}"
            except:
                pass
        
        # Image
        image = ''
        img_match = re.search(r'<img[^>]*src="([^"]+\.(?:webp|jpg|jpeg|png))"[^>]*>', article)
        if img_match:
            image = img_match.group(1)
            if not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
        # Language
        language = ''
        lang_match = re.search(r'türkçe\s+(?:dublaj|altyazı)', article, re.IGNORECASE)
        if lang_match:
            language = 'Türkçe Dublaj' if 'dublaj' in lang_match.group(0).lower() else 'Türkçe Altyazı'
        
        # Type
        film_type = 'dizi' if '/dizi/' in url or 'dizi' in source_url.lower() else 'film'
        
        # Comments
        comments = '0'
        comment_match = re.search(r'comment.*?(\d+)', article, re.IGNORECASE)
        if comment_match:
            comments = comment_match.group(1)
        
        # Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', article)
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
        print(f"    Error parsing article: {e}")
        return None

def parse_film_block(block, source_url):
    """Parse a film block (fallback method)"""
    try:
        # URL
        url_match = re.search(r'href="([^"]*)"', block)
        if not url_match:
            return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # Title
        title = ''
        title_match = re.search(r'title="([^"]*)"', block)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
        
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
        
        # IMDB
        imdb = '0.0'
        imdb_match = re.search(r'(\d+\.\d+).*?imdb', block, re.IGNORECASE)
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
            if not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
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
            'comments': '0',
            'language': '',
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
            url = f"{category_url}page/{page}/"
        
        print(f"  Page {page}: {url}")
        
        html_content = get_html(url)
        if not html_content:
            print(f"    Failed to fetch page {page}")
            break
        
        films = extract_films(html_content, url)
        
        if not films:
            print(f"    No films found on page {page}")
            # Try one more page before giving up
            if page == 1:
                continue
            else:
                break
        
        all_films.extend(films)
        print(f"    Found {len(films)} films")
        
        # Check if there are more pages (simple check)
        next_page_link = f'page/{page + 1}/'
        if page < max_pages and next_page_link not in html_content and 'class="next' not in html_content:
            print(f"    No more pages found")
            break
        
        # Be polite
        if page < max_pages:
            time.sleep(1.5)
    
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
        print("Trying direct homepage scrape...")
        
        # Try scraping homepage as fallback
        homepage_films = scrape_category(BASE_URL, 'homepage', max_pages=1)
        all_films.extend(homepage_films)
    
    if not all_films:
        print("\n❌ Still no films found!")
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
    
    # Save results
    output_file = 'hdfilms_complete.json'
    try:
        result = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(unique_films),
                'source': 'hdfilmcehennemi.ws',
                'categories': list(CATEGORIES.keys())
            },
            'films': unique_films
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"\n❌ Error saving results: {e}")
    
    # Print summary
    if unique_films:
        print(f"\nSample of scraped films:")
        print("-" * 80)
        for i, film in enumerate(unique_films[:20], 1):
            title = film['title'][:50] + "..." if len(film['title']) > 50 else film['title']
            year = film.get('year', 'N/A')
            imdb = f"⭐{film['imdb']}" if film['imdb'] != '0.0' else ""
            type_icon = "🎬" if film['type'] == 'film' else "📺"
            print(f"{i:2}. {type_icon} {title:55} {year:6} {imdb}")
    
    print(f"\n{'='*70}")
    print("DONE!")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
