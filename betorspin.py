import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET = "https://63betorspintv.live"
# Şu an aktif olan yedek sunucu (Eğer otomatik bulamazsa bunu kullanacak)
FALLBACK_SERVER = "https://5or.d72577a9dd0ec15.sbs/" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET + "/",
    "X-Requested-With": "XMLHttpRequest"
}

BANNED = ["jsdelivr", "gstatic", "google", "hizliresim", "doubleclick", "analytics", "facebook", "jscdn", "hlsjs"]

def find_server(session):
    # Önce kanal sayfasını dene
    pages = ["/channel?id=yayinzirve", "/", "/index.html"]
    for page in pages:
        try:
            r = session.get(TARGET + page, headers=HEADERS, timeout=15, verify=False)
            # Daha geniş bir regex: .sbs, .live, .me, .xyz, .site, .club, .tv, .net
            found = re.findall(r'https?://[a-z0-9.-]+\.(?:sbs|live|me|xyz|site|club|net|pw|online|com\.tr|top)/', r.text)
            for link in found:
                if not any(bad in link.lower() for bad in BANNED):
                    return link
        except: continue
    return FALLBACK_SERVER

def main():
    session = requests.Session()
    m3u_content = ["#EXTM3U"]
    
    try:
        print(f"📡 {TARGET} üzerinden sunucu aranıyor...")
        base_url = find_server(session)
        print(f"✅ Kullanılan Sunucu: {base_url}")

        r_main = session.get(TARGET, headers=HEADERS, timeout=15, verify=False)
        r_main.encoding = "utf-8"
        soup = BeautifulSoup(r_main.text, "html.parser")
        
        # Hem maçları hem kanalları yakala
        containers = soup.find_all("div", id=["matches-content", "channels-content"])
        
        count = 0
        for box in containers:
            group = "Canlı Maçlar" if box.get('id') == "matches-content" else "TV Kanalları"
            for a in box.find_all("a", href=True):
                if "id=" in a["href"]:
                    cid_match = re.search(r'id=([^&]+)', a["href"])
                    if not cid_match: continue
                    cid = cid_match.group(1)
                    
                    # Başlık için hiyerarşik arama
                    name_el = a.find(class_="home") or a.find(class_="event") or a.find(class_="channel-name")
                    title = name_el.get_text(strip=True) if name_el else cid
                    
                    # Maç ise takım isimlerini birleştir
                    away_el = a.find(class_="away")
                    if away_el and group == "Canlı Maçlar":
                        title = f"{title} - {away_el.get_text(strip=True)}"

                    m3u_content.append(f'#EXTINF:-1 group-title="{group}",{title}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET}/')
                    m3u_content.append(f'{base_url}{cid}.m3u8')
                    count += 1
        
        if count == 0:
            print("⚠️ Sayfa yapısı okunamadı veya kanallar boş.")
        else:
            print(f"📝 {count} kanal eklendi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

    with open("betorspin.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    print("💾 Dosya kaydedildi.")

if __name__ == "__main__":
    main()
