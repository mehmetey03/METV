#!/usr/bin/env python3
"""
hdch_fixed_ultimate.py - Fixed HDFilmCehennemi scraper
"""
import urllib.request
import json
import re
import html
import time
import random
from datetime import datetime
from urllib.parse import urljoin, parse_qs

BASE_URL = "https://www.hdfilmcehennemi.ws/"
EMBED_BASE = "https://hdfilmcehennemi.mobi/video/embed/"

def get_html(url, headers=None):
    """Get HTML content with better error handling"""
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': BASE_URL,
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
        return None

def extract_films_from_html(html_content, source_url):
    """Extract films from HTML with improved patterns"""
    films = []
    
    if not html_content:
        return films
    
    # YENİ PATTERN: Daha geniş bir arama pattern'i
    # Film kartlarını bulmak için daha esnek pattern
    film_sections = re.findall(
        r'<article[^>]*>.*?</article>|<div[^>]*class="[^"]*poster[^"]*"[^>]*>.*?</div>',
        html_content, 
        re.DOTALL | re.IGNORECASE
    )
    
    if not film_sections:
        # Alternatif pattern: Link pattern'i
        film_pattern = r'<a\s+[^>]*href="[^"]*/(?:film|dizi)[^"]*"[^>]*>.*?</a>'
        film_sections = re.findall(film_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    for section in film_sections:
        film = parse_film_section(section, source_url)
        if film and film['title']:
            films.append(film)
    
    return films

def parse_film_section(section_html, source_url):
    """Parse a film section with multiple fallback methods"""
    try:
        film_data = {}
        
        # 1. URL'yi çıkar
        url_match = re.search(r'href="([^"]+)"', section_html)
        if url_match:
            url = url_match.group(1)
            if url and not url.startswith('http'):
                url = urljoin(BASE_URL, url)
            film_data['url'] = url
        else:
            return None
        
        # 2. Başlığı çıkar (birden fazla yöntem)
        title = ''
        
        # Yöntem 1: title attribute
        title_match = re.search(r'title="([^"]+)"', section_html)
        if title_match:
            title = html.unescape(title_match.group(1)).strip()
        
        # Yöntem 2: data-title attribute
        if not title:
            data_title_match = re.search(r'data-title="([^"]+)"', section_html)
            if data_title_match:
                title = html.unescape(data_title_match.group(1)).strip()
        
        # Yöntem 3: İçerikten başlık
        if not title:
            # Poster title class'ını ara
            title_match = re.search(r'class="[^"]*poster-title[^"]*"[^>]*>(.*?)</', section_html, re.DOTALL | re.IGNORECASE)
            if title_match:
                title_text = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                title = html.unescape(title_text)
        
        if not title:
            # URL'den başlık çıkarmayı dene
            url_parts = film_data['url'].split('/')
            if len(url_parts) >= 2:
                possible_title = url_parts[-2].replace('-', ' ').title()
                title = possible_title
        
        if not title:
            return None
        
        film_data['title'] = clean_title(title)
        
        # 3. Yıl
        year = ''
        year_match = re.search(r'<span[^>]*>\s*(\d{4})\s*</span>', section_html)
        if not year_match:
            year_match = re.search(r'class="[^"]*year[^"]*"[^>]*>\s*(\d{4})\s*</', section_html, re.IGNORECASE)
        
        if year_match:
            year = year_match.group(1)
        
        film_data['year'] = year
        
        # 4. IMDB puanı
        imdb = '0.0'
        imdb_match = re.search(r'class="[^"]*imdb[^"]*"[^>]*>.*?(\d+\.\d+)', section_html, re.DOTALL)
        if not imdb_match:
            imdb_match = re.search(r'IMDB.*?(\d+\.\d+)', section_html, re.DOTALL | re.IGNORECASE)
        
        if imdb_match:
            try:
                rating = float(imdb_match.group(1))
                if 1.0 <= rating <= 10.0:
                    imdb = f"{rating:.1f}"
            except:
                pass
        
        film_data['imdb'] = imdb
        
        # 5. Resim URL'si
        image = ''
        img_match = re.search(r'src="([^"]+\.(?:webp|jpg|jpeg|png|gif))"', section_html, re.IGNORECASE)
        if img_match:
            image = img_match.group(1)
            if image and not image.startswith('http'):
                image = urljoin(BASE_URL, image)
        
        film_data['image'] = image
        
        # 6. Token
        token = ''
        token_match = re.search(r'data-token="(\d+)"', section_html)
        if not token_match:
            token_match = re.search(r'token="(\d+)"', section_html)
        if not token_match:
            # URL'den token çıkarmayı dene
            token_match = re.search(r'-(\d+)/$', film_data['url'])
        
        if token_match:
            token = token_match.group(1)
        
        film_data['token'] = token
        
        # 7. Tür
        film_type = 'film'
        if '/dizi/' in film_data['url'].lower():
            film_type = 'dizi'
        
        film_data['type'] = film_type
        
        # 8. Dil
        language = ''
        section_lower = section_html.lower()
        if 'yerli' in section_lower:
            language = 'Yerli'
        elif 'dublaj' in section_lower and 'altyazı' in section_lower:
            language = 'Dublaj & Altyazılı'
        elif 'dublaj' in section_lower:
            language = 'Türkçe Dublaj'
        elif 'altyazı' in section_lower or 'altyazi' in section_lower:
            language = 'Türkçe Altyazı'
        else:
            language = 'Orjinal'
        
        film_data['language'] = language
        film_data['source'] = source_url
        film_data['scraped_at'] = datetime.now().isoformat()
        
        return film_data
        
    except Exception as e:
        print(f"    Parsing error: {e}")
        return None

def clean_title(title):
    """Clean and format title"""
    if not title:
        return ""
    
    title = html.unescape(title)
    
    # Kaldırılacak kelimeler
    remove_words = [
        'izle', 'türkçe', 'dublaj', 'altyazı', 'altyazi', 'yabancı',
        'dizi', 'film', 'hd', 'full', '1080p', '720p', 'online',
        'türkce', 'turkish', 'subtitles', 'subtitle', 'dubbed'
    ]
    
    # Pattern'ler
    patterns = [
        r'\s*\(\d{4}\)\s*$',
        r'\s*\[.*?\]\s*$',
        r'\s*\-.*?$',
        r'\s*–.*?$',
    ]
    
    # Pattern'leri uygula
    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Kelimeleri kaldır
    words = title.split()
    filtered_words = []
    for word in words:
        word_lower = word.lower()
        should_keep = True
        for remove_word in remove_words:
            if word_lower == remove_word.lower():
                should_keep = False
                break
        if should_keep:
            filtered_words.append(word)
    
    title = ' '.join(filtered_words)
    
    # Fazla boşlukları temizle
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Baş harfleri büyüt
    if title:
        title = title.title()
    
    return title

def extract_embed_url_from_film_page(film_url, token):
    """Extract embed URL from individual film page - FIXED VERSION"""
    if not film_url:
        return None
    
    print(f"    Fetching: {film_url}")
    html_content = get_html(film_url)
    
    if not html_content:
        print(f"      Failed to get HTML")
        return None
    
    # ÇOKLU PATTERN DENEMESİ
    
    # Pattern 1: iframe with data-src
    patterns = [
        (r'<iframe[^>]*data-src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"', "iframe data-src"),
        (r'<iframe[^>]*src="([^"]*hdfilmcehennemi\.mobi/video/embed/[^"]*)"', "iframe src"),
        (r'src="(https?://hdfilmcehennemi\.mobi/video/embed/[^"]*)"', "direct src"),
        (r'"(https?://hdfilmcehennemi\.mobi/video/embed/[^"]*)"', "quoted URL"),
        (r'video_url\s*[:=]\s*["\']([^"\']+)["\']', "video_url variable"),
        (r'embed_url\s*[:=]\s*["\']([^"\']+)["\']', "embed_url variable"),
        (r'player\.src\s*\(\s*["\']([^"\']+)["\']', "player.src"),
        (r'loadVideo\s*\(\s*["\']([^"\']+)["\']', "loadVideo"),
    ]
    
    for pattern, pattern_name in patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            embed_url = match.group(1)
            print(f"      Found with {pattern_name}")
            
            # URL'yi düzelt
            if embed_url.startswith('//'):
                embed_url = 'https:' + embed_url
            elif not embed_url.startswith('http'):
                embed_url = 'https://' + embed_url
            
            return embed_url
    
    # Pattern 2: rapidrame_id arasın
    rapidrame_patterns = [
        r'rapidrame_id=([a-zA-Z0-9]+)',
        r'id=([a-zA-Z0-9]+)',
        r'\?([a-zA-Z0-9]+)',
    ]
    
    for pattern in rapidrame_patterns:
        match = re.search(pattern, html_content)
        if match:
            video_id = match.group(1)
            print(f"      Found video ID: {video_id}")
            return f"https://hdfilmcehennemi.mobi/video/embed/GKsnOLw2hsT/?rapidrame_id={video_id}"
    
    # Pattern 3: Token kullan
    if token:
        print(f"      Using token: {token}")
        return f"https://hdfilmcehennemi.mobi/video/embed/GKsnOLw2hsT/?rapidrame_id={token}"
    
    # Pattern 4: URL'den ID çıkar
    url_id_match = re.search(r'/(\d+)/?$', film_url)
    if url_id_match:
        video_id = url_id_match.group(1)
        print(f"      Using URL ID: {video_id}")
        return f"https://hdfilmcehennemi.mobi/video/embed/GKsnOLw2hsT/?rapidrame_id={video_id}"
    
    print(f"      No embed URL found")
    return None

def scrape_all_films():
    """Tüm filmleri topla"""
    all_films = []
    seen_urls = set()
    
    print("=" * 70)
    print("HDFilmCehennemi - Tüm Filmleri Çekme")
    print("=" * 70)
    
    # 1. Ana sayfa ve popüler sayfalar
    print("\n1. Ana sayfa ve popüler listeler...")
    initial_urls = [
        BASE_URL,
        "https://www.hdfilmcehennemi.ws/film-robotu-1/",
        "https://www.hdfilmcehennemi.ws/film-robotu-2/",
        "https://www.hdfilmcehennemi.ws/film-robotu-3/",
        "https://www.hdfilmcehennemi.ws/arsiv/",
        "https://www.hdfilmcehennemi.ws/category/film-izle-2/",
    ]
    
    for url in initial_urls:
        print(f"  Tarıyor: {url}")
        html_content = get_html(url)
        if html_content:
            films = extract_films_from_html(html_content, url)
            new_films = [f for f in films if f['url'] not in seen_urls]
            
            if new_films:
                all_films.extend(new_films)
                for film in new_films:
                    seen_urls.add(film['url'])
                print(f"    {len(new_films)} yeni film eklendi, toplam: {len(all_films)}")
        
        time.sleep(random.uniform(0.5, 1.5))
    
    # 2. Sayfa sayfa tarama
    print("\n2. Sayfa sayfa tarama (1-20)...")
    for page in range(1, 21):
        url = f"https://www.hdfilmcehennemi.ws/sayfa/{page}/"
        print(f"  Sayfa {page}: {url}")
        
        html_content = get_html(url)
        if html_content:
            films = extract_films_from_html(html_content, url)
            new_films = [f for f in films if f['url'] not in seen_urls]
            
            if new_films:
                all_films.extend(new_films)
                for film in new_films:
                    seen_urls.add(film['url'])
                print(f"    {len(new_films)} yeni film eklendi, toplam: {len(all_films)}")
            else:
                print(f"    Yeni film bulunamadı")
        
        time.sleep(random.uniform(0.3, 1.0))
    
    # 3. Kategoriler
    print("\n3. Kategorileri tarama...")
    categories = [
        "aksiyon", "komedi", "dram", "gerilim", "korku",
        "bilim-kurgu", "fantastik", "macera", "romantik",
        "suç", "biyografi", "tarih", "aile", "animasyon",
        "savaş", "western", "gizem", "polisiye", "yerli"
    ]
    
    for category in categories:
        url = f"https://www.hdfilmcehennemi.ws/tur/{category}-filmleri-izle/"
        print(f"  Kategori: {category}")
        
        html_content = get_html(url)
        if html_content:
            films = extract_films_from_html(html_content, url)
            new_films = [f for f in films if f['url'] not in seen_urls]
            
            if new_films:
                all_films.extend(new_films)
                for film in new_films:
                    seen_urls.add(film['url'])
                print(f"    {len(new_films)} yeni film eklendi")
        
        time.sleep(random.uniform(0.5, 1.5))
    
    return all_films

def get_all_embed_urls(films):
    """Tüm filmler için embed URL'leri al"""
    films_with_embeds = []
    total_films = len(films)
    
    print(f"\n{'='*70}")
    print(f"Embed URL'leri çekiliyor ({total_films} film)...")
    print(f"{'='*70}")
    
    for i, film in enumerate(films, 1):
        film_title = film.get('title', 'Bilinmeyen')[:40]
        print(f"  [{i}/{total_films}] {film_title}...")
        
        embed_url = extract_embed_url_from_film_page(film['url'], film.get('token', ''))
        film['embed_url'] = embed_url
        films_with_embeds.append(film)
        
        # Progress her 10 filmde bir göster
        if i % 10 == 0:
            success_count = sum(1 for f in films_with_embeds if f.get('embed_url'))
            print(f"    İlerleme: {i}/{total_films} - Başarılı: {success_count}")
        
        # Rastgele delay (anti-ban)
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)
    
    return films_with_embeds

