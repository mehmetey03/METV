import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL sertifika uyarılarını görmezden gel
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "https://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_active_domain():
    """GitHub üzerindeki yönlendirme sayfasından güncel domaini çeker."""
    try:
        print(f"🔍 Güncel adres {REDIRECT_SOURCE} üzerinden sorgulanıyor...")
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        # URL=https://... yapısını yakala
        match = re.search(r'URL=(https?://[^">]+)', r.text)
        if match:
            domain = match.group(1).rstrip('/')
            print(f"✅ Aktif domain bulundu: {domain}")
            return domain
    except Exception as e:
        print(f"❌ Domain çekilemedi: {e}")
    return None

def resolve_base_url(active_domain):
    """Yayınların barındığı CDN sunucusunu tespit eder."""
    try:
        # Örnek bir kanal üzerinden sunucu adresini bul
        target = f"{active_domain}/channel.html?id=yayininat"
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        
        # m3u8 uzantısından önceki sunucu adresini yakala
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
    except:
        pass
    # Varsayılan fallback sunucu
    return "https://9vy.d72577a9dd0ec19.sbs/"

def main():
    # 1. Adım: Güncel domaini al
    active_domain = get_active_domain()
    if not active_domain:
        # Eğer GitHub hata verirse senin verdiğin adresi manuel kullan
        active_domain = "https://hepbetspor5.cfd"
        print(f"⚠️ GitHub'dan alınamadı, manuel adres kullanılıyor: {active_domain}")

    # 2. Adım: Yayın sunucusunu bul
    base_url = resolve_base_url(active_domain)
    print(f"📡 Yayın Sunucusu: {base_url}")

    # 3. Adım: Sayfayı tara ve M3U oluştur
    try:
        print("⚽ Canlı maçlar ve kanallar taranıyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        
        # Canlı Maçlar Bölümü
        matches_tab = soup.find(id="matches-tab")
        count = 0
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
                    count += 1

        # Sabit Kanallar Listesi
        fixed_channels = {
            "zirve": "beIN Sports 1", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
            "ss1": "S Sports 1", "ss2": "S Sports 2", "t1": "Tivibu Spor 1",
            "as": "A Spor", "trtspor": "TRT Spor", "tv85": "TV8.5"
        }

        for cid, name in fixed_channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # Dosyayı kaydet
        with open("karsilasmalar3.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 Başarılı! 'karsilasmalar3.m3u' dosyası oluşturuldu. ({count} maç eklendi)")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
