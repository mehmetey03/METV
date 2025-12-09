import sys
import subprocess
import json
import time
from urllib.parse import urljoin

# Eksik kütüphaneleri otomatik yükle
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import requests
except ImportError:
    install("requests")
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    install("beautifulsoup4")
    from bs4 import BeautifulSoup

BASE_URL = "https://www.hdfilmcehennemi.ws"
CATEGORY_URL = f"{BASE_URL}/category/film-izle-2/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
}

def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"[WARN] {url} → {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] {url} → {e}")
    return None

def get_total_pages(html):
    """Sayfa numaralarını bulmak için pagination kontrolü"""
    soup = BeautifulSoup(html, "html.parser")
    pagination = soup.select("ul.page-numbers li a")
    pages = []
    for a in pagination:
        try:
            pages.append(int(a.text))
        except:
            continue
    return max(pages) if pages else 1

def get_film_links_from_page(html):
    """Filmlerin sayfa linklerini al"""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("h2.post-title a"):
        href = a.get("href")
        if href:
            links.append(urljoin(BASE_URL, href))
    return links

def get_embed_url(film_url):
    """Filmin embed linkini sayfa kaynağından al"""
    html = fetch_page(film_url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    # iframe veya video script kontrolleri
    iframe = soup.select_one("iframe")
    if iframe and iframe.get("src"):
        return iframe.get("src")
    # Alternatif script içinde base64 çözümleme
    scripts = soup.find_all("script")
    for script in scripts:
        if "dc_hello" in script.text:
            import re, base64
            m = re.search(r'dc_hello\("([^"]+)"\)', script.text)
            if m:
                encoded = m.group(1)
                try:
                    decoded_once = base64.b64decode(encoded).decode()
                    decoded_twice = base64.b64decode(decoded_once[::-1]).decode()
                    link = decoded_twice.split("+")[-1].strip()
                    return link if link.startswith("http") else f"https{link}"
                except:
                    continue
    return None

def main():
    first_page_html = fetch_page(CATEGORY_URL)
    if not first_page_html:
        print("Başlangıç sayfası alınamadı!")
        return

    total_pages = get_total_pages(first_page_html)
    print(f"Toplam sayfa: {total_pages}")

    all_films = []

    for page in range(1, total_pages + 1):
        print(f"[INFO] Sayfa {page}")
        page_url = f"{CATEGORY_URL}page/{page}/"
        html = fetch_page(page_url)
        if not html:
            continue
        film_links = get_film_links_from_page(html)
        print(f"[INFO] {len(film_links)} film bulundu")
        for film_url in film_links:
            embed_url = get_embed_url(film_url)
            if embed_url:
                all_films.append({"title": film_url.split("/")[-2].replace("-", " ").title(),
                                  "url": film_url,
                                  "embed": embed_url})
            time.sleep(0.2)  # Siteyi yormamak için kısa bekleme

    # JSON kaydet
    with open("hdceh_embeds.json", "w", encoding="utf-8") as f:
        json.dump(all_films, f, ensure_ascii=False, indent=4)

    print(f"[DONE] Toplam {len(all_films)} film kaydedildi → hdceh_embeds.json")

if __name__ == "__main__":
    main()
