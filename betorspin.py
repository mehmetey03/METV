import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
API_URL = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE
}

SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", 
    "beIN Sports 3": "yayinb3.m3u8", "S Sport 1": "yayinss.m3u8", 
    "S Sport 2": "yayinss2.m3u8", "Tivibu Spor 1": "yayint1.m3u8",
    "Smart Spor": "yayinsmarts.m3u8", "TRT Spor": "yayintrtspor.m3u8"
}

def main():
    m3u_content = ["#EXTM3U"]
    
    try:
        # 1. Sunucu Adresini Al
        print("📡 Sunucu adresi alınıyor...")
        base_url = requests.get(API_URL, headers=HEADERS, timeout=10).json().get("baseurl")
        if not base_url: return

        # 2. Ana Sayfayı Tara
        print("⚽ Canlı maçlar deşifre ediliyor...")
        r = requests.get(TARGET_SITE, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Maçları "single-match" class üzerinden bul
        matches = soup.find_all("a", class_="single-match")
        count_matches = 0

        for match in matches:
            href = match.get("href", "")
            cid_match = re.search(r'id=([^&]+)', href)
            
            if cid_match:
                cid = cid_match.group(1)
                # Detayları çek
                time_info = match.find("div", class_="event").get_text(strip=True) if match.find("div", class_="event") else ""
                home_team = match.find("div", class_="home").get_text(strip=True) if match.find("div", class_="home") else ""
                away_team = match.find("div", class_="away").get_text(strip=True) if match.find("div", class_="away") else ""
                sport_type = match.find("div", class_="date").get_text(strip=True) if match.find("div", class_="date") else "Spor"
                
                display_name = f"{time_info} | {home_team} - {away_team} ({sport_type})"
                
                m3u_content.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{display_name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET_SITE}')
                
                link = f"{base_url}{cid}.m3u8" if not cid.endswith(".m3u8") else f"{base_url}{cid}"
                m3u_content.append(link)
                count_matches += 1

        # 3. Sabit Kanalları Ekle
        print(f"✅ {count_matches} canlı maç bulundu. Sabit kanallar ekleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_content.append(f'#EXTINF:-1 group-title="📺 TV KANALLARI",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET_SITE}')
            m3u_content.append(f"{base_url}{file}")

        # 4. Kaydet
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"💾 Dosya hazır! Toplam {count_matches + len(SABIT_KANALLAR)} kanal eklendi.")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
