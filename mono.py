import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

    def get_active_domain(self):
        print("🔍 Aktif giriş adresi taranıyor...")
        for sayi in range(530, 560):
            url = f"https://monotv{sayi}.com"
            try:
                r = self.session.get(url, timeout=4, verify=False, headers=self.headers)
                if r.status_code == 200:
                    print(f"✅ Giriş adresi bulundu: {url}")
                    return url.rstrip('/')
            except: continue
        return None

    def scrape_channels(self, active_domain):
        print("📡 Kanallar taranıyor...")
        try:
            r = self.session.get(active_domain, headers=self.headers, timeout=10, verify=False)
            r.encoding = 'utf-8'
            html = r.text
            soup = BeautifulSoup(html, 'html.parser')

            # 1. Yayın sunucusunu (base URL) otomatik bul
            stream_match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6})/[\w\-]+/mono\.m3u8', html)
            base_url = stream_match.group(1).rstrip('/') + "/" if stream_match else "https://rei.zirvedesin201.cfd/"

            # 2. Tüm linkleri tara
            links = soup.find_all('a', href=re.compile(r'id='))
            m3u_content = ["#EXTM3U"]
            added_ids = set()

            for link in links:
                # ID'yi çek
                cid_match = re.search(r'id=([^&"\'\s]+)', link['href'])
                if not cid_match: continue
                cid = cid_match.group(1)
                
                if cid in added_ids or len(cid) < 2 or cid in ['google', 'facebook']: continue

                # Maç isimlerini (Home - Away) yakala
                home = link.find(class_="home")
                away = link.find(class_="away")
                
                if home and away:
                    name = f"{home.get_text(strip=True)} - {away.get_text(strip=True)}"
                    group = "CANLI MACLAR"
                else:
                    # Normal kanal ismi
                    name = link.get_text(strip=True).replace("7/24", "").strip()
                    group = "7/24 KANALLAR"

                if not name: name = cid.upper()

                m3u_content.append(f'#EXTINF:-1 group-title="{group}",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                added_ids.add(cid)

            if len(m3u_content) > 1:
                with open("mono.m3u", "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_content))
                print(f"🏁 BAŞARILI: {len(added_ids)} kanal kaydedildi.")
            else:
                print("❌ Hiç kanal bulunamadı.")

        except Exception as e:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    scraper = MonoScraper()
    domain = scraper.get_active_domain()
    if domain:
        scraper.scrape_channels(domain)
