import requests
import re
import sys
import urllib3
import json
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "https://raw.githubusercontent.com/mehmetey03/goal/refs/heads/main/domain.txt"
# Yeni eklenen base_url kaynağı
BASE_URL_SOURCE = "https://patronsports2.cfd/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    return None

def get_dynamic_base_url():
    """Belirtilen PHP adresinden güncel baseurl değerini çeker."""
    try:
        print(f"📡 Base URL {BASE_URL_SOURCE} adresinden alınıyor...")
        r = requests.get(BASE_URL_SOURCE, headers=HEADERS, timeout=10, verify=False)
        # JSON verisini parse et: {"baseurl":"https:\/\/..."}
        data = r.json()
        base_url = data.get("baseurl", "").replace("\\/", "/") # Ters slaşları düzelt
        if base_url:
            print(f"✅ Dinamik Base URL bulundu: {base_url}")
            return base_url
    except Exception as e:
        print(f"⚠️ Dinamik base_url alınamadı: {e}")
    return "https://hz8.d72577a9dd0ec62.cfd/" # Hata olursa eski fallback

def main():
    active_domain = get_active_domain()
    if not active_domain:
        sys.exit("❌ Başlangıç domaini bulunamadı. GitHub linkini kontrol edin.")

    # Base URL'yi artık PHP dosyasından alıyoruz
    base_url = get_dynamic_base_url()

    # GÜNCEL KANAL LİSTESİ
    fixed_channels = {
        "zirve": "beIN Sports 1 A",
        "taraftarium": "beIN Sports 1 B",
        "patron": "beIN Sports 1 C",
        "b2": "beIN Sports 2",
        "b3": "beIN Sports 3",
        "b4": "beIN Sports 4",
        "b5": "beIN Sports 5",
        "bm1": "beIN Sports 1 Max",
        "bm2": "beIN Sports 2 Max",
        "ss1": "S Sports 1",
        "ss2": "S Sports 2",
        "smarts": "Smart Sports",
        "sms2": "Smart Sports 2",
        "t1": "Tivibu Sports 1",
        "t2": "Tivibu Sports 2",
        "t3": "Tivibu Sports 3",
        "t4": "Tivibu Sports 4",
        "as": "A Spor",
        "trtspor": "TRT Spor",
        "trtspor2": "TRT Spor Yıldız",
        "trt1": "TRT 1",
        "atv": "ATV",
        "tv85": "TV8.5",
        "nbatv": "NBA TV",
        "eu1": "Euro Sport 1",
        "eu2": "Euro Sport 2",
        "ex1": "Tâbii 1",
        "ex2": "Tâbii 2",
        "ex3": "Tâbii 3",
        "ex4": "Tâbii 4",
        "ex5": "Tâbii 5",
        "ex6": "Tâbii 6",
        "ex7": "Tâbii 7",
        "ex8": "Tâbii 8"
    }

    try:
        print("📡 Canlı maçlar taranıyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        
        # 1. Canlı Maçlar Bölümü
        matches_tab = soup.find(id="matches-tab")
        if matches_tab:
            for a in matches_tab.find_all("a", href=re.compile(r'id=')):
                cid_match = re.search(r'id=([^&]+)', a["href"])
                name = a.find(class_="channel-name")
                status = a.find(class_="channel-status")
                if cid_match and name:
                    cid = cid_match.group(1)
                    title = f"{status.get_text(strip=True) if status else 'CANLI'} | {name.get_text(strip=True)}"
                    m3u_content.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                    m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # 2. Sabit Kanallar Bölümü
        for cid, name in fixed_channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        with open("karsilasmalar2.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 BAŞARILI → karsilasmalar2.m3u hazır. ({len(m3u_content)//4} kanal eklendi)")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
