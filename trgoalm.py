import requests
import re
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TRGOALS_JSON = "https://raw.githubusercontent.com/mehmetey03/METV/5af7251ac4b20adf59a0c3c8b3431b416a18ab94/trgoals_data.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    try:
        # ===============================
        # SABİT KANAL LİSTESİ (Yeni ID'lere göre güncellendi)
        # ===============================
        fixed_channels = {
            "zirve": ["beIN Sports 1 A", "Inat TV"],
            "trgoals": ["beIN Sports 1 B", "Inat TV"], # Örnekteki trgoals id'si
            "yayin1": ["beIN Sports 1 C", "Inat TV"],
            "b2": ["beIN Sports 2", "Inat TV"],
            "b3": ["beIN Sports 3", "Inat TV"],
            "b4": ["beIN Sports 4", "Inat TV"],
            "b5": ["beIN Sports 5", "Inat TV"],
            "bm1": ["beIN Sports 1 Max", "Inat TV"],
            "bm2": ["beIN Sports 2 Max", "Inat TV"],
            "ss1": ["S Sports 1", "Inat TV"],
            "ss2": ["S Sports 2", "Inat TV"],
            "t1": ["Tivibu Sports 1", "Inat TV"],
            "t2": ["Tivibu Sports 2", "Inat TV"],
            "t3": ["Tivibu Sports 3", "Inat TV"],
            "t4": ["Tivibu Sports 4", "Inat TV"],
            "smarts": ["Smart Sports", "Inat TV"],
            "as": ["A Spor", "Inat TV"],
            "trtspor": ["TRT Spor", "Inat TV"],
            "tv85": ["TV8.5", "Inat TV"],
        }

        # ===============================
        # AKTİF DOMAİN BUL
        # ===============================
        print("🔍 Aktif domain aranıyor...")
        active_domain = None
        for i in range(1497, 2000):
            url = f"https://trgoals{i}.xyz/"
            try:
                r = requests.head(url, headers=HEADERS, timeout=2, verify=False)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Aktif domain: {active_domain}")
                    break
            except: continue

        if not active_domain:
            print("❌ Aktif domain bulunamadı")
            return

        # ===============================
        # BASE URL TESPİTİ (Yeni Yapı)
        # ===============================
        # Örnek: https://9vy.d72577a9dd0ec19.sbs/
        print("📦 Yayın sunucusu adresi alınıyor...")
        # JSON'dan dinamik olarak base_url çekmeye çalışıyoruz
        try:
            json_data = requests.get(TRGOALS_JSON, timeout=10, verify=False).json()
            items = json_data.get("list", {}).get("item", [])
            sample_url = items[0].get("url", "")
            # URL'den son iki kısmı (kanal/mono.m3u8) atıp base_url alıyoruz
            base_url = "/".join(sample_url.split("/")[:-2]) + "/"
        except:
            base_url = "https://9vy.d72577a9dd0ec19.sbs/" # Manuel fallback
        
        print(f"✅ BASE_URL: {base_url}")

        # ===============================
        # CANLI MAÇLARI ÇEK
        # ===============================
        print("📡 Canlı maçlar web sitesinden taranıyor...")
        r = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        dynamic_channels = []
        matches_tab = soup.find(id="matches-tab")
        if matches_tab:
            for link in matches_tab.find_all("a", href=True):
                if "id=" in link["href"]:
                    cid_match = re.search(r'id=([^&]+)', link["href"])
                    if cid_match:
                        cid = cid_match.group(1)
                        name_el = link.find(class_="channel-name")
                        time_el = link.find(class_="channel-status")
                        if name_el:
                            time_str = time_el.get_text(strip=True) if time_el else "Canlı"
                            title = f"{time_str} | {name_el.get_text(strip=True)}"
                            dynamic_channels.append((cid, title))

        # ===============================
        # M3U OLUŞTURMA
        # ===============================
        lines = ["#EXTM3U"]

        # 1. CANLI MAÇLAR
        for cid, title in dynamic_channels:
            lines.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
            lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            # Yeni format: base_url + id + /mono.m3u8
            lines.append(f"{base_url}{cid}/mono.m3u8")

        # 2. SABİT KANALLAR
        for cid, info in fixed_channels.items():
            lines.append(f'#EXTINF:-1 group-title="Inat TV",{info[0]}')
            lines.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(f"{base_url}{cid}/mono.m3u8")

        with open("karsilasmalar2.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"🏁 TAMAM → karsilasmalar2.m3u oluşturuldu.")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
