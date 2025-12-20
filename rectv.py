#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import requests
import sys
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin

# ==================== YAPILANDIRMA ====================
# Varsayılan değerler (SADECE BAŞARISIZLIK DURUMUNDA)
DEFAULT_MAIN_URL = 'https://m.prectv60.lol'
DEFAULT_SW_KEY = '4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452/'
DEFAULT_USER_AGENT = 'okhttp/4.12.0/'
DEFAULT_REFERER = 'https://twitter.com/'
PAGE_COUNT = 4

# M3U çıktısı için sabit User-Agent
M3U_USER_AGENT = 'googleusercontent'

# GitHub kaynak dosyası
SOURCE_URL_RAW = 'https://raw.githubusercontent.com/nikyokki/nik-cloudstream/refs/heads/master/RecTV/src/main/kotlin/com/keyiflerolsun/RecTV.kt'
PROXY_URL = 'https://api.codetabs.com/v1/proxy/?quest=' + requests.utils.quote(SOURCE_URL_RAW)

# ==================== FONKSİYONLAR ====================
def fetch_github_content():
    """GitHub'dan içeriği çek"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Direkt GitHub'dan çek
        response = requests.get(SOURCE_URL_RAW, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.text
    except:
        pass
    
    try:
        # Proxy üzerinden çek
        response = requests.get(PROXY_URL, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.text
    except:
        pass
    
    return None

def parse_github_headers(github_content):
    """GitHub içeriğinden header bilgilerini parse et"""
    headers = {
        'mainUrl': None,
        'swKey': None,
        'userAgent': None,
        'referer': None
    }
    
    if not github_content:
        return headers
    
    # mainUrl - Kotlin syntax'ı
    match = re.search(r'override\s+var\s+mainUrl\s*=\s*"([^"]+)"', github_content)
    if match:
        headers['mainUrl'] = match.group(1)
        print(f"GitHub'dan mainUrl alındı: {headers['mainUrl']}")
    
    # swKey - Kotlin syntax'ı
    match = re.search(r'private\s+(val|var)\s+swKey\s*=\s*"([^"]+)"', github_content)
    if match:
        headers['swKey'] = match.group(2)
        print(f"GitHub'dan swKey alındı: {headers['swKey']}")
    
    # user-agent - headers mapOf içinde
    match = re.search(r'headers\s*=\s*mapOf\([^)]*"user-agent"[^)]*to[^"]*"([^"]+)"', github_content, re.DOTALL)
    if match:
        headers['userAgent'] = match.group(1)
        print(f"GitHub'dan userAgent alındı: {headers['userAgent']}")
    
    # referer - farklı şekillerde ara
    match = re.search(r'this\.referer\s*=\s*"([^"]+)"', github_content)
    if match:
        headers['referer'] = match.group(1)
        print(f"GitHub'dan referer alındı (this.referer): {headers['referer']}")
    else:
        match = re.search(r'referer\s*=\s*"([^"]+)"', github_content)
        if match:
            headers['referer'] = match.group(1)
            print(f"GitHub'dan referer alındı (referer): {headers['referer']}")
        else:
            match = re.search(r'headers\s*=\s*mapOf\([^)]*"Referer"[^)]*to[^"]*"([^"]+)"', github_content, re.DOTALL)
            if match:
                headers['referer'] = match.group(1)
                print(f"GitHub'dan referer alındı (headers): {headers['referer']}")
    
    return headers

def test_api_with_headers(main_url, sw_key, user_agent, referer):
    """Header'larla API testi yap"""
    test_url = f"{main_url}/api/channel/by/filtres/0/0/0/{sw_key}"
    print(f"API test URL: {test_url}")
    print(f"Test Header - User-Agent: {user_agent}")
    print(f"Test Header - Referer: {referer}")
    
    headers = {
        'User-Agent': user_agent,
        'Referer': referer
    }
    
    try:
        response = requests.get(test_url, headers=headers, timeout=15, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✓ API testi BAŞARILI - {len(data)} kanal bulundu")
                return True
            else:
                print("✗ API testi BAŞARISIZ - Geçersiz JSON formatı")
                return False
        else:
            print(f"✗ API testi BAŞARISIZ - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API testi BAŞARISIZ - Hata: {e}")
        return False

def create_m3u_content(main_url, sw_key, user_agent, referer, source):
    """M3U içeriğini oluştur"""
    print(f"\n=== SON KULLANILAN DEĞERLER ===")
    print(f"Kaynak: {source}")
    print(f"Main URL: {main_url}")
    print(f"SwKey: {sw_key}")
    print(f"User-Agent: {user_agent}")
    print(f"Referer: {referer}")
    print(f"M3U User-Agent: {M3U_USER_AGENT}")
    
    print("\n=== M3U OLUŞTURULUYOR ===")
    m3u_content = "#EXTM3U\n"
    
    headers = {
        'User-Agent': user_agent,
        'Referer': referer
    }
    
    # CANLI YAYINLAR
    print("Canlı yayınlar alınıyor...")
    total_channels = 0
    
    for page in range(PAGE_COUNT):
        api_url = f"{main_url}/api/channel/by/filtres/0/0/{page}/{sw_key}"
        
        try:
            response = requests.get(api_url, headers=headers, timeout=30, verify=False)
            if response.status_code != 200:
                print(f"API hatası: {api_url} - HTTP {response.status_code}")
                continue
                
            data = response.json()
            if not isinstance(data, list):
                print(f"JSON decode hatası: {api_url}")
                continue
            
            channel_count = 0
            for content in data:
                if 'sources' in content and isinstance(content['sources'], list):
                    for source_item in content['sources']:
                        if source_item.get('type') == 'm3u8' and 'url' in source_item:
                            channel_count += 1
                            total_channels += 1
                            
                            title = content.get('title', '')
                            
                            # Resim URL'sini oluştur
                            image = content.get('image', '')
                            if image and not image.startswith('http'):
                                image = urljoin(main_url + '/', image.lstrip('/'))
                            
                            # Kategorileri birleştir
                            categories = ''
                            if 'categories' in content and isinstance(content['categories'], list):
                                categories = ', '.join([cat.get('title', '') for cat in content['categories']])
                            
                            # M3U girişi ekle
                            m3u_content += f'#EXTINF:-1 tvg-id="{content.get("id", "")}" tvg-name="{title}" tvg-logo="{image}" group-title="{categories}", {title}\n'
                            m3u_content += f'#EXTVLCOPT:http-user-agent={M3U_USER_AGENT}\n'
                            m3u_content += f'#EXTVLCOPT:http-referrer={referer}\n'
                            m3u_content += f"{source_item['url']}\n"
            
            print(f"Sayfa {page}: {channel_count} kanal eklendi")
            
        except Exception as e:
            print(f"Hata sayfa {page}: {e}")
            continue
    
    print(f"Toplam: {total_channels} kanal eklendi")
    
    # FİLMLER
    print("\nFilmler alınıyor...")
    movie_apis = {
        "api/movie/by/filtres/0/created/SAYFA/": "Son Filmler",
        "api/movie/by/filtres/14/created/SAYFA/": "Aile",
        "api/movie/by/filtres/1/created/SAYFA/": "Aksiyon",
        "api/movie/by/filtres/13/created/SAYFA/": "Animasyon",
        "api/movie/by/filtres/19/created/SAYFA/": "Belgesel Filmleri",
        "api/movie/by/filtres/4/created/SAYFA/": "Bilim Kurgu",
        "api/movie/by/filtres/2/created/SAYFA/": "Dram",
        "api/movie/by/filtres/10/created/SAYFA/": "Fantastik",
        "api/movie/by/filtres/3/created/SAYFA/": "Komedi",
        "api/movie/by/filtres/8/created/SAYFA/": "Korku",
        "api/movie/by/filtres/17/created/SAYFA/": "Macera",
        "api/movie/by/filtres/5/created/SAYFA/": "Romantik",
    }
    
    for api_path, category_name in movie_apis.items():
        total_movies = 0
        
        for page in range(26):  # 0-25
            api_url = f"{main_url}/{api_path.replace('SAYFA', str(page))}{sw_key}"
            
            try:
                response = requests.get(api_url, headers=headers, timeout=30, verify=False)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                if not data:
                    break
                
                movie_count = 0
                for content in data:
                    if 'sources' in content and isinstance(content['sources'], list):
                        for source_item in content['sources']:
                            if source_item.get('type') == 'm3u8' and 'url' in source_item:
                                movie_count += 1
                                total_movies += 1
                                
                                title = content.get('title', '')
                                
                                # Resim URL'sini oluştur
                                image = content.get('image', '')
                                if image and not image.startswith('http'):
                                    image = urljoin(main_url + '/', image.lstrip('/'))
                                
                                # M3U girişi ekle
                                m3u_content += f'#EXTINF:-1 tvg-id="{content.get("id", "")}" tvg-name="{title}" tvg-logo="{image}" group-title="{category_name}", {title}\n'
                                m3u_content += f'#EXTVLCOPT:http-user-agent={M3U_USER_AGENT}\n'
                                m3u_content += f'#EXTVLCOPT:http-referrer={referer}\n'
                                m3u_content += f"{source_item['url']}\n"
                
                if movie_count == 0:
                    break
                    
            except:
                break
        
        print(f"{category_name}: {total_movies} film eklendi")
    
    # DİZİLER
    print("\nDiziler alınıyor...")
    series_apis = {
        "api/serie/by/filtres/0/created/SAYFA/": "Son Diziler"
    }
    
    for api_path, category_name in series_apis.items():
        total_series = 0
        
        for page in range(26):  # 0-25
            api_url = f"{main_url}/{api_path.replace('SAYFA', str(page))}{sw_key}"
            
            try:
                response = requests.get(api_url, headers=headers, timeout=30, verify=False)
                if response.status_code != 200:
                    break
                    
                data = response.json()
                if not data:
                    break
                
                series_count = 0
                for content in data:
                    if 'sources' in content and isinstance(content['sources'], list):
                        for source_item in content['sources']:
                            if source_item.get('type') == 'm3u8' and 'url' in source_item:
                                series_count += 1
                                total_series += 1
                                
                                title = content.get('title', '')
                                
                                # Resim URL'sini oluştur
                                image = content.get('image', '')
                                if image and not image.startswith('http'):
                                    image = urljoin(main_url + '/', image.lstrip('/'))
                                
                                # M3U girişi ekle
                                m3u_content += f'#EXTINF:-1 tvg-id="{content.get("id", "")}" tvg-name="{title}" tvg-logo="{image}" group-title="{category_name}", {title}\n'
                                m3u_content += f'#EXTVLCOPT:http-user-agent={M3U_USER_AGENT}\n'
                                m3u_content += f'#EXTVLCOPT:http-referrer={referer}\n'
                                m3u_content += f"{source_item['url']}\n"
                
                if series_count == 0:
                    break
                    
            except:
                break
        
        print(f"{category_name}: {total_series} dizi eklendi")
    
    return m3u_content

# ==================== ANA PROGRAM ====================
def main():
    print("=== GITHUB HEADER TESTİ ===")
    
    # 1. GitHub'dan içeriği al
    github_content = fetch_github_content()
    
    if github_content:
        print("✓ GitHub içeriği başarıyla alındı")
        
        # 2. GitHub içeriğini parse et
        github_headers = parse_github_headers(github_content)
        
        # 3. GitHub'dan gelen değerlerin tamamı var mı kontrol et
        if all(github_headers.values()):
            print("\n=== API TESTİ (GITHUB HEADER'LARI İLE) ===")
            
            # İLK ETAP: GitHub header'ları ile API testi
            api_test_result = test_api_with_headers(
                github_headers['mainUrl'],
                github_headers['swKey'],
                github_headers['userAgent'],
                github_headers['referer']
            )
            
            if api_test_result:
                print("\n✓ İLK ETAP BAŞARILI - GitHub header'ları kullanılacak")
                main_url = github_headers['mainUrl']
                sw_key = github_headers['swKey']
                user_agent = github_headers['userAgent']
                referer = github_headers['referer']
                source = "GITHUB"
            else:
                print("\n✗ İLK ETAP BAŞARISIZ - Varsayılan değerlerle test yapılıyor...")
                
                # İKİNCİ ETAP: Varsayılan değerlerle test
                default_test_result = test_api_with_headers(
                    DEFAULT_MAIN_URL,
                    DEFAULT_SW_KEY,
                    DEFAULT_USER_AGENT,
                    DEFAULT_REFERER
                )
                
                if default_test_result:
                    print("\n✓ İKİNCİ ETAP BAŞARILI - Varsayılan değerler kullanılacak")
                    main_url = DEFAULT_MAIN_URL
                    sw_key = DEFAULT_SW_KEY
                    user_agent = DEFAULT_USER_AGENT
                    referer = DEFAULT_REFERER
                    source = "VARSayILAN"
                else:
                    print("\n✗ TÜM TESTLER BAŞARISIZ - Son çare varsayılan değerler kullanılacak")
                    main_url = DEFAULT_MAIN_URL
                    sw_key = DEFAULT_SW_KEY
                    user_agent = DEFAULT_USER_AGENT
                    referer = DEFAULT_REFERER
                    source = "VARSayILAN (ZORUNLU)"
        else:
            print("✗ GitHub'dan eksik header bilgileri! Varsayılan değerler kullanılıyor.")
            main_url = DEFAULT_MAIN_URL
            sw_key = DEFAULT_SW_KEY
            user_agent = DEFAULT_USER_AGENT
            referer = DEFAULT_REFERER
            source = "VARSayILAN"
    else:
        print("✗ GitHub içeriği alınamadı! Varsayılan değerler kullanılıyor.")
        main_url = DEFAULT_MAIN_URL
        sw_key = DEFAULT_SW_KEY
        user_agent = DEFAULT_USER_AGENT
        referer = DEFAULT_REFERER
        source = "VARSayILAN"
    
    # 4. M3U içeriğini oluştur
    m3u_content = create_m3u_content(main_url, sw_key, user_agent, referer, source)
    
    # 5. Dosyaya kaydet
    with open('rectv.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print(f"\nOluşturulan M3U dosyası: rectv.m3u")
    print("İşlem tamamlandı!")

if __name__ == "__main__":
    main()
