import requests
import re
import os
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# AYARLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
# Senin verdiğin ve çalışan kesin sunucu adresi
FIXED_STREAM_SERVER = "https://obv.d72577a9dd0ec28.sbs/" 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_redirected_url():
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15, verify=False)
        match = re.search(r'replace\(["\'](https?://[^"\']+)["\']\)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except:
        pass
    return "https://hepbetspor16.cfd"

def main():
    active_domain = get_redirected_url()
    # Otomatik bulmak yerine senin verdiğin kesin çalışan sunucuyu kullanıyoruz
    base_url = FIXED_STREAM_SERVER 
    
    print(f"🚀 Aktif Domain: {active_domain}")
    print(f"📡 Yayın Sunucusu (Sabitlendi): {base_url}")

    m3u_content = ["#EXTM3U"]
    
    # 1. Web sitesindeki butonları tara
    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Sitedeki tüm kanal linklerini yakala
        for a in soup.find_all("a", href=re.compile(r'id=')):
            cid_match = re.search(r'id=([^&]+)', a["href"])
            if cid_match:
                cid = cid_match.group(1)
                # İsimlendirme: Eğer içerde class="channel-name" varsa al, yoksa temiz metni al
                name_tag = a.find(class_="channel-name")
                name = name_tag.get_text(strip=True) if name_tag else a.get_text(strip=True)
                
                if not name: name = cid # Boşsa ID'yi yaz

                m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                # Örn: https://obv.d72577a9dd0ec28.sbs/patron/mono.m3u8
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                
    except Exception as e:
        print(f"❌ Hata: {e}")

    # DOSYA OLUŞTURMA
    file_name = "karsilasmalar4.m3u"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    if os.path.exists(file_name):
        print(f"✅ {file_name} oluşturuldu ({os.path.getsize(file_name)} byte).")
        print(f"Örnek Link: {base_url}patron/mono.m3u8")

if __name__ == "__main__":
    main()
