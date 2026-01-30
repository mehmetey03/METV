import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoBot:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://google.com"
        }
        self.search_range = range(530, 560)

    def find_active_assets(self):
        """Aktif domaini ve o domainin kullandığı yayın sunucusunu bulur."""
        print("🔍 Aktif kaynaklar taranıyor...")
        
        for num in self.search_range:
            domain = f"https://monotv{num}.com"
            try:
                # 1. Domain kontrolü
                r = requests.get(domain, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200:
                    print(f"✅ Domain bulundu: {domain}")
                    
                    # 2. Yayın sunucusunu (Base URL) HTML içinden çek
                    # Genelde m3u8 linklerinin başındaki https://... kısmını yakalar
                    stream_match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6}/)[^"\']+?/mono\.m3u8', r.text)
                    
                    if stream_match:
                        base_stream = stream_match.group(1)
                        print(f"✅ Yayın sunucusu tespit edildi: {base_stream}")
                        return domain, base_stream
                    else:
                        # Alternatif: Sayfadaki herhangi bir sbs/xyz/cfd uzantılı stream yapısını ara
                        alt_match = re.search(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site|cfd)/)', r.text)
                        if alt_match:
                            base_stream = alt_match.group(1)
                            print(f"✅ Yayın sunucusu (Alternatif) tespit edildi: {base_stream}")
                            return domain, base_stream
            except:
                continue
        return None, None

    def run(self):
        active_url, base_stream = self.find_active_assets()
        
        if not active_url or not base_stream:
            print("❌ Kaynaklar otomatik bulunamadı. Site yapısı değişmiş olabilir.")
            return

        try:
            r = requests.get(active_url, headers=self.headers, verify=False, timeout=10)
            r.encoding = 'utf-8'
            soup = BeautifulSoup(r.text, "html.parser")
            
            m3u_lines = ["#EXTM3U"]
            # Kanal linklerini topla
            channels = soup.find_all("a", href=re.compile(r'channel\?id='))
            
            for ch in channels:
                cid_match = re.search(r'id=([^&"]+)', ch['href'])
                if not cid_match: continue
                cid = cid_match.group(1)
                
                # Maç ve kanal isimlerini temizle
                home = ch.find(class_="home")
                away = ch.find(class_="away")
                
                if home and away:
                    name = f"{home.get_text(strip=True)} - {away.get_text(strip=True)}"
                    group = "CANLI MACLAR"
                else:
                    name = ch.get_text(strip=True).replace("7/24", "").strip()
                    group = "7/24 KANALLAR"

                if not name: name = cid.upper()

                m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
                m3u_lines.append(f'#EXTVLCOPT:http-referrer={active_url}/')
                m3u_lines.append(f'{base_stream}{cid}/mono.m3u8')

            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_lines))
            print(f"🏁 İşlem tamam: {len(m3u_lines)//3} kanal m3u olarak kaydedildi.")

        except Exception as e:
            print(f"❌ Liste işlenirken hata: {e}")

if __name__ == "__main__":
    MonoBot().run()
