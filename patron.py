import requests
import re
import os
import urllib3
import json
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAK ADRESLERİ
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DIRECT_API_URL = "https://patronsports1.cfd/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_base_url(api_link):
    try:
        r = requests.get(api_link, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            base = data.get("baseurl", "")
            if base:
                return base.replace("\\", "").strip().rstrip('/') + "/"
    except:
        pass
    return None

def main():
    # 1. YAYIN SUNUCUSUNU BUL
    base_url = get_base_url(DIRECT_API_URL)
    
    if not base_url:
        try:
            r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
            found_domain = re.search(r'(https?://[^\s\'"]+)', r.text).group(1).rstrip('/')
            base_url = get_base_url(found_domain + "/domain.php")
        except:
            pass

    if not base_url:
        print("❌ HATA: Yayın sunucusu alınamadı.")
        return

    # Gönderdiğin HTML'in olduğu ana sayfa
    match_source_site = "https://patronsports1.cfd"

    print(f"🚀 Yayın Sunucusu: {base_url}")
    print(f"📡 Kanal Kaynağı: {match_source_site}")

    m3u_content = ["#EXTM3U"]
    
    # 2. KANALLARI VE RESİMLERİ ÇEK
    try:
        resp = requests.get(match_source_site, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Gönderdiğin HTML yapısındaki .channel-item sınıflarını bul
        items = soup.find_all("div", class_="channel-item")
        
        count = 0
        for item in items:
            # ID Çekme (data-src içinden: /ch.html?id=patron)
            src = item.get("data-src", "")
            cid_match = re.search(r'id=([^&]+)', src)
            if not cid_match: continue
            cid = cid_match.group(1)

            # Kanal İsmi Çekme (.channel-name-text içinden)
            name_tag = item.find("span", class_="channel-name-text")
            name = name_tag.get_text(strip=True) if name_tag else cid.upper()

            # Resim (Logo) Çekme (.channel-logo-right içinden)
            img_tag = item.find("img", class_="channel-logo-right")
            logo_url = img_tag.get("src", "") if img_tag else ""

            # M3U Formatına Ekle
            m3u_content.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="PATRON TV",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            count += 1

    except Exception as e:
        print(f"⚠️ Kanal listesi çekilirken hata: {e}")

    # DOSYAYA YAZ
    if count > 0:
        with open("karsilasmalar4.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"✅ karsilasmalar4.m3u başarıyla güncellendi. (Toplam {count} kanal ve logo eklendi)")
    else:
        print("❌ HATA: Hiç kanal bulunamadı, HTML yapısı değişmiş olabilir.")

if __name__ == "__main__":
    main()
