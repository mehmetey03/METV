import cloudscraper
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Adresi Mobil Olarak Değiştirdik
SITE_URL = "https://jokerbettv177.com/"
DOMAIN_API = "https://maqrizi.com/domain.php"

# User-Agent'ı Mobil (iPhone) olarak değiştirdik, 403'ü aşabilir.
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"

def main():
    try:
        # 1. Base URL Çek
        base_url = ""
        try:
            base_url = requests.get(DOMAIN_API, timeout=10).json().get("baseurl", "")
        except:
            print("API'den sunucu alınamadı.")

        # 2. Siteye Bağlan
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android',
                'desktop': False
            }
        )
        
        response = scraper.get(SITE_URL, headers={"User-Agent": MOBILE_UA}, timeout=20)
        
        # 403 kontrolü
        if response.status_code == 403:
            print("❌ Site hala 403 veriyor. GitHub IP'leri yasaklı.")
            return

        html = response.text
        m3u = ["#EXTM3U"]
        ids = set()

        # StreamX (Worker) Linkleri
        worker_matches = re.findall(r'data-streamx="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
        for link, name in worker_matches:
            if link not in ids:
                m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name.strip().upper()}')
                m3u.append(f'#EXTVLCOPT:http-user-agent={MOBILE_UA}')
                m3u.append(f'#EXTVLCOPT:http-referrer={SITE_URL}')
                m3u.append(link)
                ids.add(link)

        # Normal Data-Stream
        normal_matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
        for stream_id, name in normal_matches:
            if stream_id not in ids:
                clean_name = name.strip().upper()
                group = "⚽ CANLI MAÇLAR" if "-" in clean_name else "📺 SABİT KANALLAR"
                m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
                m3u.append(f'#EXTVLCOPT:http-user-agent={MOBILE_UA}')
                m3u.append(f'#EXTVLCOPT:http-referrer={SITE_URL}')
                m3u.append(f"{base_url}{stream_id}.m3u8")
                ids.add(stream_id)

        if len(m3u) > 1:
            with open("joker.m3u8", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u))
            print(f"✅ Başarılı! {len(ids)} yayın kaydedildi.")
        else:
            print("⚠️ Sayfa açıldı ama yayın bulunamadı.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()
