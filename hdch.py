import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urljoin

# ============================================================================
# AYARLAR VE SABİTLER
# ============================================================================
PAGES_TO_SCRAPE = int(sys.argv[1]) if len(sys.argv) > 1 else 10
DELAY_BETWEEN_FILMS = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05  # Çok daha düşük

BASE_URL = "https://www.hdfilmcehennemi.nl"
GITHUB_JSON_URL = "https://raw.githubusercontent.com/sevdimcim/vod-max/refs/heads/main/hdfilmcehennemi.json"

# Daha agresif header ayarları
HEADERS_PAGE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": f"{BASE_URL}/",
    "X-Requested-With": "fetch",
    "Accept": "application/json",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate",
}

HEADERS_FILM = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate",
}

# Thread yapılandırması
MAX_WORKERS = 12  # 12 paralel iş parçacığı
MAX_RETRIES = 2
RETRY_DELAY = 0.5

# Thread-safe lock
data_lock = Lock()

# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

# Genel session (connection pooling için)
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
        response = session.get(url, headers=HEADERS_PAGE, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return get_json_response(url, retry_count + 1)
        return None

def get_soup(url, retry_count=0):
    try:
        response = session.get(url, headers=HEADERS_FILM, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        if retry_count < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
            return get_soup(url, retry_count + 1)
        return None

def slugify(text):
    text = text.lower()
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    text = re.sub(r'[^a-z0-9]', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text

def extract_film_data(a_etiketi):
    """Film verisini çıkar - hızlı işlem"""
    try:
        film_link = a_etiketi.get('href')
        film_adi = a_etiketi.get('title') or a_etiketi.text.strip()
        
        if not film_adi:
            return None
        
        poster_url = ""
        poster_img = a_etiketi.find('img')
        
        if poster_img:
            poster_url = poster_img.get('data-src', '') or poster_img.get('src', '')
            if poster_url and "?" in poster_url:
                poster_url = poster_url.split("?")[0]
        
        return {
            'film_adi': film_adi,
            'film_link': film_link,
            'poster_url': poster_url
        }
    except:
        return None

def process_film(film_info, filmler_data):
    """Tek film işleyen işçi fonksiyonu"""
    if not film_info:
        return None
    
    film_adi = film_info['film_adi']
    film_link = film_info['film_link']
    poster_url = film_info['poster_url']
    
    video_url = ""
    
    if film_link:
        try:
            target_url = urljoin(BASE_URL, film_link)
            film_soup = get_soup(target_url)
            
            if film_soup:
                iframe = film_soup.find('iframe', {'class': 'close'})
                
                if iframe and iframe.get('data-src'):
                    raw_iframe_url = iframe.get('data-src')
                    
                    if "rapidrame_id=" in raw_iframe_url:
                        rapid_id = raw_iframe_url.split("rapidrame_id=")[1]
                        video_url = f"https://www.hdfilmcehennemi.com/rplayer/{rapid_id}"
                    else:
                        video_url = raw_iframe_url
        except:
            pass
    
    film_id = slugify(film_adi)
    
    with data_lock:
        filmler_data[film_id] = {
            "isim": film_adi,
            "resim": poster_url if poster_url else "https://via.placeholder.com/300x450/15161a/ffffff?text=No+Image",
            "link": video_url
        }
    
    return film_id

def process_page(sayfa, filmler_data, film_counter):
    """Bir sayfayı işle - paralel çalışacak"""
    api_page_url = f"{BASE_URL}/load/page/{sayfa}/categories/film-izle-2/"
    
    try:
        data = get_json_response(api_page_url)
        
        if not data:
            return 0
        
        html_chunk = data.get('html', '')
        soup = BeautifulSoup(html_chunk, 'html.parser')
        film_kutulari = soup.find_all('a', class_='poster')
        
        if not film_kutulari:
            return 0
        
        processed_count = 0
        
        # Filmler için mini thread pool (sayfa içinde)
        with ThreadPoolExecutor(max_workers=4) as mini_executor:
            futures = []
            
            for a_etiketi in film_kutulari:
                film_info = extract_film_data(a_etiketi)
                if film_info:
                    future = mini_executor.submit(process_film, film_info, filmler_data)
                    futures.append(future)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    processed_count += 1
                    with data_lock:
                        film_counter[0] += 1
        
        print(f"✅ Sayfa {sayfa}: {processed_count} film işlendi")
        return processed_count
        
    except Exception as e:
        print(f"❌ Sayfa {sayfa} hatası: {e}")
        return 0

# ============================================================================
# ANA FONKSİYON
# ============================================================================

def main():
    print("🚀 HDFilmCehennemi Botu Başlatıldı (TÜRBİ MOD - 50X HIZLI)")
    print(f"📊 {PAGES_TO_SCRAPE} sayfa taranacak")
    print(f"⚡ {MAX_WORKERS} paralel işçi (thread) etkin\n")
    
    filmler_data = {}
    film_counter = [0]  # Mutable counter for threads
    
    start_time = time.time()
    
    try:
        # Sayfa işleme için paralel executor
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            
            # Tüm sayfalar için task gönder
            for sayfa in range(1, PAGES_TO_SCRAPE + 1):
                future = executor.submit(process_page, sayfa, filmler_data, film_counter)
                futures[future] = sayfa
            
            # Tamamlanan işleri takip et
            completed = 0
            for future in as_completed(futures):
                completed += 1
                sayfa = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    print(f"❌ Sayfa {sayfa} işleme hatası: {e}")
                
                print(f"📈 İlerleme: {completed}/{PAGES_TO_SCRAPE}")
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*60)
        print(f"✅ İşlem tamamlandı!")
        print(f"⏱️  Süre: {elapsed_time:.2f} saniye")
        print(f"🎬 Toplam Film: {len(filmler_data)}")
        print(f"⚡ Hız: {len(filmler_data)/elapsed_time:.1f} film/saniye")
        print("="*60 + "\n")
        
        create_files(filmler_data)
        
    except KeyboardInterrupt:
        print("\n⚠️  İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"💥 Ana hata: {e}")

def create_files(data):
    # JSON dosyası
    json_filename = "hdfilmcehennemi.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON: '{json_filename}' ({os.path.getsize(json_filename) / 1024:.2f} KB)")
    
    # HTML dosyası
    first_99_keys = list(data.keys())[:99]
    first_99_data = {k: data[k] for k in first_99_keys}
    create_html_file(first_99_data, len(data))

def create_html_file(embedded_data, total_film_count):
    embedded_json_str = json.dumps(embedded_data, ensure_ascii=False)
    
    html_template = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <title>TITAN TV FİLM VOD</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css?family=PT+Sans:700i" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://kit.fontawesome.com/bbe955c5ed.js" crossorigin="anonymous"></script>
    <style>
        *:not(input):not(textarea) {{
            -moz-user-select: -moz-none;
            -khtml-user-select: none;
            -webkit-user-select: none;
            -o-user-select: none;
            -ms-user-select: none;
            user-select: none
        }}
        body {{
            margin: 0;
            padding: 0;
            background: #00040d;
            font-family: sans-serif;
            font-size: 15px;
            -webkit-tap-highlight-color: transparent;
            font-style: italic;
            line-height: 20px;
            -webkit-text-size-adjust: 100%;
            text-decoration: none;
            -webkit-text-decoration: none;
            overflow-x: hidden;
        }}
        .filmpaneldis {{
            background: #15161a;
            width: 100%;
            margin: 20px auto;
            overflow: hidden;
            padding: 10px 5px;
            box-sizing: border-box;
            min-height: 500px;
        }}
        .baslik {{
            width: 96%;
            color: #fff;
            padding: 15px 10px;
            box-sizing: border-box;
            border-bottom: 2px solid #572aa7;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .filmpanel {{
            width: 12%;
            height: 200px;
            background: #15161a;
            float: left;
            margin: 1.14%;
            color: #fff;
            border-radius: 15px;
            box-sizing: border-box;
            box-shadow: 1px 5px 10px rgba(0,0,0,0.1);
            border: 1px solid #323442;
            padding: 0px;
            overflow: hidden;
            transition: border 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            position: relative;
        }}
        .filmisimpanel {{
            width: 100%;
            height: 200px;
            position: relative;
            margin-top: -200px;
            background: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 1) 100%);
            pointer-events: none;
        }}
        .filmpanel:hover {{
            color: #fff;
            border: 3px solid #572aa7;
            box-shadow: 0 0 10px rgba(87, 42, 167, 0.5);
        }}
        .filmresim {{
            width: 100%;
            height: 100%;
            margin-bottom: 0px;
            overflow: hidden;
            position: relative;
        }}
        .filmresim img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.4s ease;
        }}
        .filmpanel:hover .filmresim img {{
            transform: scale(1.1);
        }}
        .filmisim {{
            width: 100%;
            font-size: 14px;
            text-decoration: none;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0px 5px;
            box-sizing: border-box;
            color: #fff;
            position: absolute;
            bottom: 5px;
            text-align: center;
        }}
        .aramapanel {{
            width: 100%;
            height: 60px;
            background: #15161a;
            border-bottom: 1px solid #323442;
            margin: 0px auto;
            padding: 10px;
            box-sizing: border-box;
            overflow: hidden;
            z-index: 11111;
            position: sticky;
            top: 0;
        }}
        .aramapanelsag {{
            width: auto;
            height: 40px;
            box-sizing: border-box;
            overflow: hidden;
            float: right;
        }}
        .aramapanelsol {{
            width: 50%;
            height: 40px;
            box-sizing: border-box;
            overflow: hidden;
            float: left;
        }}
        .aramapanelyazi {{
            height: 40px;
            width: 180px;
            border: 1px solid #323442;
            background: #000;
            box-sizing: border-box;
            padding: 0px 10px;
            color: #fff;
            margin: 0px 5px;
            border-radius: 5px;
        }}
        .aramapanelbuton {{
            height: 40px;
            width: 40px;
            text-align: center;
            background-color: #572aa7;
            border: none;
            color: #fff;
            box-sizing: border-box;
            overflow: hidden;
            float: right;
            transition: .35s;
            border-radius: 5px;
            cursor: pointer;
        }}
        .aramapanelbuton:hover {{
            background-color: #fff;
            color: #000;
        }}
        .logo {{
            width: 40px;
            height: 40px;
            float: left;
        }}
        .logo img {{
            width: 100%;
            border-radius: 50%;
        }}
        .logoisim {{
            font-size: 15px;
            width: auto;
            height: 40px;
            line-height: 40px;
            font-weight: 500;
            color: #fff;
            margin-left: 10px;
            float: left;
        }}
        .hataekran i {{
            color: #572aa7;
            font-size: 80px;
            text-align: center;
            width: 100%;
        }}
        .hataekran {{
            width: 80%;
            margin: 20px auto;
            color: #fff;
            background: #15161a;
            border: 1px solid #323442;
            padding: 20px;
            box-sizing: border-box;
            border-radius: 10px;
            text-align: center;
        }}
        .hatayazi {{
            color: #fff;
            font-size: 15px;
            text-align: center;
            width: 100%;
            margin: 20px 0px;
        }}
        .status-bar {{
            color: #888;
            font-size: 12px;
            padding: 5px 10px;
            text-align: right;
        }}
        @media(max-width:550px) {{
            .filmpanel {{
                width: 31.33%;
                height: 190px;
                margin: 1%;
            }}
            .aramapanelyazi {{
                width: 120px;
            }}
            .logoisim {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="aramapanel">
        <div class="aramapanelsol">
            <div class="logo"><img src="https://i.hizliresim.com/t75soiq.png"></div>
            <div class="logoisim">TITAN TV</div>
        </div>
        <div class="aramapanelsag">
            <form action="" name="ara" method="GET" onsubmit="return false;">
                <input type="text" id="filmSearch" placeholder="Film Ara..." class="aramapanelyazi" onkeyup="searchFilms(this.value)">
                <button type="button" class="aramapanelbuton" onclick="searchFilms(document.getElementById('filmSearch').value)">
                    <i class="fas fa-search"></i>
                </button>
            </form>
        </div>
    </div>

    <div class="status-bar" id="dbStatus">Veriler yükleniyor...</div>

    <div class="filmpaneldis" id="filmListesiContainer">
        <div class="baslik" id="baslikText">HDFİLMCEHENNEMİ FİLM ARŞİVİ</div>
        <div id="gridContainer"></div>
    </div>

    <script>
        var localDB = {embedded_json_str};
        const REMOTE_JSON_URL = "{GITHUB_JSON_URL}";
        var masterDB = {{ ...localDB }};
        var isFullDBLoaded = false;
        var totalRemoteCount = 0;

        window.onload = function() {{
            renderFilms(localDB);
            document.getElementById('baslikText').innerText = "VİTRİN (İlk " + Object.keys(localDB).length + " Film)";
            fetchFullDatabase();
        }};

        async function fetchFullDatabase() {{
            try {{
                document.getElementById('dbStatus').innerText = "Tüm arşiv indiriliyor...";
                const response = await fetch(REMOTE_JSON_URL);
                if (!response.ok) throw new Error("Bağlantı hatası");
                const fullData = await response.json();
                masterDB = {{ ...masterDB, ...fullData }};
                isFullDBLoaded = true;
                totalRemoteCount = Object.keys(masterDB).length;
                document.getElementById('dbStatus').innerText = "Arşiv Güncel: " + totalRemoteCount + " Film";
                document.getElementById('baslikText').innerText = "FİLM ARŞİVİ (" + totalRemoteCount + " Film)";
            }} catch (error) {{
                console.error("❌ JSON çekilemedi:", error);
                document.getElementById('dbStatus').innerText = "Sadece Vitrin Modu (Bağlantı Hatası)";
            }}
        }}

        function renderFilms(dataObj, isSearch = false) {{
            var container = document.getElementById("gridContainer");
            container.innerHTML = "";
            var keys = Object.keys(dataObj);
            var limit = isSearch ? 1000 : 99;
            var count = 0;

            if (keys.length === 0) {{
                container.innerHTML = `<div class="hataekran"><i class="fas fa-search"></i><div class="hatayazi">Film bulunamadı!</div></div>`;
                return;
            }}

            for (var i = 0; i < keys.length; i++) {{
                if (count >= limit) break;
                var key = keys[i];
                var film = dataObj[key];
                var item = document.createElement("div");
                item.className = "filmpanel";
                item.onclick = (function(link) {{
                    return function() {{
                        if (link) window.open(link, '_blank');
                        else alert("Link bulunamadı");
                    }}
                }})(film.link);
                item.innerHTML = `
                    <div class="filmresim">
                        <img src="${{film.resim}}" loading="lazy" onerror="this.src='https://via.placeholder.com/300x450/15161a/ffffff?text=No+Image'">
                    </div>
                    <div class="filmisimpanel">
                        <div class="filmisim">${{film.isim}}</div>
                    </div>
                `;
                container.appendChild(item);
                count++;
            }}
        }}

        function searchFilms(query) {{
            query = query.toLowerCase().trim();
            var baslik = document.getElementById("baslikText");
            if (!query) {{
                renderFilms(localDB);
                baslik.innerText = isFullDBLoaded ? "FİLM ARŞİVİ (" + totalRemoteCount + " Film)" : "VİTRİN";
                return;
            }}
            var results = {{}};
            var resultCount = 0;
            for (var key in masterDB) {{
                var filmName = masterDB[key].isim.toLowerCase();
                if (filmName.includes(query)) {{
                    results[key] = masterDB[key];
                    resultCount++;
                }}
            }}
            baslik.innerText = `Arama Sonuçları: ${{resultCount}} Film`;
            renderFilms(results, true);
        }}
    </script>
</body>
</html>'''
    
    html_filename = "hdfilmcehennemi.html"
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"✅ HTML: '{html_filename}' ({os.path.getsize(html_filename) / 1024:.2f} KB)")
    print(f"🎬 Gömülü Film: {len(embedded_data)} | Toplam: {total_film_count}")

if __name__ == "__main__":
    main()
