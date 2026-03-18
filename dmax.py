import os
import re
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PLAYLIST_FILE = "dmax.m3u"
LOG_FILE = "progress.log"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/91.0.4472.124 Safari/537.36"
}

# Session + Retry ayarı
session = requests.Session()
retries = Retry(
    total=5,                # En fazla 5 tekrar
    backoff_factor=1,       # 1, 2, 4, 8 sn bekleme
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

def curl_get(url):
    """Sağlamlaştırılmış GET isteği"""
    try:
        resp = session.get(url, headers=HEADERS, verify=False, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Hata: {e}", flush=True)
        return ""

def write_log(message):
    print(message, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def get_series_list():
    url = "https://www.dmax.com.tr/kesfet?size=80"
    html = curl_get(url)
    series = []
    seen = set()

    matches = re.findall(
        r'<div class="poster">.*?<a.*?href="(https://www\.dmax\.com\.tr/[a-z0-9-]+)".*?<img src="(https://img-tlctv1\.mncdn\.com/.*?)" alt=""',
        html, re.S
    )

    for series_url, logo in matches:
        if series_url not in seen:
            seen.add(series_url)
            series.append({
                "url": series_url,
                "logo": logo,
                "name": os.path.basename(series_url)
            })
    return series

def get_season_count(url):
    html = curl_get(url)
    seasons = re.findall(r'<option value="(\d+)">', html)
    return list(reversed(seasons)) if seasons else []

def get_episodes(base_url, season, series_name, logo):
    m3u8_lines = []
    for episode in range(1, 101):
        episode_url = f"{base_url}/{season}-sezon-{episode}-bolum"
        html = curl_get(episode_url)

        if not html or "video-player vod-player" not in html:
            break

        code_match = re.search(r'data-video-code="(.*?)"', html)
        if code_match:
            code = code_match.group(1)
            m3u8 = f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=27&ReferenceId={code}&SecretKey=NtvApiSecret2014*&.m3u8"

            m3u8_line = (
                f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {series_name} {season} Sezon {episode} Bölüm" '
                f'tvg-logo="{logo}" group-title="DMAX BELGESELLER",TR: {series_name} {season} Sezon {episode} Bölüm\n'
                f'{m3u8}\n'
            )

            m3u8_lines.append(m3u8_line)
            print(f"[{series_name} S{season}E{episode}] {m3u8}", flush=True)

    return m3u8_lines

def process_series(series):
    base_url = series["url"].rstrip("/")
    main_html = curl_get(base_url)

    title_match = re.search(r"<title>(.*?)</title>", main_html)
    series_name = title_match.group(1).replace(" | DMAX", "") if title_match else os.path.basename(base_url)

    write_log(f"{series_name} çekiliyor...")

    m3u8_lines = []
    seasons = get_season_count(base_url)

    for season in seasons:
        m3u8_lines.extend(get_episodes(base_url, season, series_name, series["logo"]))

    write_log(f"{series_name} tamamlandı, {len(m3u8_lines)} bölüm bulundu.")
    return m3u8_lines

def main():
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

    series_list = get_series_list()
    write_log(f"Toplam {len(series_list)} dizi bulundu.")

    all_lines = ["#EXTM3U\n"]

    # Çoklu iş parçacığı ile hızlandır
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_series, series) for series in series_list]
        for future in as_completed(futures):
            all_lines.extend(future.result())

    # Tüm içerik en sonda dosyaya yaz
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.writelines(all_lines)

    write_log("Tüm diziler işlendi!")

if __name__ == "__main__":
    main()
