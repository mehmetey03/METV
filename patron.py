import requests
import re
import os
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_redirected_url():
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15, verify=False)
        match = re.search(r'replace\(["\'](https?://[^"\']+)["\']\)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except Exception as e:
        print(f"Domain çekme hatası: {e}")
    return "https://hepbetspor16.cfd" # Fallback

def resolve_base_url(active_domain):
    try:
        # Örnek bir kanal üzerinden sunucuyu bul
        r = requests.get(f"{active_domain}/ch.html?id=b2", headers=HEADERS, timeout=10, verify=False)
        match = re.search(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site|cfd))/', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
    except:
        pass
    return "https://obv.d72577a9dd0ec28.sbs/" # Senin verdiğin çalışan sunucu

def main():
    active_domain = get_redirected_url()
    base_url = resolve_base_url(active_domain)
    
    print(f"Aktif Domain: {active_domain}")
    print(f"Yayın Sunucusu: {base_url}")

    m3u_content = ["#EXTM3U"]
    
    # Sabit Kanal Listesi
    fixed_channels = {
        "patron": "beIN Sports 1", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
        "ss1": "S Sport 1", "ss2": "S Sport 2", "trtspor": "TRT Spor"
    }

    # 1. Web sitesinden canlı maçları çekmeyi dene
    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        # href içinde 'id=' olan tüm linkleri tara
        for a in soup.find_all("a", href=re.compile(r'id=')):
            cid_match = re.search(r'id=([^&]+)', a["href"])
            if cid_match:
                cid = cid_match.group(1)
                name = a.get_text(strip=True) or cid
                m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
    except Exception as e:
        print(f"Maç listesi çekilemedi: {e}")

    # 2. Sabit kanalları ekle (Eğer daha önce eklenmediyse)
    for cid, name in fixed_channels.items():
        link = f"{base_url}{cid}/mono.m3u8"
        if link not in "\n".join(m3u_content):
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{link}')

    # DOSYA OLUŞTURMA (Git hatasını önlemek için en kritik yer)
    file_name = "karsilasmalar4.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    if os.path.exists(file_name):
        print(f"✅ {file_name} başarıyla oluşturuldu. Boyut: {os.path.getsize(file_name)} byte")
    else:
        print("❌ Dosya oluşturulamadı!")

if __name__ == "__main__":
    main()
