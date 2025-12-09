#!/usr/bin/env python3
"""
hdfilm_working.py - Working HDFilmCehennemi scraper
"""
import requests
import json
import re
import time
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://www.hdfilmcehennemi.ws/"

def fetch_page(url):
    """Fetch page with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
        'Referer': BASE_URL,
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_films_from_category(html, category_url):
    """Extract films from category page HTML"""
    films = []
    
    if not html:
        return films
    
    # Look for the posters container
    poster_container_pattern = r'<div class="posters-[^"]*"[^>]*>(.*?)</div>\s*</div>'
    container_match = re.search(poster_container_pattern, html, re.DOTALL)
    
    if not container_match:
        print("No poster container found")
        return films
    
    container_html = container_match.group(1)
    
    # Find all poster links
    poster_pattern = r'<a\s+[^>]*class="poster"[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>(.*?)</a>'
    poster_matches = re.finditer(poster_pattern, container_html, re.DOTALL | re.IGNORECASE)
    
    for match in poster_matches:
        try:
            url = match.group(1)
            title = match.group(2)
            content = match.group(3)
            
            # Clean title
            title = title.strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'<span>(\d{4})</span>', content)
            if year_match:
                year = year_match.group(1)
            
            # Extract IMDB rating
            imdb = '0.0'
            imdb_match = re.search(r'<span class="imdb">.*?(\d+\.\d+)</span>', content, re.DOTALL)
            if imdb_match:
                imdb = imdb_match.group(1)
            
            # Extract comments count
            comments = '0'
            comments_match = re.search(r'<span>\s*<svg[^>]*>.*?</svg>\s*(\d+)\s*</span>', content, re.DOTALL)
            if comments_match:
                comments = comments_match.group(1)
            
            # Extract image
            image = ''
            img_match = re.search(r'src="([^"]+\.webp)"', content)
            if img_match:
                image = img_match.group(1)
            
            # Extract language
            language = ''
            lang_match = re.search(r'<span class="poster-lang">.*?<span>\s*(.*?)\s*</span>', content, re.DOTALL)
            if lang_match:
                language = lang_match.group(1).strip()
            
            # Determine type (film or dizi)
            film_type = 'film'
            if '/dizi/' in url:
                film_type = 'dizi'
            
            # Extract token
            token = ''
            token_match = re.search(r'data-token="(\d+)"', match.group(0))
            if token_match:
                token = token_match.group(1)
            
            films.append({
                'url': url,
                'title': title,
                'year': year,
                'imdb': imdb,
                'comments': comments,
                'image': image,
                'language': language,
                'type': film_type,
                'token': token,
                'scraped_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error processing film: {e}")
            continue
    
    return films

def get_pagination_info(html):
    """Get pagination information from page"""
    # Look for data-page-items attribute
    page_items_match = re.search(r'data-page-items="(\d+)"', html)
    if page_items_match:
        return int(page_items_match.group(1))
    
    # Try to find total pages
    total_pages_match = re.search(r'data-pages="(\d+)"', html)
    if total_pages_match:
        return int(total_pages_match.group(1))
    
    return 1

def scrape_category(category_url, max_pages=5):
    """Scrape a category with pagination"""
    all_films = []
    
    for page in range(1, max_pages + 1):
        if page == 1:
            url = category_url
        else:
            # Try different pagination formats
            url = f"{category_url}page/{page}/"
        
        print(f"Scraping page {page}...")
        html = fetch_page(url)
        
        if not html:
            print(f"  Failed to fetch page {page}")
            break
        
        films = extract_films_from_category(html, url)
        
        if not films:
            print(f"  No films found on page {page}")
            break
        
        all_films.extend(films)
        print(f"  Found {len(films)} films on page {page}")
        
        # Check if there are more pages
        if page == 1:
            total_items = get_pagination_info(html)
            if total_items <= len(films):
                print(f"  Only one page found ({total_items} items)")
                break
        
        # Be polite
        time.sleep(1)
    
    return all_films

def get_categories():
    """Get available categories"""
    categories = [
        {
            'name': 'Film İzle',
            'url': f"{BASE_URL}category/film-izle-2/",
            'type': 'film'
        },
        {
            'name': 'Dizi İzle',
            'url': f"{BASE_URL}category/dizi-izle-2/",
            'type': 'dizi'
        },
        {
            'name': 'Yerli Filmler',
            'url': f"{BASE_URL}category/yerli-film-izle/",
            'type': 'film'
        },
        {
            'name': 'Yabancı Dizi',
            'url': f"{BASE_URL}category/yabanci-dizi-izle/",
            'type': 'dizi'
        },
        {
            'name': '1080p Film',
            'url': f"{BASE_URL}category/1080p-film-izle/",
            'type': 'film'
        },
        {
            'name': 'Netflix',
            'url': f"{BASE_URL}category/netflix-film-izle/",
            'type': 'film'
        }
    ]
    return categories

def main():
    print("HDFilmCehennemi Scraper")
    print("=" * 60)
    
    # Get available categories
    categories = get_categories()
    
    print(f"\nFound {len(categories)} categories:")
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat['name']} ({cat['type']})")
    
    all_films = []
    
    # Scrape each category
    for category in categories:
        print(f"\n{'='*60}")
        print(f"Scraping: {category['name']}")
        print(f"URL: {category['url']}")
        print(f"{'='*60}")
        
        category_films = scrape_category(category['url'], max_pages=3)
        all_films.extend(category_films)
        
        print(f"Total from {category['name']}: {len(category_films)} films")
        
        # Be polite between categories
        time.sleep(2)
    
    # Remove duplicates
    unique_films = []
    seen_urls = set()
    
    for film in all_films:
        if film['url'] not in seen_urls:
            seen_urls.add(film['url'])
            unique_films.append(film)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total films collected: {len(all_films)}")
    print(f"Unique films: {len(unique_films)}")
    
    if not unique_films:
        print("\n❌ No films found!")
        return
    
    # Organize by type
    films_by_type = {'film': [], 'dizi': []}
    for film in unique_films:
        films_by_type[film['type']].append(film)
    
    # Save results
    result = {
        'metadata': {
            'scraped_at': datetime.now().isoformat(),
            'total_films': len(unique_films),
            'films_count': len(films_by_type['film']),
            'diziler_count': len(films_by_type['dizi']),
            'categories_scraped': [cat['name'] for cat in categories]
        },
        'films_by_type': films_by_type,
        'all_films': unique_films
    }
    
    filename = 'hdfilms_complete.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to: {filename}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total unique films: {len(unique_films)}")
    print(f"Films: {len(films_by_type['film'])}")
    print(f"Diziler: {len(films_by_type['dizi'])}")
    
    # Years distribution
    years = {}
    for film in unique_films:
        year = film.get('year', 'Unknown')
        years[year] = years.get(year, 0) + 1
    
    if years:
        print(f"\nYears distribution ({len(years)} different years):")
        sorted_years = sorted([(y, c) for y, c in years.items() if y != '' and y != 'Unknown'], 
                            key=lambda x: x[1], reverse=True)
        for year, count in sorted_years[:10]:
            print(f"  {year}: {count} films")
    
    # Top films by IMDB
    films_with_imdb = [f for f in unique_films if f.get('imdb', '0.0') not in ['0.0', '0', '']]
    if films_with_imdb:
        films_with_imdb.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
        print(f"\nTop films by IMDB rating:")
        for idx, film in enumerate(films_with_imdb[:10], 1):
            print(f"{idx:2}. {film['title'][:40]:40} ({film.get('year', 'N/A'):4}) - IMDB: {film['imdb']}")
    
    # Sample films
    print(f"\nSample films (first 10):")
    for idx, film in enumerate(unique_films[:10], 1):
        imdb = f"IMDB: {film['imdb']}" if film['imdb'] != '0.0' else ""
        year = f"({film['year']})" if film['year'] else ""
        print(f"{idx:2}. {film['title'][:40]:40} {year:8} {imdb}")

def test_single_category():
    """Test scraping a single category"""
    print("Testing single category scraping...")
    
    test_url = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"
    
    html = fetch_page(test_url)
    if not html:
        print("Failed to fetch page")
        return
    
    films = extract_films_from_category(html, test_url)
    
    print(f"\nFound {len(films)} films in category")
    
    if films:
        print("\nFirst 5 films:")
        for i, film in enumerate(films[:5], 1):
            print(f"{i}. {film['title']} ({film.get('year', 'N/A')}) - IMDB: {film['imdb']}")
            print(f"   URL: {film['url']}")
            print(f"   Image: {film['image'][:50]}..." if film['image'] else "   No image")
            print()

if __name__ == '__main__':
    # Uncomment for quick testing
    # test_single_category()
    
    # Run main scraper
    main()
