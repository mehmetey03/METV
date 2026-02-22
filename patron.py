import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def main():
    main_site = "https://hepbetspor16.cfd"
    base_url = "https://obv.d72577a9dd0ec28.sbs/"
    
    print(f"📡 Bağlanılıyor: {main_site}")
    
    response = requests.get(main_site, headers=HEADERS, timeout=15, verify=False)
    html = response.text
    
    # Tüm maçları tek bir regex ile bul
    pattern = r'id=(.?*?)".*?team-name">(.*?)</span>.*?team-name">(.*?)</span>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    m3u = ["#EXTM3U"]
    
    for cid, team1, team2 in matches:
        name = f"{team1} - {team2}"
        print(f"📺 {name} (ID: {cid})")
        
        m3u.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
        m3u.append(f'#EXTVLCOPT:http-referrer={main_site}/')
        m3u.append(f'{base_url}{cid}/mono.m3u8')
    
    with open("patron_maçlar.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    
    print(f"✅ Toplam {len(matches)} maç eklendi")

if __name__ == "__main__":
    main()
