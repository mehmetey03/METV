import requests
import yaml
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = "https://puhutv.com"
API_URL = "https://puhutv.com/api/assets/{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ---------------------------------------------------
# Güvenli İstek Fonksiyonu (Script ASLA Durmasın)
# ---------------------------------------------------
def safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.text
        return None
    except:
        return None

# ---------------------------------------------------
# API JSON Çekme (Hatalı İçerik Scripti Durduramaz)
# ---------------------------------------------------
def safe_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        return r.json()
    except:
        return None

# ---------------------------------------------------
# Tüm içerikleri listele
# ---------------------------------------------------
def get_all_series():
    html = safe_get(BASE_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href*='-detay']")

    result = []
    for a in links:
        href = a.get("href")
        if href and "-detay" in href:
            result.append(BASE_URL + href)

    return list(set(result))


# ---------------------------------------------------
# Serie içeriğini al
# ---------------------------------------------------
def fetch_series(url):
    html = safe_get(url)
    if not html:
        print(f"[WARN] Sayfa açılamadı: {url}")
        return None

    # asset ID yakalama
    try:
        asset_id = html.split('"assetId":')[1].split(",")[0].strip()
    except:
        print(f"[WARN] assetId alınamadı: {url}")
        return None

    json_data = safe_json(API_URL.format(asset_id))

    if not json_data or "contentData" not in json_data:
        print(f"[WARN] contentData bulunamadı: {url}")
        return None

    # contentData içinde "serie" olmayabilir → Atla!
    serie = json_data["contentData"].get("serie")
    if not serie:
        print(f"[WARN] contentData/serie bulunamadı: {url}")
        return None

    episodes = serie.get("episodes", [])
    if not episodes:
        print(f"[WARN] bölüm verisi yok: {url}")
        return None

    final_items = []

    for ep in episodes:
        try:
            title = ep.get("title", "Bilinmiyor")
            playback = ep["playback"]["url"]
            final_items.append({
                "title": title,
                "url": playback
            })
        except:
            continue

    return final_items


# ---------------------------------------------------
# YAML ve M3U oluştur
# ---------------------------------------------------
def save_outputs(data):
    # YAML Kaydet
    with open("puhutv.yml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    # M3U Kaydet
    with open("puhutv.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in data:
            f.write(f'#EXTINF:-1,{ch["title"]}\n')
            f.write(ch["url"] + "\n")

    print("\n✅ puhutv.yml ve puhutv.m3u başarıyla oluşturuldu!\n")


# ---------------------------------------------------
# ANA PROGRAM
# ---------------------------------------------------
def main():
    print("🔍 Tüm diziler alınıyor...")
    series_list = get_all_series()

    if not series_list:
        print("[FATAL] Hiç içerik listelenemedi!")
        return

    print(f"📌 Toplam {len(series_list)} içerik bulundu.\n")

    all_items = []

    for url in tqdm(series_list, desc="Processing Series"):
        data = fetch_series(url)
        if data:
            all_items.extend(data)
        # hata olsa bile script devam eder
        time.sleep(0.3)

    if not all_items:
        print("[WARN] Hiç veri işlenemedi ama dosyalar YİNE DE oluşturulacak!")
        save_outputs([])
        return

    save_outputs(all_items)


# ---------------------------------------------------
if __name__ == "__main__":
    main()