def save_results(films):
    """Sonuçları kaydet"""
    if not films:
        print("❌ Kaydedilecek film yok!")
        return
    
    # 1. Tam sonuçlar
    try:
        result = {
            'metadata': {
                'scraped_at': datetime.now().isoformat(),
                'total_films': len(films),
                'films_with_embeds': sum(1 for f in films if f.get('embed_url')),
                'source': 'hdfilmcehennemi.ws'
            },
            'films': films
        }
        
        with open('hdfilms_complete_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Tam sonuçlar kaydedildi: hdfilms_complete_fixed.json")
    except Exception as e:
        print(f"❌ Tam sonuçlar kaydedilemedi: {e}")
    
    # 2. GitHub için basit format
    try:
        simple_data = []
        for film in films:
            # Embed URL kontrolü
            embed_url = film.get('embed_url', '')
            if embed_url and 'rapidrame_id=' in embed_url:
                # rapidrame_id'yi çıkar
                match = re.search(r'rapidrame_id=([a-zA-Z0-9]+)', embed_url)
                if match:
                    video_id = match.group(1)
                    # Sizin formatınıza çevir
                    embed_url = f"https://metvmetv33.byethost15.com/hdcehennemi.php?ID={video_id}&video.mp4"
            
            simple_data.append({
                'title': film.get('title', ''),
                'year': film.get('year', ''),
                'type': film.get('type', 'film'),
                'url': film.get('url', ''),
                'embed_url': embed_url,
                'imdb': film.get('imdb', '0.0'),
                'image': film.get('image', ''),
                'token': film.get('token', '')
            })
        
        with open('hdceh_embeds_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(simple_data, f, ensure_ascii=False, indent=2)
        print(f"✅ GitHub için embed dosyası kaydedildi: hdceh_embeds_fixed.json")
    except Exception as e:
        print(f"❌ Embed dosyası kaydedilemedi: {e}")
    
    # 3. CSV formatında da kaydet (isteğe bağlı)
    try:
        import csv
        with open('hdfilms_fixed.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Year', 'IMDB', 'URL', 'Embed URL', 'Has Embed'])
            
            for film in films:
                has_embed = 'EVET' if film.get('embed_url') else 'HAYIR'
                writer.writerow([
                    film.get('title', ''),
                    film.get('year', ''),
                    film.get('imdb', ''),
                    film.get('url', ''),
                    film.get('embed_url', ''),
                    has_embed
                ])
        print(f"✅ CSV dosyası kaydedildi: hdfilms_fixed.csv")
    except Exception as e:
        print(f"⚠️ CSV kaydedilemedi: {e}")

def print_summary(films):
    """Özet bilgi göster"""
    if not films:
        print("❌ Gösterilecek film yok!")
        return
    
    total = len(films)
    with_embeds = sum(1 for f in films if f.get('embed_url'))
    success_rate = (with_embeds / total * 100) if total > 0 else 0
    
    print(f"\n{'='*70}")
    print("SONUÇ ÖZETİ:")
    print(f"{'='*70}")
    print(f"Toplam Film: {total}")
    print(f"Embed URL'si Olan: {with_embeds}")
    print(f"Başarı Oranı: %{success_rate:.1f}")
    
    # IMDB dağılımı
    imdb_counts = {
        '9.0+': sum(1 for f in films if float(f.get('imdb', 0)) >= 9.0),
        '8.0-8.9': sum(1 for f in films if 8.0 <= float(f.get('imdb', 0)) < 9.0),
        '7.0-7.9': sum(1 for f in films if 7.0 <= float(f.get('imdb', 0)) < 8.0),
        '6.0-6.9': sum(1 for f in films if 6.0 <= float(f.get('imdb', 0)) < 7.0),
        '5.0-5.9': sum(1 for f in films if 5.0 <= float(f.get('imdb', 0)) < 6.0),
        '0.0': sum(1 for f in films if f.get('imdb') == '0.0'),
    }
    
    print(f"\nIMDB Dağılımı:")
    for range_name, count in imdb_counts.items():
        if count > 0:
            percentage = (count / total * 100)
            print(f"  {range_name}: {count} film (%{percentage:.1f})")
    
    # En yüksek IMDB'li 5 film
    films_with_rating = [f for f in films if f.get('imdb') != '0.0']
    if films_with_rating:
        films_with_rating.sort(key=lambda x: float(x.get('imdb', 0)), reverse=True)
        print(f"\nEn Yüksek IMDB'li 5 Film:")
        for i, film in enumerate(films_with_rating[:5], 1):
            title = film.get('title', '')[:50]
            has_embed = '✓' if film.get('embed_url') else '✗'
            print(f"  {i}. {title:50} ⭐{film.get('imdb', '0.0')} [embed:{has_embed}]")
    
    # Embed'siz filmler
    films_without_embed = [f for f in films if not f.get('embed_url')]
    if films_without_embed:
        print(f"\nEmbed'siz Filmler (ilk 5):")
        for i, film in enumerate(films_without_embed[:5], 1):
            print(f"  {i}. {film.get('title', '')}")
        
        if len(films_without_embed) > 5:
            print(f"  ... ve {len(films_without_embed) - 5} film daha")
    
    print(f"\n{'='*70}")
    print("İŞLEM TAMAMLANDI!")
    print(f"{'='*70}")

def main():
    """Ana fonksiyon"""
    print("HDFilmCehennemi Scraper - Başlıyor...")
    
    try:
        # 1. Tüm filmleri çek
        all_films = scrape_all_films()
        
        if not all_films:
            print("❌ Hiç film bulunamadı!")
            return
        
        # 2. Benzersiz filmler
        unique_films = []
        seen_titles = set()
        
        for film in all_films:
            title = film.get('title', '').lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_films.append(film)
        
        print(f"\nBenzersiz film sayısı: {len(unique_films)}")
        
        # 3. Tüm filmler için embed URL'leri al
        films_with_embeds = get_all_embed_urls(unique_films)
        
        # 4. Sonuçları kaydet
        save_results(films_with_embeds)
        
        # 5. Özet göster
        print_summary(films_with_embeds)
        
    except KeyboardInterrupt:
        print("\n\n❌ İşlem kullanıcı tarafından durduruldu!")
    except Exception as e:
        print(f"\n\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
