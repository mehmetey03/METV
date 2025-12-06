import requests
from bs4 import BeautifulSoup
import json
import time
import re

BASE = "https://dizipall30.com"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

def get_html(url):
    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except:
        return ""

def scrape_simple():
    """PHP'deki regex mantığını kullanan basit scraper"""
    all_movies = []
    page = 1
    
    while page <= 3:  # Sadece 3 sayfa test
        if page == 1:
            url = f"{BASE}/filmler"
        else:
            url = f"{BASE}/filmler/{page}"
        
        print(f"→ Sayfa {page}: {url}")
        html = get_html(url)
        
        if not html:
            break
        
        # PHP'deki regex pattern'ini kullan
        pattern = r'<li\s+class="[^"]*w-1/2[^"]*"[^>]*>(.*?)</li>'
        matches = re.findall(pattern, html, re.DOTALL)
        
        print(f"  • Regex ile {len(matches)} blok bulundu")
        
        for i, content in enumerate(matches[:3]):  # İlk 3'ü göster
            print(f"\n  Blok {i+1}:")
            
            # Başlık
            title_match = re.search(r'<h2[^>]*class="truncate"[^>]*>(.*?)</h2>', content, re.DOTALL)
            title = title_match.group(1).strip() if title_match else "Başlık Yok"
            title = re.sub(r'<[^>]+>', '', title)  # HTML tag'larını temizle
            print(f"    Başlık: {title}")
            
            # Puan
            rating_match = re.search(r'<span[^>]*class="[^"]*rating[^"]*"[^>]*>.*?</svg>\s*([\d\.]+)', content, re.DOTALL)
            rating = rating_match.group(1) if rating_match else "0.0"
            print(f"    Puan: {rating}")
            
            # Yıl
            year_match = re.search(r'<span[^>]*class="[^"]*year[^"]*"[^>]*>([^<]+)</span>', content)
            year = year_match.group(1).strip() if year_match else ""
            print(f"    Yıl: {year}")
            
            # Tür
            genre_match = re.search(r'<p[^>]*class="truncate"[^>]*title="([^"]+)"', content)
            genre = genre_match.group(1) if genre_match else ""
            print(f"    Tür: {genre}")
            
            # Resim
            img_match = re.search(r'(?:src|data-src)="(https://dizipall30\.com/uploads/movies/original/[^"]+\.webp)"', content)
            img = img_match.group(1) if img_match else ""
            print(f"    Resim: {img[:50]}...")
            
            # Detay URL
            url_match = re.search(r'href="(https://dizipall30\.com/film/[^"]+)"', content)
            detail = url_match.group(1) if url_match else ""
            print(f"    Detay: {detail}")
        
        time.sleep(1)
        page += 1
    
    return all_movies

if __name__ == "__main__":
    print("🔍 Basit scraper testi...\n")
    movies = scrape_simple()
