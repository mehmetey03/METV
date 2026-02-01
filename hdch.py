#!/usr/bin/env python3
import urllib.request
import json
import re
import html
import time
import ssl
from datetime import datetime
from urllib.parse import urljoin, urlparse

# ==========================================================
# AYARLAR - DOMAİN DEĞİŞİRSE SADECE BURAYI GÜNCELLE
# ==========================================================
BASE_DOMAIN = "https://www.hdfilmcehennemi.nl"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url):
    """Gelişmiş HTTP İsteği (SSL ve Bot Koruması Aşımı)"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': BASE_DOMAIN + "/",
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

def clean_title(title):
    """Başlığı film ismine dönüştürür"""
    title = html.unescape(title)
    garbage = [r'\s*izle\s*', r'\s*türkçe\s*', r'\s*dublaj\s*', r'\s*altyazı\s*', r'\s*hd\s*', r'\s*full\s*']
    for pattern in garbage:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    return title.strip()

def parse_film_poster(poster_html):
    """HTML bloğundan film verilerini toplar"""
    try:
        url_match = re.search(r'href="([^"]+)"', poster_html)
        if not url_match: return None
        
        url = url_match.group(1)
        if not url.startswith('http'):
            url = urljoin(BASE_DOMAIN, url)
            
        title_match = re.search(r'title="([^"]+)"', poster_html)
        title = title_match.group(1) if title_match else "Bilinmeyen Başlık"
        
        token_match = re.search(r'data-token="(\d+)"', poster_html)
        token = token_match.group(1) if token_match else ""
        
        imdb_match = re.search(r'class="imdb"[^>]*>.*?(\d+\.\d+)', poster_html, re.DOTALL)
        imdb = imdb_match.group(1) if imdb_match else "0.0"

        return {
            'url': url,
            'title': clean_title(title),
            'imdb': imdb,
            'token': token,
            'type': 'dizi' if '/dizi/' in url else 'film',
            'scraped_at': datetime.now().isoformat()
        }
    except:
        return None

def get_embed_url(film_url, token):
    """Film sayfasının içinden asıl video linkini bulur"""
    content = get_html(film_url)
    if not content: return None
    
    # Yöntem 1: Iframe taraması
    iframe = re.search(r'iframe[^>]*?(?:src|data-src)="([^"]*?embed/[^"]+)"', content)
    if iframe:
        src = iframe.group(1)
        return src if src.startswith('http') else "https:" + src
    
    # Yöntem 2: Rapidrame ID (Token) üzerinden manuel oluşturma
    if token:
        return f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={token}"
    return None

def main():
    all_films = []
    seen_urls = set()
    
    print(f"--- BAŞLATILIYOR: {BASE_DOMAIN} ---")

    # 1. KATEGORİ VE KEŞİF LİSTESİ
    list_paths = [
        "/", "/category/film-izle-2/", "/category/nette-ilk-filmler/",
        "/dil/turkce-dublajli-film-izleyin-4/", "/yil/2025-filmleri-izle-3/",
        "/tur/aksiyon-filmleri-izleyin-6/", "/tur/bilim-kurgu-filmlerini-izleyin-5/",
        "/imdb-7-puan-uzeri-filmler-2/", "/en-cok-begenilen-filmleri-izle-2/"
    ]

    # Sayfaları tara (Keşif)
    for path in list_paths:
        target = urljoin(BASE_DOMAIN, path)
        print(f"Taranyor: {target}")
        html_content = get_html(target)
        if html_content:
            posters = re.findall(r'<a\s+[^>]*?data-token="\d+"[^>]*?>.*?</a>', html_content, re.DOTALL)
            for p in posters:
                film = parse_film_poster(p)
                if film and film['url'] not in seen_urls:
                    all_films.append(film)
                    seen_urls.add(film['url'])
        time.sleep(0.5)

    # 2. ARAMA BAZLI KEŞİF (Daha fazla film bulmak için)
    search_terms = ["2024", "2025", "aksiyon", "macera"]
    for term in search_terms:
        search_url = f"{BASE_DOMAIN}/?s={term}"
        print(f"Aranıyor: {term}")
        html_content = get_html(search_url)
        if html_content:
            posters = re.findall(r'<a\s+[^>]*?data-token="\d+"[^>]*?>.*?</a>', html_content, re.DOTALL)
            for p in posters:
                film = parse_film_poster(p)
                if film and film['url'] not in seen_urls:
                    all_films.append(film)
                    seen_urls.add(film['url'])

    # 3. DETAYLARI VE EMBEDLERİ AL
    print(f"\n--- {len(all_films)} İçerik İçin Embed Linkleri Çekiliyor ---")
    final_data = []
    for i, film in enumerate(all_films, 1):
        print(f"[{i}/{len(all_films)}] {film['title']}")
        film['embed_url'] = get_embed_url(film['url'], film['token'])
        final_data.append(film)
        
        # Her 20 filmde bir kaydet (Çökme riskine karşı yedekleme)
        if i % 20 == 0:
            with open('hdceh_backup.json', 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)

    # 4. FİNAL KAYIT VE ÖZET
    output_file = 'hdceh_full_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print("\n" + "="*50)
    print(f"İŞLEM TAMAMLANDI!")
    print(f"Toplam Bulunan: {len(final_data)}")
    print(f"Dosya: {output_file}")
    print("="*50)

if __name__ == '__main__':
    main()
