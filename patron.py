import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
# Ana yönlendirici URL
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_redirected_url(source_url):
    """HTML içindeki window.location.replace veya href yönlendirmesini yakalar."""
    try:
        print(f"🔗 Yönlendirme adresi kontrol ediliyor: {source_url}")
        r = requests.get(source_url, headers=HEADERS, timeout=10, verify=False)
        r.encoding = "utf-8"
        
        # HTML içindeki yönlendirme linkini ara
        match = re.search(r'window\.location\.replace\(["\'](https?://[^"\']+)["\']\)', r.text)
        if not match:
            match = re.search(r'window\.location\.href\s*=\s*["\'](https?://[^"\']+)["\']', r.text)
            
        if match:
            final_url = match.group(1).rstrip('/')
            print(f"🚀 Hedef domain bulundu: {final_url}")
            return final_url
    except Exception as e:
        print(f"❌ Yönlendirme adresi alınamadı: {e}")
    return None

def resolve_base_url(active_domain):
    """Yayın sunucusunun base (stream) adresini bulur."""
    target = f"{active_domain}/channel.html?id=yayininat"
    try:
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        # Regex ile m3u8 yolunu içeren sunucuyu yakala
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
        
        alt_match = re.search(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site)/)', r.text)
        if alt_match:
            return alt_match.group(1).rstrip('/') + "/"
    except: 
        pass
    return None

def main():
    # 1. Adım: Yönlendirme sayfasından güncel domaini al
    active_domain = get_redirected_url(REDIRECT_SOURCE_URL)
    
    if not active_domain:
        print("❌ Aktif domain tespit edilemedi.")
        sys.exit()

    # 2. Adım: Yayın sunucusunu (base_url) tespit et
    base_url = resolve_base_url(active_domain)
    if not base_url:
        base_url = "https://9vy.d72577a9dd0ec19.sbs/" 
        print(f"⚠️ Yayın sunucusu otomatik bulunamadı, fallback: {base_url}")
    else:
        print(f"✅ Yayın sunucusu tespit edildi: {base_url}")

    fixed_channels = {
        "zirve": "beIN Sports 1 A", "trgoals": "beIN Sports 1 B", "yayin1": "beIN Sports 1 C",
        "patron": "beIN Sports 1 D", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
        "b4": "beIN Sports 4", "b5": "beIN Sports 5", "bm1": "beIN Sports 1 Max",
        "bm2": "beIN Sports 2 Max", "ss1": "S Sports 1", "ss2": "S Sports 2",
        "smarts": "Smart Sports", "sms2": "Smart Sports 2", "t1": "Tivibu Sports 1",
        "t2": "Tivibu Sports 2", "t3": "Tivibu Sports 3", "t4": "Tivibu Sports 4",
        "as": "A Spor", "trtspor": "TRT Spor", "trtspor2": "TRT Spor Yıldız",
        "trt1": "TRT 1", "atv": "ATV", "tv85": "TV8.5", "nbatv": "NBA TV",
        "eu1": "Euro Sport 1", "eu2": "Euro Sport 2",
        "ex1": "Tâbii 1", "ex2": "Tâbii 2", "ex3": "Tâbii 3", "ex4": "Tâbii 4"
    }

    try:
        print("📡 Canlı maçlar taranıyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        
        # 1. Canlı Maçlar
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

        # 2. Sabit Kanallar
        for cid, name in fixed_channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # Dosya ismi güncellendi
        file_name = "karsilasmalar4.m3u"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 BAŞARILI → {file_name} oluşturuldu.")

    except Exception as e:
        print(f"❌ Liste oluşturulurken hata: {e}")

if __name__ == "__main__":
    main()
