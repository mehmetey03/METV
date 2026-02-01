#!/usr/bin/env python3
import json
import re
import html
import time
import requests
from datetime import datetime
from urllib.parse import urljoin

# ==========================================================
# AYARLAR
# ==========================================================
BASE_DOMAIN = "https://www.hdfilmcehennemi.nl"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

# HTTP Session başlat (Çerezleri ve bağlantıyı korur)
session = requests.Session()

def get_html(url):
    """Modern bot korumalarını aşmak için geliştirilmiş istek yapısı"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': BASE_DOMAIN + "/",
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
    }
    try:
        # verify=False SSL hatalarını es geçer
        response = session.get(url, headers=headers, timeout=15, verify=True)
        if response.status_code == 200:
            return response.text
        else:
            print(f"      [!] Hata: HTTP {response.status_code} ({url})")
            return None
    except Exception as e:
        print(f"      [!] Bağlantı koptu: {e}")
        return None

def clean_title(title):
    title = html.unescape(title)
    garbage = [r'\s*izle\s*', r'\s*türkçe\s*', r'\s*dublaj\s*', r'\s*altyazı\s*', r'\s*hd\s*', r'\s*full\s*']
    for pattern in garbage:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    return title.strip()

def parse_film_poster(poster_html):
    try:
        url_match = re.search(r'href="([^"]+)"', poster_html)
        if not url_match: return None
        url = urljoin(BASE_DOMAIN, url_match.group(1))
        
        title_match = re.search(r'title="([^"]+)"', poster_html)
        title = title_match.group(1) if title_match else "Bilinmeyen"
        
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
    content = get_html(film_url)
    if not content: return None
    
    # Sayfa içindeki iframe'leri tara
    iframe = re.search(r'iframe[^>]*?(?:src|data-src)="([^"]*?embed/[^"]+)"', content)
    if iframe:
        src = iframe.group(1)
        return src if src.startswith('http') else "https:" + src
    
    # Token üzerinden üret (Site mantığına göre)
    if token:
        return f"{EMBED_BASE}GKsnOLw2hsT/?rapidrame_id={token}"
    return None

def main():
    all_films = []
    seen_urls = set()
    
    # 1. FAZ: KATEGORİ TARAMASI
    paths = ["/", "/category/film-izle-2/", "/category/nette-ilk-filmler/", "/imdb-7-puan-uzeri-filmler-2/"]
    
    print(f"--- BAŞLATILIYOR: {BASE_DOMAIN} ---")
    
    for path in paths:
        url = urljoin(BASE_DOMAIN, path)
        print(f"Taranıyor: {url}")
        html_content = get_html(url)
        
        if html_content:
            # Regex desenini daha esnek hale getirdim
            posters = re.findall(r'<a[^>]*data-token="\d+"[^>]*>.*?</a>', html_content, re.DOTALL)
            print(f"   Analiz: {len(posters)} potansiyel film bulundu.")
            
            for p in posters:
                film = parse_film_poster(p)
                if film and film['url'] not in seen_urls:
                    all_films.append(film)
                    seen_urls.add(film['url'])
        time.sleep(1)

    if not all_films:
        print("\n[!] KRİTİK HATA: Hiç film bulunamadı. Site botu tamamen engelliyor olabilir.")
        return

    # 2. FAZ: EMBED ÇEKİMİ
    print(f"\n--- {len(all_films)} Film İçin Detaylar Alınıyor ---")
    for i, film in enumerate(all_films, 1):
        print(f"[{i}/{len(all_films)}] {film['title']}")
        film['embed_url'] = get_embed_url(film['url'], film['token'])
        time.sleep(0.5)

    # 3. KAYIT
    with open('hdceh_full_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_films, f, ensure_ascii=False, indent=2)

    print(f"\n✅ İŞLEM TAMAMLANDI! {len(all_films)} içerik kaydedildi.")

if __name__ == '__main__':
    main()
