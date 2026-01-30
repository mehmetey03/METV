import requests
import re
import sys
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def get_active_domain(self):
        print("🔍 Aktif giriş adresi taranıyor...")
        for sayi in range(530, 600):
            url = f"https://monotv{sayi}.com"
            try:
                r = self.session.get(url, timeout=5, verify=False, headers=self.headers)
                if r.status_code == 200:
                    print(f"✅ Giriş adresi bulundu: {url}")
                    return url.rstrip('/')
            except:
                continue
        return None

    def resolve_base_url(self, active_domain):
        print("📡 Yayın sunucusu tespit ediliyor...")
        try:
            # Ana sayfayı çekip içindeki m3u8 patternlerini ara
            r = self.session.get(active_domain, headers=self.headers, timeout=10, verify=False)
            # Sayfa içinde gizli olabilecek m3u8 sunucularını ara
            match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6})/[\w\-]+/mono\.m3u8', r.text)
            if match:
                res = match.group(1).rstrip('/') + "/"
                print(f"✅ Otomatik sunucu bulundu: {res}")
                return res
        except:
            pass
        return "https://rei.zirvedesin201.cfd/"

    def scrape_channels(self, active_domain, base_url):
        print("📡 Kanallar taranıyor...")
        try:
            r = self.session.get(active_domain, headers=self.headers, timeout=10, verify=False)
            content = r.text
            
            # BeautifulSoup bazen JS içeren sitelerde sapıtabilir, o yüzden REGEX ile direkt ID çekiyoruz
            # Örn: channel.html?id=zirve veya id=bein1 gibi yapıları yakalar
            cids = re.findall(r'id=([a-zA-Z0-9_-]+)', content)
            cids = list(dict.fromkeys(cids)) # Tekrar edenleri temizle
            
            if not cids:
                # Alternatif: Eğer id= şeklinde yoksa, direkt linkleri ara
                cids = re.findall(r'href=["\'](?:[^"\']*)\?id=([^"\'&]+)', content)

            m3u_content = ["#EXTM3U"]
            for cid in cids:
                # Gereksiz id'leri filtrele (analytics, reklam vb. olmasın diye)
                if len(cid) < 2 or cid in ['google', 'facebook', 'twitter']: continue
                
                name = cid.upper().replace('B', 'beIN ').replace('S', 'S ') # Basit isimlendirme
                m3u_content.append(f'#EXTINF:-1 group-title="MonoTV Otomatik",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')

            if len(m3u_content) > 1:
                with open("mono.m3u", "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_content))
                print(f"🏁 BAŞARILI: {len(m3u_content)//3} kanal bulundu ve kaydedildi.")
            else:
                print("❌ Kanal bulunamadı. Site bot koruması kullanıyor olabilir.")

        except Exception as e:
            print(f"❌ Hata: {e}")

def main():
    scraper = MonoScraper()
    domain = scraper.get_active_domain()
    if domain:
        base = scraper.resolve_base_url(domain)
        scraper.scrape_channels(domain, base)
    else:
        print("❌ Siteye ulaşılamadı.")

if __name__ == "__main__":
    main()
