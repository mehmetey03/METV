import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import yaml
import os
import sys
import time

main_url = "https://puhutv.com/"
diziler_url = "https://puhutv.com/dizi"
m3u_file = "puhutv.m3u"
yml_file = "puhutv.yml"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

def safe_json_from_next_data(soup):
    """__NEXT_DATA__ içinden JSON çıkarmaya çalış. Başarısızsa None döner."""
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script:
        return None
    try:
        return json.loads(script.string)
    except Exception:
        return None

def get_series_details(series_id):
    """ESKİ API çağrısı hâlâ çalışıyorsa kullan; çalışmazsa basit fallback döner."""
    url = f"https://appservice.puhutv.com/service/serie/getSerieInformations?id={series_id}"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                return data[0]
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {"title": "", "seasons": []}

def build_stream_url_from_video_id(video_id):
    """Mevcut yaklaşım: dygvideo redirect url şablonu. Eğer farklı bilgi varsa burayı değiştir."""
    if not video_id:
        return None
    return f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=29&ReferenceId={video_id}&SecretKey=NtvApiSecret2014*&.m3u8"

def extract_episode_video_id(ep):
    """Episode objesinden video id çıkarmaya çalış (farklı alan isimleri için fallback)."""
    # Olası alan isimleri
    for key in ("videoId", "video_id", "videoID", "id_video"):
        if key in ep and ep[key]:
            return ep[key]
    # Bazı yapılarda 'videos' listesi olabilir
    if isinstance(ep.get("videos"), list) and ep.get("videos"):
        first = ep["videos"][0]
        if isinstance(first, dict):
            for key in ("id", "videoId", "video_id"):
                if key in first and first[key]:
                    return first[key]
    # başka fallback'ler:
    if ep.get("source") and isinstance(ep["source"], dict):
        return ep["source"].get("id") or ep["source"].get("videoId")
    return None

def extract_episode_image(ep, content):
    """Bölüm ya da dizi objesinden uygun resmi al (thumbnail fallback)."""
    # episode seviyesinden dene
    for key in ("image", "img", "images", "poster"):
        if key in ep and ep[key]:
            val = ep[key]
            if isinstance(val, dict):
                # dict içinden thumbnail veya url kontrolü
                for sub in ("thumbnail", "thumb", "url", "src"):
                    if sub in val and val[sub]:
                        return val[sub]
                # rastgele dict -> string değer döndür
                for v in val.values():
                    if isinstance(v, str) and v.startswith("http"):
                        return v
            if isinstance(val, str) and val.startswith("http"):
                return val
    # content (dizi) seviyesinden dene
    if isinstance(content, dict):
        for key in ("image", "img", "poster", "thumbnail"):
            if key in content and content[key]:
                val = content[key]
                if isinstance(val, str) and val.startswith("http"):
                    return val
                if isinstance(val, dict):
                    return val.get("thumbnail") or val.get("url")
    return ""

