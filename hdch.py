import urllib.request
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

# ==========================================================
# ONLY CHANGE THIS VARIABLE WHEN THE DOMAIN CHANGES
# ==========================================================
BASE_DOMAIN = "https://www.hdfilmcehennemi.nl" 
# ==========================================================

EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url, headers=None):
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': BASE_DOMAIN + "/",
    }
    if headers:
        default_headers.update(headers)
    try:
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception:
        return None

def extract_films_from_html(html_content, source_url):
    films = []
    if not html_content:
        return films
    
    film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
    film_matches = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    for match in film_matches:
        film = parse_film_poster(match, source_url)
        if film:
            films.append(film)
    return films

def parse_film_poster(poster_html, source_url):
    try:
        url_match = re.search(r'href="([^"]+)"', poster_html)
        if not url_match: return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_DOMAIN, url)
        
        title = ''
        title_match = re.search(r'title="([^"]+)"', poster_html)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
        
        if not title: return None
        title = clean_title(title)
        
        # ... (Rest of your parsing logic for year, imdb, etc. remains the same)
        
        return {
            'url': url,
            'title': title,
            'type': 'dizi' if '/dizi/' in url else 'film',
            'source': source_url,
            'scraped_at': datetime.now().isoformat()
        }
    except:
        return None

def scrape_discovery_pages():
    all_films = []
    
    # We use f-strings to inject the BASE_DOMAIN dynamically
    list_paths = [        
        "//",
        "//category/film-izle-2/",
        "//category/nette-ilk-filmler/",
        "//dil/turkce-dublajli-film-izleyin-4/",
        "//yil/2025-filmleri-izle-3/",
        "//tur/aile-filmleri-izleyin-7/",
        "//tur/aksiyon-filmleri-izleyin-6/",
        "//tur/bilim-kurgu-filmlerini-izleyin-5/",
        "//tur/fantastik-filmlerini-izleyin-3/",
        "//category/1080p-hd-film-izle-5/",
        "//serifilmlerim-3/",
        "//ulke/turkiye-2/",
        "//tur/savas-filmleri-izle-5/",
        "//komedi-filmleri/",
        "//dram-filmleri/",
        "//gerilim-filmleri/",
        "//bilim-kurgu-filmleri/",
        "//fantastik-filmleri/",
        "//en-cok-begenilen-filmleri-izle-2/",
        "//en-cok-yorumlananlar-2/",
        "//imdb-7-puan-uzeri-filmler-2/",
 ] 
    
    print(f"Scraping using Base Domain: {BASE_DOMAIN}")
    
    for path in list_paths:
        full_url = urljoin(BASE_DOMAIN, path)
        print(f"  Testing: {full_url}")
        html_content = get_html(full_url)
        if html_content:
            films = extract_films_from_html(html_content, full_url)
            # Logic to add unique films...
            all_films.extend(films)
            
    # Automated Page range
    for i in range(1, 6):
        page_url = f"{BASE_DOMAIN}/sayfa/{i}/"
        # scrape...
        
    return all_films

# ... (rest of your helper functions)

if __name__ == '__main__':
    # You can even prompt for the domain if you want it to be fully interactive
    # BASE_DOMAIN = input("Enter current domain (e.g., https://www.hdfilmcehennemi.nl): ")
    main()
