import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API ve Site Bilgileri
API_URL = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE
}

# Sabit Kanal Listesi
SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", "beIN Sports 3": "yayinb3.m3u8",
    "S Sport 1": "yayinss.m3u8", "S Sport 2": "yayinss2.m3u8", "Tivibu Spor 1": "yayint1.m3u8",
    "Smart Spor": "yayinsmarts.m3u8", "TRT Spor": "yayintrtspor.m3u8", "TV8.5": "yayintv85.m3u8"
}

def main():
    m3u_content = ["#EXTM3U"]
    
    try:
        # 1. Sunucu Adresini Al
        print("📡 Sunucu adresi alınıyor...")
        base_url = requests.get(API_URL, headers=HEADERS, timeout=10).json().get("baseurl")
        if not base_url: return

        # 2. Ana Sayfayı Tara (Canlı Maçlar İçin)
        print("⚽ Canlı maçlar taranıyor...")
        r = requests.get(TARGET_SITE, headers=HEADERS, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Maç kutucuklarını bul
        matches_div = soup.find("div", id="matches-content")
        if matches_div:
            for a in matches_div.find_all("a", href=True):
                cid_match = re.search(r'id=([^&]+)', a["href"])
                if cid_match:
                    cid = cid_match.group(1)
                    # Takım isimlerini al
                    home = a.find(class_="home").get_text(strip=True) if a.find(class_="home") else ""
                    away = a.find(class_="away").get_text(strip=True) if a.find(class_="away") else ""
                    time = a.find(class_="event").get_text(strip=True) if a.find(class_="event") else "00:00"
                    
                    match_name = f"{time} | {home} - {away}" if home else cid
                    
                    m3u_content.append(f'#EXTINF:-1 group-title="⚽ CANLI MACLAR",{match_name}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET_SITE}')
                    # Eğer cid içinde zaten .m3u8 varsa ekleme, yoksa ekle
                    link = f"{base_url}{cid}" if ".m3u8" in cid else f"{base_url}{cid}.m3u8"
                    m3u_content.append(link)

        # 3. Sabit Kanalları Ekle
        print("📺 Sabit kanallar ekleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_content.append(f'#EXTINF:-1 group-title="📺 TV KANALLARI",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET_SITE}')
            m3u_content.append(f"{base_url}{file}")

        # 4. Dosyayı Kaydet
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"✅ İşlem Tamam! Toplam {len(m3u_content)//4} içerik eklendi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
