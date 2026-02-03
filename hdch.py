import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ============================================================================
# AYARLAR VE SABİTLER
# ============================================================================
PAGES_TO_SCRAPE = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DELAY_BETWEEN_FILMS = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05  # Çok hızlı

BASE_URL = "https://www.hdfilmcehennemi.nl"
GITHUB_JSON_URL = "https://raw.githubusercontent.com/mehmetey03/METV/refs/heads/main/hdceh_list.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Connection": "keep-alive",
}

# Thread yapılandırması
MAX_WORKERS = 12
MAX_RETRIES = 2
RETRY_DELAY = 0.5

# Thread-safe lock
data_lock = Lock()

# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=MAX_WORKERS,
    pool_maxsize=MAX_WORKERS,
    max_retries=0
)
session.mount('http://', adapter)
session.mount('https://', adapter)

def get_json_response(url, retry_count=0):
    try:
        resp = session.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return get_json_response(url, retry_count + 1)
        return None

def slugify(text):
    text = text.lower()
    text = text.replace('ı','i').replace('ğ','g').replace('ü','u').replace('ş','s').replace('ö','o').replace('ç','c')
    text = re.sub(r'[^a-z0-9]', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text

def process_page(page_num, filmler_data, film_counter):
    api_url = f"{BASE_URL}/ajax/movies?page={page_num}"
    data = get_json_response(api_url)
    if not data or 'movies' not in data:
        print(f"❌ Sayfa {page_num} boş veya hatalı")
        return 0

    processed_count = 0
    for film in data['movies']:
        film_id = slugify(film['title'])
        with data_lock:
            filmler_data[film_id] = {
                "isim": film['title'],
                "resim": film.get('poster', ''),
                "link": film.get('link', '')
            }
            film_counter[0] += 1
            processed_count += 1

    print(f"✅ Sayfa {page_num}: {processed_count} film işlendi")
    return processed_count

# ============================================================================
# ANA FONKSİYON
# ============================================================================
def main():
    print("🚀 HDFilmCehennemi Botu Başlatıldı (Liste API ile)")
    print(f"📊 {PAGES_TO_SCRAPE} sayfa taranacak")
    print(f"⚡ {MAX_WORKERS} paralel işçi (thread) etkin\n")

    filmler_data = {}
    film_counter = [0]

    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(process_page, p, filmler_data, film_counter): p for p in range(1, PAGES_TO_SCRAPE+1)}
            for future in as_completed(futures):
                _ = future.result()
                print(f"📈 İlerleme: {film_counter[0]} film toplandı")

        elapsed = time.time() - start_time
        print("\n" + "="*60)
        print(f"✅ İşlem tamamlandı!")
        print(f"⏱️  Süre: {elapsed:.2f} saniye")
        print(f"🎬 Toplam Film: {len(filmler_data)}")
        print(f"⚡ Hız: {len(filmler_data)/elapsed:.1f} film/saniye")
        print("="*60 + "\n")

        create_files(filmler_data)

    except KeyboardInterrupt:
        print("\n⚠️ İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"💥 Ana hata: {e}")

# ============================================================================
# JSON ve HTML Dosyaları
# ============================================================================
def create_files(data):
    json_filename = "hdceh_list.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON: '{json_filename}' ({os.path.getsize(json_filename)/1024:.2f} KB)")

    first_99_keys = list(data.keys())[:99]
    first_99_data = {k:data[k] for k in first_99_keys}
    create_html_file(first_99_data, len(data))

def create_html_file(embedded_data, total_count):
    embedded_json_str = json.dumps(embedded_data, ensure_ascii=False)
    html_template = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>HDFilmCehennemi</title>
<style>
body {{ background:#000; color:#fff; font-family:sans-serif; }}
.filmpanel{{width:12%;float:left;margin:1%;border:1px solid #333;padding:5px;cursor:pointer;}}
.filmpanel img{{width:100%;}}
</style>
</head>
<body>
<h1>HDFilmCehennemi - Toplam {total_count} Film</h1>
<div id="films">
<script>
var films = {embedded_json_str};
for(var k in films){{
  var f = films[k];
  document.write('<div class="filmpanel" onclick="window.open(\\''+f.link+'\\',\\'_blank\\')"><img src="'+f.resim+'" alt="'+f.isim+'"><div>'+f.isim+'</div></div>');
}}
</script>
</div>
</body>
</html>
"""
    html_filename = "hdfilmcehennemi.html"
    with open(html_filename,"w",encoding="utf-8") as f:
        f.write(html_template)
    print(f"✅ HTML: '{html_filename}' ({os.path.getsize(html_filename)/1024:.2f} KB)")

# ============================================================================
if __name__ == "__main__":
    main()
