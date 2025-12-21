import requests
from bs4 import BeautifulSoup
import json
import time
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------
# DOMAIN BULMA - BASİT VE ETKİLİ
# ------------------------------
def find_active_domain():
    """
    Aktif domain'i bulur (30'dan 50'ye kadar dener)
    """
    print("🔍 Aktif domain aranıyor...")
    
    for i in range(30, 51):  # 30'dan 50'ye kadar
        test_domain = f"https://dizipall{i}.com"
        try:
            print(f"  Testing: {test_domain}")
            response = requests.get(test_domain, timeout=3, 
                                   headers={"User-Agent": "Mozilla/5.0"})
            
            if response.status_code == 200:
                # Basit kontrol: sayfada "film" veya "dizi" kelimesi var mı?
                if "film" in response.text.lower() or "dizi" in response.text.lower():
                    print(f"✓ Aktif domain bulundu: {test_domain}")
                    return test_domain
        except:
            continue
    
    # Hiçbiri çalışmazsa en son bilinen
    print("⚠ Aktif domain bulunamadı, son bilinen kullanılıyor...")
    return "https://dizipall34.com"

# Aktif domain'i bul
BASE = find_active_domain()
print(f"🌐 Kullanılan domain: {BASE}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ------------------------------
# HTML çekme
# ------------------------------
def get_html(url):
    try:
        r = SESSION.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return ""

# ------------------------------
# Embed URL çözme
# ------------------------------
def get_embed_url(detail_url):
    if not detail_url:
        return ""
    html = get_html(detail_url)
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')

    # iframe
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        src = iframe['src']
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = 'https://dizipal.website' + src
        return src

    # data-video-id
    video_div = soup.find(attrs={"data-video-id": True})
    if video_div:
        return f"https://dizipal.website/{video_div['data-video-id']}"

    # fallback
    slug = detail_url.rstrip('/').split('/')[-1]
    return f"https://dizipal.website/{hashlib.md5(slug.encode()).hexdigest()[:13]}"

# ------------------------------
# Film scraping
# ------------------------------
def scrape_page(page=1):
    url = f"{BASE}/filmler" if page == 1 else f"{BASE}/filmler/{page}"
    print(f"→ Sayfa {page} çekiliyor: {url}")
    html = get_html(url)
    if not html:
        print("  ⚠ HTML çekilemedi")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    containers = soup.select('li.w-1\\/2')
    if not containers:
        containers = soup.find_all(class_=lambda x: x and 'w-1/2' in x)
    if not containers:
        print(f"❌ Film kutusu yok → Durdu.")
        return []

    movies = []
    for container in containers:
        try:
            # Başlık
            title_elem = container.find(['h2', 'h3', 'h4'])
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Yıl
            year_elem = container.find(class_=lambda x: x and 'year' in x)
            year = year_elem.get_text(strip=True) if year_elem else ""

            # Tür
            genre_elem = container.find(class_=lambda x: x and 'title' in x)
            genre = genre_elem.get('title', '') if genre_elem else ""

            # Resim
            img = ""
            for img_elem in container.find_all('img'):
                src = img_elem.get('data-src') or img_elem.get('src') or ""
                if 'uploads/movies/original/' in src:
                    if src.startswith('//'):
                        img = 'https:' + src
                    elif src.startswith('/'):
                        img = BASE + src
                    else:
                        img = src
                    break  # ilk uygun resmi bulunca dur

            # Detay URL
            link_elem = container.find('a', href=lambda x: x and '/film/' in x)
            detail_url = ""
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    detail_url = BASE + href
                elif href.startswith('http'):
                    detail_url = href

            movies.append({
                "title": title,
                "year": year,
                "genre": genre,
                "image": img,
                "detail_url": detail_url,
                "embed_url": ""  # Sonra dolduracağız
            })
        except Exception as e:
            print(f"⚠ Film işlenirken hata: {e}")

    return movies

# ------------------------------
# Embed URL'leri paralel al
# ------------------------------
def fill_embed_urls(movies):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_embed_url, m['detail_url']): m for m in movies}
        for future in as_completed(futures):
            movie = futures[future]
            try:
                movie['embed_url'] = future.result(timeout=10)
            except:
                movie['embed_url'] = ""

# ------------------------------
# Maksimum sayfa sayısını otomatik bul
# ------------------------------
def get_max_pages():
    """
    Toplam sayfa sayısını otomatik bulur
    """
    url = f"{BASE}/filmler"
    html = get_html(url)
    if not html:
        print("⚠ Sayfa sayısı bulunamadı, varsayılan 158 kullanılıyor")
        return 158
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Pagination linklerini ara
        max_page = 1
        
        # Tüm linkleri kontrol et
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/filmler/' in href and href != '/filmler/':
                # Sayfa numarasını çıkar
                parts = href.split('/')
                for part in parts:
                    if part.isdigit():
                        page_num = int(part)
                        if page_num > max_page:
                            max_page = page_num
        
        # Pagination class'ını ara
        pagination = soup.find(class_='pagination')
        if pagination:
            for link in pagination.find_all('a'):
                text = link.get_text(strip=True)
                if text.isdigit():
                    page_num = int(text)
                    if page_num > max_page:
                        max_page = page_num
        
        if max_page > 1:
            print(f"📊 Otomatik bulunan sayfa sayısı: {max_page}")
            return max_page
        else:
            print("⚠ Sadece 1 sayfa bulundu")
            return 1
            
    except Exception as e:
        print(f"⚠ Sayfa sayısı bulunurken hata: {e}")
    
    return 158  # varsayılan

# ------------------------------
# Tüm sayfaları çek
# ------------------------------
def scrape_all():
    # Sayfa sayısını otomatik bul
    max_pages = get_max_pages()
    print(f"📚 Toplam {max_pages} sayfa taranacak\n")
    
    all_movies = []
    for page in range(1, max_pages + 1):
        movies = scrape_page(page)
        if not movies:
            print(f"⚠ Sayfa {page}'de film bulunamadı, durduruluyor...")
            break
        
        fill_embed_urls(movies)
        all_movies.extend(movies)
        print(f"✓ Sayfa {page}: {len(movies)} film eklendi (Toplam: {len(all_movies)})")
        
        # Dinamik bekleme
        if page % 10 == 0:
            time.sleep(1)  # Her 10 sayfada bir 1 saniye bekle
        else:
            time.sleep(0.2)
    
    return all_movies

# ------------------------------
# MAIN
# ------------------------------
if __name__ == "__main__":
    print("🎬 DIZIPAL FILM SCRAPER")
    print("=" * 50)
    
    movies = scrape_all()

    # JSON kaydet
    try:
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "film.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(movies, f, indent=2, ensure_ascii=False)
        print(f"\n🎉 Toplam film: {len(movies)}")
        print(f"💾 film.json kaydedildi! ({file_path})")
        
        # İstatistik
        with_embed = sum(1 for movie in movies if movie.get('embed_url'))
        print(f"🔗 Embed URL'si olan filmler: {with_embed}/{len(movies)}")
        
    except Exception as e:
        print(f"❌ film.json kaydedilemedi: {e}")
    
    print("=" * 50)
