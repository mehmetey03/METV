import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Siteye özel ayarlar
TARGET_SITE = "https://63betorspintv.live"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE + "/"
}

# Yasaklı (sahte) reklam domainleri
BANNED_DOMAINS = ["gstatic", "jsdelivr", "google", "doubleclick", "analytics", "facebook", "twitter"]

def resolve_base_url(channel_id):
    """Kanal sayfasından gerçek yayın sunucusunu (base_url) çözer."""
    target = f"{TARGET_SITE}/channel?id={channel_id}"
    try:
        r = requests.get(target, headers=HEADERS, timeout=10, verify=False)
        # m3u8 linklerini bul
        urls = re.findall(r'["\'](https?://[^\s"\']+?/)[\w\-]+\.m3u8', r.text)
        for link in urls:
            if not any(banned in link for banned in BANNED_DOMAINS):
                return link
        # Alternatif geniş arama
        alt_urls = re.findall(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|me|net|com|pw|site|club)/)', r.text)
        for link in alt_urls:
            if not any(banned in link for banned in BANNED_DOMAINS):
                return link
    except: pass
    return None

def main():
    try:
        print(f"📡 {TARGET_SITE} taranıyor...")
        
        # 1. Yayın sunucusunu bul (beIn Sports 1 üzerinden)
        base_url = resolve_base_url("yayinzirve")
        if not base_url:
            sys.exit("❌ Yayın sunucusu bulunamadı.")
        print(f"✅ Yayın sunucusu yakalandı: {base_url}")

        # 2. Ana sayfayı çek ve analiz et
        r = requests.get(TARGET_SITE, headers=HEADERS, timeout=10, verify=False)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        final_list = []

        # --- MAÇLAR KISMI (live-content) ---
        matches_area = soup.find(id="matches-content")
        if matches_area:
            for a in matches_area.find_all("a", href=re.compile(r'id=')):
                cid = re.search(r'id=([^&]+)', a["href"]).group(1)
                event = a.find(class_="event").get_text(strip=True) if a.find(class_="event") else "Maç"
                home = a.find(class_="home").get_text(strip=True) if a.find(class_="home") else ""
                away = a.find(class_="away").get_text(strip=True) if a.find(class_="away") else ""
                title = f"{event} | {home} - {away}"
                final_list.append({"cid": cid, "title": title, "group": "Canlı Maçlar"})

        # --- KANALLAR KISMI (channels-content) ---
        channels_area = soup.find(id="channels-content")
        if channels_area:
            for a in channels_area.find_all("a", href=re.compile(r'id=')):
                cid = re.search(r'id=([^&]+)', a["href"]).group(1)
                name = a.find(class_="home").get_text(strip=True) if a.find(class_="home") else cid
                final_list.append({"cid": cid, "title": name, "group": "TV Kanalları"})

        # 3. M3U Dosyasını Yazdır
        with open("betorspin.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for item in final_list:
                f.write(f'#EXTINF:-1 group-title="{item["group"]}",{item["title"]}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={TARGET_SITE}/\n')
                f.write(f'{base_url}{item["cid"]}.m3u8\n')

        print(f"🏁 TAMAM → {len(final_list)} kanal 'betorspin.m3u' dosyasına ham linklerle eklendi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
