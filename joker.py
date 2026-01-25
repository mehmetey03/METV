import cloudscraper
import re

# Sabit Bilgiler
SITE_URL = "https://jokerbettv177.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def main():
    try:
        # Cloudscraper ile bot korumasını aşmaya çalışıyoruz
        scraper = cloudscraper.create_scraper()
        print(f"📡 Siteye bağlanılıyor: {SITE_URL}")
        
        response = scraper.get(SITE_URL, headers={"User-Agent": UA}, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Site engelledi! Statü Kodu: {response.status_code}")
            return
        
        html_content = response.text
        print("✅ Site içeriği başarıyla çekildi.")

        m3u = ["#EXTM3U"]
        processed_links = set()

        # 1. ÖNCELİK: data-streamx (Worker linkleri: https://pix.xsiic...)
        # HTML: data-streamx="https://..." data-name="S Sport 1"
        streams_x = re.findall(r'data-streamx="([^"]+)".*?data-name="([^"]+)"', html_content, re.DOTALL)
        
        for link, name in streams_x:
            if link not in processed_links:
                clean_name = name.strip().upper()
                m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR (WORKER)",{clean_name}')
                m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
                m3u.append(f'#EXTVLCOPT:http-referrer={SITE_URL}')
                m3u.append(link)
                processed_links.add(link)

        # 2. İKİNCİ ÖNCELİK: Normal data-stream (Eğer streamx yoksa maçlar için)
        streams_normal = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html_content, re.DOTALL)
        # Not: Buradaki linkler için senin API'den gelen baseurl gerekebilir. 
        # Ancak streamx linkleri (pix.xsiic...) daha stabil çalışacaktır.

        if len(m3u) > 1:
            with open("joker.m3u8", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u))
            print(f"🚀 BAŞARILI: {len(processed_links)} adet Worker yayını kaydedildi.")
        else:
            print("❌ HATA: Uygun yayın linki (streamx) bulunamadı.")

    except Exception as e:
        print(f"💥 Hata oluştu: {e}")

if __name__ == "__main__":
    main()
