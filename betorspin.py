import requests
import re
import urllib3
import os
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET = "https://63betorspintv.live"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET + "/"
}

def main():
    session = requests.Session()
    m3u_content = ["#EXTM3U"]
    base_url = None

    try:
        print(f"📡 {TARGET} taranıyor...")
        # Ana sayfaya gir ve çerezleri al
        session.get(TARGET, headers=HEADERS, timeout=15, verify=False)
        
        # Yayın sunucusunu bulmak için kanal sayfasını tara
        r_chan = session.get(f"{TARGET}/channel?id=yayinzirve", headers=HEADERS, timeout=15, verify=False)
        
        # Regex ile .sbs, .live vb. biten m3u8 sunucularını ara
        found_urls = re.findall(r'https?://[a-z0-9.-]+\.(?:sbs|xyz|live|me|site|club|net|pw)/', r_chan.text)
        for link in found_urls:
            if not any(x in link for x in ["gstatic", "google", "hizliresim", "doubleclick"]):
                base_url = link
                break

        if base_url:
            print(f"✅ Sunucu bulundu: {base_url}")
            r_main = session.get(TARGET, headers=HEADERS, timeout=15, verify=False)
            soup = BeautifulSoup(r_main.text, "html.parser")
            
            containers = soup.find_all("div", id=["matches-content", "channels-content"])
            for box in containers:
                group = "Canlı Maçlar" if box.get('id') == "matches-content" else "TV Kanalları"
                for a in box.find_all("a", href=re.compile(r'id=')):
                    cid = re.search(r'id=([^&]+)', a["href"]).group(1)
                    name_div = a.find(class_="home") or a.find(class_="event")
                    title = name_div.get_text(strip=True) if name_div else cid
                    
                    m3u_content.append(f'#EXTINF:-1 group-title="{group}",{title}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET}/')
                    m3u_content.append(f'{base_url}{cid}.m3u8')
        else:
            print("⚠️ Sunucu bulunamadı, boş dosya korunuyor.")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

    # HATA ALSA BİLE DOSYAYI OLUŞTUR (Git hatasını önlemek için)
    with open("betorspin.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    print("📝 betorspin.m3u8 dosyası güncellendi.")

if __name__ == "__main__":
    main()
