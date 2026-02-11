import requests
import re
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "https://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_active_domain():
    try:
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        match = re.search(r'URL=(https?://[^">]+)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except: pass
    return "https://hepbetspor5.cfd"

def resolve_base_url(active_domain):
    # 'patron' kanalı üzerinden m3u8 sunucusunu bul
    target = f"{active_domain}/ch.html?id=patron"
    try:
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
    except: pass
    return "https://9vy.d72577a9dd0ec19.sbs/"

def main():
    active_domain = get_active_domain()
    base_url = resolve_base_url(active_domain)
    
    print(f"🔗 Aktif Domain: {active_domain}")
    print(f"📡 Yayın Sunucusu: {base_url}")

    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        channel_count = 0

        # --- YENİ YAPI: div.channel-item TARAMA ---
        # Sitedeki tüm kanal kutularını bul
        items = soup.find_all("div", class_="channel-item")

        for item in items:
            # ID bilgisini data-src içinden al (/ch.html?id=xxx)
            data_src = item.get("data-src", "")
            cid_match = re.search(r'id=([^&]+)', data_src)
            
            if cid_match:
                cid = cid_match.group(1)
                
                # Kanal ismini 'channel-name-text' class'ından al
                name_tag = item.find(class_="channel-name-text")
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    
                    # M3U Formatına Ekle
                    m3u_content.append(f'#EXTINF:-1 group-title="Canlı Kanallar",{name}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                    m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                    channel_count += 1

        # Dosyaya yaz
        with open("karsilasmalar3.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 Başarılı! 'karsilasmalar3.m3u' oluşturuldu.")
        print(f"📊 Toplam {channel_count} kanal ve maç listeye eklendi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
