import requests
import re
import sys
import urllib3

# SSL uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://monotv530.com/"
        }

    def get_active_domain(self):
        print("🔍 Aktif giriş adresi taranıyor...")
        for sayi in range(530, 560):
            url = f"https://monotv{sayi}.com"
            try:
                r = self.session.get(url, timeout=5, verify=False, headers=self.headers)
                if r.status_code == 200:
                    print(f"✅ Giriş adresi bulundu: {url}")
                    return url.rstrip('/')
            except:
                continue
        return None

    def scrape_channels(self, active_domain):
        print("📡 Veriler ayıklanıyor...")
        base_url = "https://rei.zirvedesin201.cfd/"
        
        try:
            r = self.session.get(active_domain, headers=self.headers, verify=False)
            content = r.text
            
            # HTML içindeki her bir kanal/maç bloğunu yakala
            # Pattern: href="channel?id=xxx" bloğunun içindeki tüm içeriği alır
            blocks = re.findall(r'<a class="single-match[^"]*" href="channel\?id=([^"]+)"(.*?)</a>', content, re.DOTALL)
            
            m3u_content = ["#EXTM3U"]
            seen_ids = set()

            for cid, block in blocks:
                if cid in seen_ids: continue
                
                # Blok içinden isimleri çek (Home ve Away takımları/kanal adları)
                home = re.search(r'class="home">([^<]+)</div>', block)
                away = re.search(r'class="away"[^>]*>([^<]*)(?:<img|</div>)', block)
                event = re.search(r'class="event">([^<]+)</div>', block)
                
                # Temizlik ve İsimlendirme
                name_parts = []
                if home: name_parts.append(home.group(1).strip())
                if away and away.group(1).strip(): name_parts.append(away.group(1).strip())
                
                full_name = " - ".join(name_parts) if name_parts else cid.upper()
                event_info = event.group(1).strip() if event else "7/24"
                
                # Grup Belirleme
                group = "MAÇLAR" if "7/24" not in event_info else "KANALLAR"
                
                # M3U Satırlarını Oluştur
                m3u_content.append(f'#EXTINF:-1 group-title="{group}",{full_name} ({event_info})')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                seen_ids.add(cid)

            if len(seen_ids) > 0:
                with open("mono.m3u", "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_content))
                print(f"🏁 BAŞARILI: {len(seen_ids)} adet yayın listeye eklendi.")
            else:
                print("❌ Veri bulunamadı. Regex desenleri sitedeki değişikliğe uymuyor olabilir.")
                sys.exit(1) # Hata ver ki boş dosya pushlanmasın

        except Exception as e:
            print(f"❌ Hata oluştu: {e}")
            sys.exit(1)

def main():
    scraper = MonoScraper()
    domain = scraper.get_active_domain()
    if domain:
        scraper.scrape_channels(domain)
    else:
        print("❌ Siteye ulaşılamadı.")
        sys.exit(1)

if __name__ == "__main__":
    main()
