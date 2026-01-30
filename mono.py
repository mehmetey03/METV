import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://monotv530.com/"
        }

    def get_active_domain(self):
        for sayi in range(530, 600):
            url = f"https://monotv{sayi}.com"
            try:
                r = self.session.get(url, timeout=5, verify=False)
                if r.status_code == 200:
                    return url.rstrip('/')
            except:
                continue
        return None

    def scrape(self):
        domain = self.get_active_domain()
        if not domain:
            print("❌ Aktif domain bulunamadı.")
            return

        print(f"✅ Domain: {domain}")
        base_url = "https://rei.zirvedesin201.cfd/" # Statik veya dinamik sunucu adresi
        
        try:
            r = self.session.get(domain, headers=self.headers, verify=False)
            soup = BeautifulSoup(r.text, "html.parser")
            m3u_content = ["#EXTM3U"]
            seen_ids = set()

            # Tüm 'single-match' class'ına sahip linkleri tara
            for a in soup.find_all("a", class_="single-match"):
                href = a.get("href", "")
                cid_match = re.search(r'id=([^&]+)', href)
                
                if cid_match:
                    cid = cid_match.group(1)
                    if cid in seen_ids: continue
                    
                    # HTML içinden isimleri çekme
                    home = a.find(class_="home")
                    away = a.find(class_="away")
                    event = a.find(class_="event")
                    
                    # İsim oluşturma mantığı
                    if home and away:
                        # Eğer maç ise: "Takım A - Takım B"
                        channel_name = f"{home.get_text(strip=True)} - {away.get_text(strip=True)}"
                    elif home:
                        # Eğer kanal ise (beIN vb.): "BEIN SPORTS 1"
                        channel_name = home.get_text(strip=True)
                    else:
                        channel_name = cid.upper()

                    # Grup bilgisi (Maç mı Kanal mı?)
                    group = "Canlı Maçlar" if event and "7/24" not in event.get_text() else "7/24 Spor Kanalları"
                    
                    m3u_content.append(f'#EXTINF:-1 group-title="{group}",{channel_name}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={domain}/')
                    m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                    seen_ids.add(cid)

            if len(m3u_content) > 1:
                with open("mono.m3u", "w", encoding="utf-8") as f:
                    f.write("\n".join(m3u_content))
                print(f"🏁 Başarılı! {len(seen_ids)} kanal listeye eklendi.")
            else:
                print("❌ HTML okundu ama kanal verisi ayıklanamadı.")

        except Exception as e:
            print(f"❌ Hata: {e}")

if __name__ == "__main__":
    MonoScraper().scrape()