def get_stream_urls(series_slug_or_url):
    """Dizi sayfasından bütün sezonları ve bölümleri çek; episodes listesi döndür."""
    # series_slug_or_url bazen sadece slug gelebilir; normalize et
    if series_slug_or_url.startswith("http"):
        url = series_slug_or_url
    else:
        url = urljoin(main_url, series_slug_or_url.lstrip("/"))

    try:
        r = session.get(url, timeout=15)
    except Exception as e:
        print(f"[WARN] {url} isteği başarısız: {e}", file=sys.stderr)
        return []

    if r.status_code != 200:
        print(f"[WARN] {url} durum kodu {r.status_code}", file=sys.stderr)
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    data = safe_json_from_next_data(soup)
    if not data:
        print(f"[WARN] __NEXT_DATA__ bulunamadı: {url}", file=sys.stderr)
        return []

    # Olabilecek birkaç farklı yol:
    props = data.get("props", {}) or {}
    pageProps = props.get("pageProps") or props.get("initialProps") or {}
    content = pageProps.get("contentData") or pageProps.get("serie") or pageProps.get("serieData") or pageProps.get("data")

    # Bazı yapılar top-level farklı olabilir; denemeler:
    if not content and "pageProps" in data:
        # daha derin arama
        for k in ("content", "contentData", "serie", "serieData"):
            if pageProps.get(k):
                content = pageProps.get(k)
                break

    if not content:
        print(f"[WARN] contentData/serie bulunamadı: {url}", file=sys.stderr)
        return []

    episodes = []

    # Eğer content doğrudan 'seasons' içeriyorsa:
    seasons = content.get("seasons") or []
    if not seasons and content.get("season"):
        # tek sezon yapılı ise
        seasons = [content.get("season")]

    # Eğer seasons boşsa, bazı sayfalarda doğrudan 'episodes' listesi olabilir
    if not seasons and content.get("episodes"):
        seasons = [{"name": "", "episodes": content.get("episodes")}]

    for season in seasons:
        season_name = season.get("name") or season.get("title") or ""
        eps = season.get("episodes") or season.get("items") or []
        for ep in eps:
            # ep bir dict olmalı
            if not isinstance(ep, dict):
                continue

            ep_id = ep.get("id") or ep.get("episodeId") or ep.get("episode_id")
            ep_name = ep.get("name") or ep.get("title") or f"Episode {ep_id or 'unknown'}"
            # link slug veya tam url
            ep_slug = ep.get("slug") or ep.get("url") or ep.get("link") or ""
            ep_url = urljoin(main_url, ep_slug) if ep_slug and not ep_slug.startswith("http") else (ep_slug or "")
            ep_img = extract_episode_image(ep, content)
            video_id = extract_episode_video_id(ep)

            stream_url = build_stream_url_from_video_id(video_id) if video_id else None

            # Eğer stream_url yoksa atla (veya alternatif yöntemler eklenebilir)
            if not stream_url:
                # Fallback: bazı yapılarda 'playback' ya da 'playlist' alanı olabilir
                if ep.get("playback") and isinstance(ep["playback"], str):
                    stream_url = ep["playback"]
                elif ep.get("playlist") and isinstance(ep["playlist"], str):
                    stream_url = ep["playlist"]
                else:
                    # atla
                    continue

            full_name = f"{content.get('name') or content.get('title') or ''} {season_name} {ep_name}".strip()

            episodes.append({
                "id": ep_id,
                "name": ep_name,
                "img": ep_img,
                "url": ep_url,
                "stream_url": stream_url,
                "season": season_name,
                "full_name": full_name
            })

    return episodes

