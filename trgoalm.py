import requests
import re
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GÜNCEL SABİT KANAL LİSTESİ JSON
TRGOALS_JSON = "https://raw.githubusercontent.com/mehmetey03/METV/c4ba1c230767d0cd393798283dd4caec10b83374/trgoals_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    try:
        # ===============================
        # 1. AKTİF DOMAİN BUL (Web sitesi için)
        # ===============================
        print("🔍 Aktif domain aranıyor...")
        active_domain = "https://trgoals1521.xyz/" # Hızlı olması için son bulduğunu başa koyabilirsin
        try:
            r = requests.head(active_domain, headers=HEADERS, timeout=3, verify=False)
            if r.status_code != 200:
                for i in range(1510, 1550):
                    url = f"https://trgoals{i}.xyz/"
                    try:
                        if requests.head(url, headers=HEADERS, timeout=2, verify=False).status_code == 200:
                            active_domain = url
                            break
                    except: continue
        except: pass
        print(f"✅ Aktif domain: {active_domain}")

        # ===============================
        # 2. SABİT KANALLARI JSON'DAN ÇEK
        # ===============================
        print("📦 Sabit kanallar JSON'dan alınıyor...")
        json_response = requests.get(TRGOALS_JSON, timeout=10, verify=False).json()
        items = json_response.get("list", {}).get("item", [])
        
        fixed_entries = []
        base_url_auto = ""

        for item in items:
            title = item.get("title", "Bilinmeyen Kanal")
            url = item.get("url", "")
            if url:
                fixed_entries.append((title, url))
                # İlk geçerli URL'den base_url çıkarmaya çalış (dinamik maçlar için)
                if not base_url_auto:
                    base_url_auto = "/".join(url.split("/")[:-2]) + "/"

        print(f"✅ {len(fixed_entries)} sabit kanal yüklendi.")
        print(f"📡 Otomatik Base URL: {base_url_auto}")

        # ===============================
        # 3. CANLI MAÇLARI WEB SİTESİNDEN ÇEK
        # ===============================
        print("📡 Canlı maçlar web sitesinden taranıyor...")
        dynamic_channels = []
        try:
            r = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            matches_tab = soup.find(id="matches-tab")
            if matches_tab:
                for link in matches_tab.find_all("a", href=True):
                    cid_match = re.search(r'id=([^&]+)', link["href"])
                    if cid_match:
                        cid = cid_match.group(1)
                        name_el = link.find(class_="channel-name")
                        time_el = link.find(class_="channel-status")
                        if name_el:
                            label = f"{time_el.get_text(strip=True) if time_el else 'CANLI'} | {name_el.get_text(strip=True)}"
                            # Dinamik maç linkini yeni formata göre oluştur
                            m3u8_url = f"{base_url_auto}{cid}/mono.m3u8"
                            dynamic_channels.append((label, m3u8_url))
        except Exception as e:
            print(f"⚠️ Maçlar çekilirken hata: {e}")

        # ===============================
        # 4. M3U OLUŞTURMA
        # ===============================
        lines = ["#EXTM3U"]

        # Önce Canlı Maçlar
        for title, link in dynamic_channels:
            lines.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
            lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(link)

        # Sonra Sabit Kanallar
        for title, link in fixed_entries:
            lines.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{title}')
            lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(link)

        with open("karsilasmalar2.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"🏁 TAMAM → karsilasmalar2.m3u oluşturuldu. ({len(dynamic_channels)} Maç + {len(fixed_entries)} Sabit)")

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

if __name__ == "__main__":
    main()
