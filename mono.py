import requests
import re
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

    def get_active_domain(self):
        print("🔍 Aktif giriş adresi taranıyor...")
        for sayi in range(530, 560): # Menzili daralttım, daha hızlı tarar
            url = f"https://monotv{sayi}.com"
            try:
                r = self.session.get(url, timeout=5, verify=False, headers=self.headers)
                if r.status_code == 200:
                    print(f"✅ Giriş adresi bulundu: {url}")
                    return url.rstrip('/')
            except: continue
        return None

    def resolve_base_url(self, active_domain):
        try:
            r = self.session.get(active_domain, headers=self.headers, timeout=10, verify=False)
            # Yayın sunucusunu (base URL) regex ile otomatik yakala
            match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6})/[\w\-]+/mono\.m3u8', r.text)
            if match:
                return match.group(1).rstrip('/') + "/"
        except: pass
        return "https://rei.zirvedesin201.cfd/" # Fallback (Yedek Sunucu)

    def scrape_channels(self, active_domain, base_url):
        print("📡 Kanallar taranıyor...")
        try:
            r = self.session.get(active_domain, headers=self.headers, timeout=10, verify=False)
            # Sadece channel?id= kısmını değil, tüm id'leri yakalar
            cids = re.findall(r'id=([a-zA-Z0-9_-]+)', r.text)
            unique_ids = []
            [unique_ids.append(x) for x in cids if x not in unique_ids]

            m3u_content = ["#EXTM3U"]
            for cid in unique_ids:
                # Filtreleme
                if len(cid) < 2 or cid in ['google', 'facebook', 'twitter', 'whatsapp', 'telegram']: continue
                
                # İsimlendirme (Geliştirilmiş)
                name = cid.upper()
                group = "7/24 Kanallar"
                
                if any(x in cid.lower() for x in ['bein', 'spor', 'mac', 'tivibu', 'smart']):
                    group = "Spor Kanalları"

                m3u_content.append(f'#EXTINF:-1 group-title="{group}",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')

            if len(m3u_content) > 1:
                with open("mono.m3u", "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_content))
                print(f"🏁 BAŞARILI: {len(unique_ids)} yayın kaydedildi.")
            else:
                print("❌ Kanal bulunamadı.")
        except Exception as e:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    scraper = MonoScraper()
    domain = scraper.get_active_domain()
    if domain:
        base = scraper.resolve_base_url(domain)
        scraper.scrape_channels(domain, base)