def get_all_content():
    """Diziler listesini çek ve her dizi için bölümleri al."""
    try:
        r = session.get(diziler_url, timeout=15)
    except Exception as e:
        print(f"[ERROR] {diziler_url} isteği başarısız: {e}", file=sys.stderr)
        return []

    if r.status_code != 200:
        print(f"[ERROR] {diziler_url} durum kodu {r.status_code}", file=sys.stderr)
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    data = safe_json_from_next_data(soup)
    container_items = []

    if data:
        # Orijinal sayfada container_items şu yolda bulunuyordu:
        # data["props"]["pageProps"]["data"]["data"]["container_items"]
        pageProps = data.get("props", {}).get("pageProps", {}) or {}
        # Try multiple possible paths:
        c1 = pageProps.get("data", {}) or {}
        if isinstance(c1, dict) and c1.get("data") and isinstance(c1["data"], dict):
            container_items = c1["data"].get("container_items", [])
        if not container_items:
            # direkt pageProps içinde olabilir
            container_items = pageProps.get("container_items") or pageProps.get("containerItems") or []
        # bazı sayfalarda props.pageProps.contentData içinde katalog olabilir
        if not container_items and pageProps.get("contentData"):
            contentData = pageProps.get("contentData")
            if isinstance(contentData, dict) and contentData.get("catalog"):
                container_items = contentData["catalog"].get("container_items", []) or contentData["catalog"].get("items", [])
    else:
        print("[WARN] Browse sayfasında __NEXT_DATA__ yok; alternatif scraping atlanıyor.", file=sys.stderr)

    # Fallback: eğer container_items boşsa, basit bir HTML select/anchors taraması yap
    series_list = []
    if container_items:
        for item in container_items:
            for content in item.get("items", []) if isinstance(item.get("items", []), list) else []:
                series_list.append(content)
    else:
        # Basit HTML linkleri topla (en basit fallback)
        anchors = soup.select("a[href*='/dizi/'], a[href*='/series/'], a[href*='/program/']")
        seen = set()
        for a in anchors:
            href = a.get("href")
            name = a.get_text(strip=True) or a.get("title") or ""
            if not href:
                continue
            slug = href
            if slug in seen:
                continue
            seen.add(slug)
            series_list.append({
                "id": None,
                "name": name,
                "meta": {"slug": slug},
                "image": a.find("img")["src"] if a.find("img") and a.find("img").get("src") else ""
            })

    all_series = []
    for series in tqdm(series_list, desc="Processing Series"):
        series_id = series.get("id")
        series_name = series.get("name") or series.get("title") or ""
        series_slug = series.get("meta", {}).get("slug") or series.get("slug") or series.get("url") or ""
        series_img = series.get("image") or series.get("img") or ""

        # Normalize slug -> tam path
        if series_slug and not series_slug.startswith("http"):
            series_slug = urljoin(main_url, series_slug.lstrip("/"))

        # Eğer id varsa eski API çağrısıyla seasons al, yoksa doğrudan sayfadan al
        series_details = get_series_details(series_id) if series_id else {}
        # get_stream_urls fonksiyonu artık series sayfasından sezon+bölüm alıyor
        episodes = []
        try:
            episodes = get_stream_urls(series_slug or series.get("meta", {}).get("slug") or "")
        except Exception as e:
            print(f"[WARN] Bölümler alınırken hata: {e}", file=sys.stderr)

        temp_series = {
            "name": series_name,
            "img": series_img,
            "url": series_slug,
            "episodes": episodes
        }

        # sadece bölümü olanları ekle
        if episodes:
            all_series.append(temp_series)

        # kısa gecikme, web sunucusuna yüklenmeyi azaltmak için
        time.sleep(0.2)

    return all_series

def create_m3u_file(data):
    total_eps = sum(len(s["episodes"]) for s in data)
    if total_eps == 0:
        print(f"[INFO] Hiç bölüm bulunamadı — {m3u_file} oluşturulmadı.")
        return

    with open(m3u_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for series in data:
            for ep in series["episodes"]:
                # yalnızca geçerli stream_url olanları yaz
                if not ep.get("stream_url"):
                    continue
                # güvenli string'ler
                tvg_logo = ep.get("img", "")
                full_name = ep.get("full_name") or f"{series.get('name','')} {ep.get('season','')} {ep.get('name','')}".strip()
                # EXTINF satırını Türkçe ve düzenli yap
                info = f'#EXTINF:-1 tvg-id="vod.tr" tvg-name="TR: {full_name}" tvg-logo="{tvg_logo}" group-title="PUHUTV DİZİLER",TR: {full_name}\n'
                f.write(info)
                f.write(f"{ep['stream_url']}\n")
    print(f"{m3u_file} başarıyla güncellendi! Toplam bölüm: {total_eps}")

def create_yaml_file(data):
    if os.path.exists(yml_file):
        print(f"{yml_file} zaten mevcut, oluşturulmadı.")
        return
    try:
        with open(yml_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"{yml_file} başarıyla oluşturuldu!")
    except Exception as e:
        print(f"[ERROR] YAML yazılırken hata: {e}", file=sys.stderr)

def main():
    print("PuhuTV scraping başlıyor...")
    data = get_all_content()
    if not data:
        print("[WARN] Veri bulunamadı veya hata oluştu. Script sonlanıyor.")
        return
    create_m3u_file(data)
    create_yaml_file(data)
    # debug info: kaç dizi ve kaç bölüm
    series_count = len(data)
    eps_count = sum(len(s["episodes"]) for s in data)
    print(f"[DONE] Diziler: {series_count}, Bölümler: {eps_count}")

if __name__ == "__main__":
    main()
