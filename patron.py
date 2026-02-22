import requests
import re
import os
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# AYARLAR
SOURCE_URL = "https://hepbetspor16.cfd" # HTML'in çekileceği ana sayfa
STREAM_SERVER = "https://obv.d72577a9dd0ec28.sbs/" 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def main():
    m3u_content = ["#EXTM3U"]
    
    try:
        print(f"📡 Veri çekiliyor: {SOURCE_URL}")
        resp = requests.get(SOURCE_URL, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # HTML içindeki tüm maç kartlarını (channel-item) bul
        match_items = soup.find_all("div", class_="channel-item")
        
        for item in match_items:
            # 1. Yayın ID'sini data-src'den çek (/ch.html?id=patron)
            src = item.get("data-src", "")
            cid_match = re.search(r'id=([^&]+)', src)
            if not cid_match:
                continue
            cid = cid_match.group(1)

            # 2. Takım İsimlerini Çek
            teams = item.find_all("span", class_="team-name")
            home_team = teams[0].get_text(strip=True) if len(teams) > 0 else "Bilinmeyen"
            away_team = teams[1].get_text(strip=True) if len(teams) > 1 else ""
            
            # 3. Lig Bilgisini Çek
            league_tag = item.find("span", class_="league-text")
            league = league_tag.get_text(strip=True) if league_tag else "Canlı Maç"

            # 4. Saat Bilgisini Çek
            time_tag = item.find("span", class_="match-time")
            match_time = time_tag.get_text(strip=True) if time_tag else ""

            # M3U Formatını oluştur
            display_name = f"{home_team} - {away_team} [{match_time}] ({league})".replace(" -  ", "")
            
            m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{display_name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={SOURCE_URL}/')
            m3u_content.append(f'{STREAM_SERVER}{cid}/mono.m3u8')

        print(f"✅ {len(match_items)} maç listeye eklendi.")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

    # DOSYA YAZMA
    file_name = "karsilasmalar4.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    if os.path.exists(file_name):
        print(f"📂 {file_name} başarıyla güncellendi.")

if __name__ == "__main__":
    main()
