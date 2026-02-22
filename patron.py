import requests
import re
import os
import urllib3
import json
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SADECE API KAYNAĞI
API_URL = "https://patronsports1.cfd/domain.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_dynamic_config():
    """API'den baseurl çeker ve aktif domaini belirler."""
    try:
        r = requests.get(API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        
        # JSON'dan baseurl'i al
        base_url = data.get("baseurl", "").strip().rstrip('/') + "/"
        
        # Aktif domaini API adresinden türet (https://patronsports1.cfd)
        active_domain = "/".join(API_URL.split("/")[:3])
        
        return active_domain, base_url
    except Exception as e:
        print(f"⚠️ Kritik Hata: Veri çekilemedi -> {e}")
        return None, None

def main():
    # Dinamik bilgileri al
    active_domain, base_url = get_dynamic_config()
    
    # Bilgiler eksikse kod çalışmayı durdurur (Fallback yazılmadı)
    if not active_domain or not base_url:
        return

    m3u_content = ["#EXTM3U"]
    
    # 1. CANLI MAÇLAR
    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        match_items = soup.find_all("div", class_="channel-item")
        
        for item in match_items:
            src = item.get("data-src", "")
            cid_match = re.search(r'id=([^&]+)', src)
            if not cid_match: continue
            cid = cid_match.group(1)

            teams = item.find_all("span", class_="team-name")
            home = teams[0].get_text(strip=True) if len(teams) > 0 else "Kanal"
            away = teams[1].get_text(strip=True) if len(teams) > 1 else ""
            league = item.find("span", class_="league-text").get_text(strip=True) if item.find("span", class_="league-text") else "Spor"
            mtime = item.find("span", class_="match-time").get_text(strip=True) if item.find("span", class_="match-time") else ""

            display_name = f"{home} - {away} [{mtime}] ({league})".strip()
            
            m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{display_name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            
    except:
        pass

    # 2. SABİT KANALLAR (Dinamik BaseURL ile)
    fixed_channels = {
        "patron": "beIN Sports 1", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
        "ss1": "S Sport 1", "ss2": "S Sport 2", "t1": "Tivibu Spor 1"
    }

    for cid, name in fixed_channels.items():
        m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
        m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    # DOSYA YAZMA
    if len(m3u_content) > 1:
        with open("karsilasmalar4.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"✅ Liste oluşturuldu. Sunucu: {base_url}")

if __name__ == "__main__":
    main()
