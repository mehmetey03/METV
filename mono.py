import requests
import re
import json
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AdvancedMonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

    def get_active_domain(self):
        """Domainleri tarar ve aktif olanı döndürür."""
        print("🔍 Aktif domain taranıyor...")
        # Senin brute-force mantığın en güvenlisi
        for sayi in range(530, 560):
            domain = f"https://monotv{sayi}.com"
            try:
                # Sadece ana sayfayı hızlıca kontrol et
                r = self.session.get(domain, timeout=4, verify=False, headers=self.headers)
                if r.status_code == 200:
                    print(f"✅ Aktif site bulundu: {domain}")
                    return domain.rstrip('/')
            except:
                continue
        return None

    def find_m3u8_server(self, html):
        """Yayın sunucusunu HTML içinden otomatik ayıklar."""
        # Senin verdiğin sunucuyu da kapsayan geniş regex
        pattern = r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site|cfd|tv)/)'
        match = re.search(pattern, html)
        if match:
            server = match.group(1)
            print(f"🌐 Yayın sunucusu: {server}")
            return server
        return "https://rei.zirvedesin201.cfd/" # Fallback

    def scrape(self):
        domain = self.get_active_domain()
        if not domain: return

        try:
            r = self.session.get(domain, headers=self.headers, verify=False)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, 'html.parser')
            
            m3u8_server = self.find_m3u8_server(r.text)
            channels = []

            # 1. Maçlar ve Kanallar için Ortak Tarama
            # Sitedeki tüm 'channel?id=' içeren linkleri bul
            links = soup.find_all('a', href=re.compile(r'channel\?id='))
            
            for link in links:
                cid_match = re.search(r'id=([^&"\']+)', link['href'])
                if not cid_match: continue
                cid = cid_match.group(1)

                # İsim Ayıklama (Gelişmiş)
                # Önce içindeki span veya div'lere bak, yoksa düz metni al
                home = link.find(class_="home")
                away = link.find(class_="away")
                
                if home and away:
                    name = f"{home.get_text(strip=True)} - {away.get_text(strip=True)}"
                    group = "CANLI MACLAR"
                else:
                    name = link.get_text(strip=True).replace("7/24", "").strip()
                    group = "7/24 KANALLAR"

                if not name: name = cid.upper()

                channels.append({
                    "name": name,
                    "group": group,
                    "url": f"{m3u8_server}{cid}/mono.m3u8"
                })

            # 2. M3U Oluşturma
            if channels:
                with open("mono_list.m3u", "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    for ch in channels:
                        f.write(f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}\n')
                        f.write(f'#EXTVLCOPT:http-referrer={domain}/\n')
                        f.write(f'{ch["url"]}\n')
                print(f"🏁 Başarılı! {len(channels)} kanal mono_list.m3u dosyasına yazıldı.")
            else:
                print("⚠️ Hiç kanal bulunamadı.")

        except Exception as e:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    AdvancedMonoScraper().scrape()
