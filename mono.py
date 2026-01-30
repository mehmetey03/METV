import requests
import re
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoScraper:
    def __init__(self):
        self.session = requests.Session()
        # GitHub engeline takılmamak için daha detaylı header
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }

    def get_active_domain(self):
        print("🔍 Aktif giriş adresi taranıyor...")
        for sayi in range(530, 560):
            url = f"https://monotv{sayi}.com"
            try:
                # SSL doğrulamayı kapatıp timeout'u artırdık
                r = self.session.get(url, timeout=10, verify=False, headers=self.headers)
                if r.status_code == 200:
                    print(f"✅ Giriş adresi bulundu: {url}")
                    return url.rstrip('/')
            except:
                continue
        return None

    def scrape_channels(self, active_domain):
        print("📡 Metin tabanlı derin tarama yapılıyor...")
        base_url = "https://rei.zirvedesin201.cfd/"
        
        try:
            r = self.session.get(active_domain, headers=self.headers, verify=False)
            content = r.text
            
            # YENİ REGEX: Daha basit, id ve ismi içeren her şeyi yakalar
            # id= değerini ve <div> içindeki ilk büyük harfli metni arar
            raw_matches = re.findall(r'id=([a-zA-Z0-9_-]+)".*?>([^<]{3,40})<', content, re.DOTALL)
            
            m3u_content = ["#EXTM3U"]
            seen_ids = set()

            for cid, name in raw_matches:
                # Çöp verileri temizle
                cid = cid.strip()
                name = re.sub(r'<[^>]*>', '', name).strip() # HTML etiketlerini temizle
                
                if cid in seen_ids or len(cid) < 2 or "css" in cid or "js" in cid:
                    continue
                
                if len(name) < 2: name = cid.upper()

                m3u_content.append(f'#EXTINF:-1 group-title="MonoTV",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                seen_ids.add(cid)

            if len(seen_ids) > 0:
                with open("mono.m3u", "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_content))
                print(f"🏁 BAŞARILI: {len(seen_ids)} yayın kaydedildi.")
            else:
                # EĞER HALA BULAMAZSA: Sadece ID'leri çek (Acil Durum Modu)
                print("⚠️ İsimler bulunamadı, ham ID taramasına geçiliyor...")
                emergency_ids = re.findall(r'id=([a-zA-Z0-9]{2,10})', content)
                emergency_ids = list(dict.fromkeys([i for i in emergency_ids if i not in ['live', 'next']]))
                
                if emergency_ids:
                    for eid in emergency_ids:
                        m3u_content.append(f'#EXTINF:-1,{eid.upper()}')
                        m3u_content.append(f'{base_url}{eid}/mono.m3u8')
                    with open("mono.m3u", "w", encoding="utf-8") as f:
                        f.write("\n".join(m3u_content))
                    print(f"🏁 ACİL DURUM: {len(emergency_ids)} ID kaydedildi.")
                else:
                    print("❌ Hiçbir veri çekilemedi. Site GitHub'ı blokluyor.")
                    sys.exit(1)

        except Exception as e:
            print(f"❌ Hata: {e}")
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
