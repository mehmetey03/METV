import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoBot:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        }
        self.base_stream = "https://rei.zirvedesin201.cfd/"
        self.redirect_url = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/index.html"

    def find_domain(self):
        # 1. Yöntem: Yönlendirme sayfasını kontrol et
        try:
            r = requests.get(self.redirect_url, timeout=5)
            match = re.search(r'URL=(https?://[^">]+)', r.text)
            if match:
                domain = match.group(1).rstrip('/')
                # Domainin gerçekten canlı olduğunu doğrula
                check = requests.head(domain, timeout=3, verify=False)
                if check.status_code < 400:
                    return domain
        except: pass

        # 2. Yöntem: Brute-force (Numara üzerinden otomatik tara)
        print("⚠️ Yönlendirme çalışmıyor, domainler taranıyor...")
        for i in range(530, 550):
            test_url = f"https://monotv{i}.com"
            try:
                r = requests.head(test_url, timeout=2, verify=False)
                if r.status_code == 200:
                    return test_url
            except: continue
        return None

    def run(self):
        active_url = self.find_domain()
        if not active_url:
            print("❌ Aktif domain hiçbir şekilde bulunamadı!")
            return

        print(f"✅ Hedef: {active_url}")
        
        try:
            r = requests.get(active_url, headers=self.headers, verify=False, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            
            m3u_lines = ["#EXTM3U"]
            
            # Hem maçları hem 7/24 kanalları tek seferde kazı
            channels = soup.find_all("a", href=re.compile(r'id='))
            
            for ch in channels:
                cid = re.search(r'id=([^&"]+)', ch['href']).group(1)
                
                # İsim yapılandırması (Home-Away varsa maçtır, yoksa kanaldır)
                home = ch.find(class_="home")
                away = ch.find(class_="away")
                
                if home and away:
                    name = f"{home.text.strip()} vs {away.text.strip()}"
                    group = "CANLI MACLAR"
                else:
                    # Alternatif: İçindeki span veya div'den ismi al
                    name = ch.get_text(strip=True).replace("7/24", "").strip()
                    group = "7/24 KANALLAR"

                if not name: name = cid.upper()

                m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
                m3u_lines.append(f'#EXTVLCOPT:http-referrer={active_url}/')
                m3u_lines.append(f'{self.base_stream}{cid}/mono.m3u8')

            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_lines))
                
            print(f"🏁 Tamamlandı. {len(m3u_lines)//3} kanal kaydedildi.")

        except Exception as e:
            print(f"❌ Tarama hatası: {e}")

if __name__ == "__main__":
    MonoBot().run()
