import cloudscraper
import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
SITE_URL = "https://jokerbettv177.com/"
DOMAIN_API = "https://maqrizi.com/domain.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def main():
    try:
        # 1. Base URL Çek
        base_url = requests.get(DOMAIN_API, timeout=10).json().get("baseurl", "")
        
        # 2. Siteye Bağlan (Bot Korumasını Aşmak İçin Scraper Kullanıyoruz)
        scraper = cloudscraper.create_scraper()
        response = scraper.get(SITE_URL, headers={"User-Agent": UA}, timeout=15)
        
        if response.status_code != 200:
            print(f"Site Hatası: {response.status_code}")
            return

        html = response.text
        m3u = ["#EXTM3U"]
        ids = set()

        # 3. StreamX Linklerini Bul (Paylaştığın pix.xsiic... linkleri)
        # Örnek: data-streamx="https://..." data-name="S Sport 1"
        worker_matches = re.findall(r'data-streamx="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
        for link, name in worker_matches:
            if link not in ids:
                m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name.strip().upper()}')
                m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
                m3u.append(f'#EXTVLCOPT:http-referrer={SITE_URL}')
                m3u.append(link)
                ids.add(link)

        # 4. Normal Data-Stream Linklerini Bul (Maçlar için)
        normal_matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
        for stream_id, name in normal_matches:
            if stream_id not in ids:
                clean_name = name.strip().upper()
                group = "⚽ CANLI MAÇLAR" if "-" in clean_name else "📺 SABİT KANALLAR"
                m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
                m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
                m3u.append(f'#EXTVLCOPT:http-referrer={SITE_URL}')
                m3u.append(f"{base_url}{stream_id}.m3u8")
                ids.add(stream_id)

        # 5. Dosyayı Kaydet
        if len(m3u) > 1:
            with open("joker.m3u8", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u))
            print(f"Başarılı! {len(ids)} yayın joker.m3u8 dosyasına yazıldı.")
        else:
            print("Yayın bulunamadı!")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()
