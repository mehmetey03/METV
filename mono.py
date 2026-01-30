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

    def find_active_domain(self):
        print("🔍 Aktif domain taranıyor...")
        for i in range(530, 560):
            domain = f"https://monotv{i}.com"
            try:
                r = requests.get(domain, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200:
                    return domain.rstrip('/'), r.text
            except: continue
        return None, None

    def run(self):
        active_url, html_content = self.find_active_domain()
        if not active_url:
            print("❌ Aktif site bulunamadı.")
            return

        print(f"✅ Site bulundu: {active_url}")

        # 1. Yayın sunucusunu bul
        stream_match = re.search(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site|cfd|tv)/)', html_content)
        base_stream = stream_match.group(1) if stream_match else "https://rei.zirvedesin201.cfd/"
        print(f"🌐 Sunucu: {base_stream}")

        # 2. Kanalları Yakala (Regex ile daha garanti)
        # channel?id=X yapısındaki tüm X değerlerini bulur
        all_ids = re.findall(r'channel\?id=([a-zA-Z0-9_-]+)', html_content)
        unique_ids = list(dict.fromkeys(all_ids)) # Tekrarları sil

        if not unique_ids:
            print("⚠️ Hiç ID bulunamadı. Sayfa yapısı tamamen değişmiş olabilir.")
            return

        m3u_lines = ["#EXTM3U"]
        soup = BeautifulSoup(html_content, "html.parser")

        for cid in unique_ids:
            # Çöp ID'leri filtrele
            if cid in ['google', 'facebook', 'twitter']: continue

            # İsim bulma: Önce HTML içinde bu ID'ye sahip olan <a> etiketini ara
            name = cid.upper()
            group = "KANALLAR"
            
            link_element = soup.find("a", href=re.compile(f"id={cid}"))
            if link_element:
                home = link_element.find(class_="home")
                away = link_element.find(class_="away")
                if home and away:
                    name = f"{home.get_text(strip=True)} - {away.get_text(strip=True)}"
                    group = "MACLAR"
                else:
                    clean_name = link_element.get_text(strip=True).replace("7/24", "").strip()
                    if clean_name: name = clean_name

            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={active_url}/')
            m3u_lines.append(f'{base_stream}{cid}/mono.m3u8')

        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        
        print(f"🏁 BİTTİ! {len(unique_ids)} kanal mono.m3u dosyasına eklendi.")

if __name__ == "__main__":
    MonoBot().run()
