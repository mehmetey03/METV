import requests
import re
import sys
import urllib3
import json
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
# Ana domain bilgisini aldığımız yer
REDIRECT_SOURCE = "https://raw.githubusercontent.com/mehmetey03/goal/refs/heads/main/domain.txt"
# M3U8 linkleri için base url kaynağı
BASE_URL_SOURCE = "https://patronsports2.cfd/domain.php"

# Yeni veri kaynakları
MATCHES_ENDPOINT = "https://data-reality.com/matches.php"
CHANNELS_ENDPOINT = "https://data-reality.com/channels.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sanstv2.live/"
}

def get_active_domain():
    """GitHub üzerindeki domain.txt dosyasından güncel adresi çeker."""
    try:
        print(f"🔍 Aktif domain {REDIRECT_SOURCE} adresinden alınıyor...")
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        domain = r.text.strip().rstrip('/')
        if domain.startswith("http"):
            print(f"✅ Aktif domain bulundu: {domain}")
            return domain
        else:
            match = re.search(r'(https?://[^\s"<]+)', r.text)
            if match:
                return match.group(1).rstrip('/')
    except Exception as e:
        print(f"❌ Domain çekilirken hata: {e}")
    return "https://www.sanstv2.live" # Fallback

def get_dynamic_base_url():
    """Belirtilen PHP adresinden güncel baseurl değerini çeker."""
    try:
        print(f"📡 Base URL {BASE_URL_SOURCE} adresinden alınıyor...")
        r = requests.get(BASE_URL_SOURCE, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "").replace("\\/", "/")
        if base_url:
            print(f"✅ Dinamik Base URL bulundu: {base_url}")
            return base_url
    except Exception as e:
        print(f"⚠️ Dinamik base_url alınamadı: {e}")
    return "https://hz8.d72577a9dd0ec62.cfd/"

def main():
    active_domain = get_active_domain()
    base_url = get_dynamic_base_url()
    
    m3u_content = ["#EXTM3U"]

    # 1. CANLI MAÇLARI TARA (matches.php)
    try:
        print(f"📡 Canlı maçlar taranıyor: {MATCHES_ENDPOINT}")
        resp = requests.get(MATCHES_ENDPOINT, headers=HEADERS, timeout=15, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        matches = soup.find_all("a", class_="single-match")
        for match in matches:
            href = match.get("href", "")
            cid_match = re.search(r'id=([^&]+)', href)
            
            if cid_match:
                cid = cid_match.group(1)
                
                # Takım ve etkinlik bilgilerini ayıkla
                home = match.find(class_="home").get_text(strip=True) if match.find(class_="home") else ""
                away = match.find(class_="away").get_text(strip=True) if match.find(class_="away") else ""
                event = match.find(class_="event").get_text(strip=True) if match.find(class_="event") else ""
                time_info = match.find(class_="date").get_text(strip=True) if match.find(class_="date") else "CANLI"
                
                title = f"{time_info} | {home} - {away} ({event})"
                
                m3u_content.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
    except Exception as e:
        print(f"❌ Maçlar taranırken hata: {e}")

    # 2. SABİT KANALLARI TARA (channels.php)
    try:
        print(f"📡 Sabit kanallar taranıyor: {CHANNELS_ENDPOINT}")
        resp = requests.get(CHANNELS_ENDPOINT, headers=HEADERS, timeout=15, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        
        channels = soup.find_all("a", class_="single-match")
        for channel in channels:
            href = channel.get("href", "")
            cid_match = re.search(r'id=([^&]+)', href)
            
            if cid_match:
                cid = cid_match.group(1)
                # Kanal adını al (home class'ı içinde bein sports vb. yazıyor)
                channel_name = channel.find(class_="home").get_text(strip=True) if channel.find(class_="home") else cid.upper()
                
                m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{channel_name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
    except Exception as e:
        print(f"❌ Kanallar taranırken hata: {e}")

    # DOSYAYA YAZ
    with open("karsilasmalar5.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))

    print(f"---")
    print(f"🏁 BAŞARILI → karsilasmalar5.m3u oluşturuldu.")
    print(f"📊 Toplam Satır: {len(m3u_content)}")

if __name__ == "__main__":
    main()
