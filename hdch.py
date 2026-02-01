#!/usr/bin/env python3
import urllib.request
import json
import re
import html
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

# ==========================================================
# DOMAIN DEĞİŞTİĞİNDE SADECE BURAYI GÜNCELLEYİN
# ==========================================================
BASE_DOMAIN = "https://www.hdfilmcehennemi.nl" 
# ==========================================================

EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url, headers=None):
    """HTML içeriğini güvenli bir şekilde çeker"""
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

def clean_title(title):
    """Başlığı temizler"""
    title = html.unescape(title)
    suffixes = [r'\s*izle\s*$', r'\s*türkçe\s*$', r'\s*dublaj\s*$', r'\s*altyazı\s*$', r'\s*hd\s*$']
    for suffix in suffixes:
        title = re.sub(suffix, '', title, flags=re.IGNORECASE)
    return title.strip()

def parse_film_poster(poster_html, source_url):
    """Poster bloğundan film verilerini ayıklar"""
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
        
        # Token ve IMDB gibi diğer verileri çekme denemesi
        token_match = re.search(r'data-token="(\d+)"', poster_html)
        token = token_match.group(1) if token_match else ""
        
        return {
            'url': url,
            'title': clean_title(title),
            'type': 'dizi' if '/dizi/' in url else 'film',
            'token': token,
            'source': source_url,
            'scraped_at': datetime.now().isoformat()
        }
    except:
        return None

def extract_films_from_html(html_content, source_url):
    """Sayfa içindeki tüm film posterlerini bulur"""
    films = []
    if not html_content: return films
    
    film_pattern = r'<a\s+[^>]*data-token="\d+"[^>]*>.*?</a>'
    film_matches = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    for match in film_matches:
        film = parse_film_poster(match, source_url)
        if film: films.append(film)
    return films

def scrape_discovery_pages():
    """Kategori ve keşfet sayfalarını tarar"""
    all_films = []
    seen_urls = set()
    
    list_paths = [
        "/",
        "/category/film-izle-2/",
        "/category/nette-ilk-filmler/",
        "/dil/turkce-dublajli-film-izleyin-4/",
        "/yil/2025-filmleri-izle-3/",
        "/tur/aile-filmleri-izleyin-7/",
        "/tur/aksiyon-filmleri-izleyin-6/",
        "/tur/bilim-kurgu-filmlerini-izleyin-5/",
        "/category/1080p-hd-film-izle-5/",
        "/ulke/turkiye-2/",
        "/en-cok-begenilen-filmleri-izle-2/",
        "/imdb-7-puan-uzeri-filmler-2/",
    ]
    
    print(f"--- BAŞLATILIYOR: {BASE_DOMAIN} ---")
    
    for path in list_paths:
        full_url = urljoin(BASE_DOMAIN, path)
        print(f"Taranyor: {full_url}")
        html_content = get_html(full_url)
        if html_content:
            found = extract_films_from_html(html_content, full_url)
            for f in found:
                if f['url'] not in seen_urls:
                    all_films.append(f)
                    seen_urls.add(f['url'])
        time.sleep(0.5)

    # Otomatik Sayfalama (İlk 5 Sayfa)
    for i in range(1, 6):
        page_url = f"{BASE_DOMAIN}/sayfa/{i}/"
        print(f"Sayfa taranıyor: {page_url}")
        html_content = get_html(page_url)
        if html_content:
            found = extract_films_from_html(html_content, page_url)
            for f in found:
                if f['url'] not in seen_urls:
                    all_films.append(f)
                    seen_urls.add(f['url'])
                    
    return all_films

def main():
    # 1. Filmleri Keşfet
    unique_films = scrape_discovery_pages()
    print(f"\nToplam {len(unique_films)} benzersiz içerik bulundu.")

    # 2. Sonuçları Kaydet
    output_file = 'hdceh_list.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_films, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Veriler başarıyla kaydedildi: {output_file}")
    except Exception as e:
        print(f"❌ Kayıt hatası: {e}")

if __name__ == '__main__':
    main()
