import requests
import re
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
    """Verilen API linkinden baseurl'i (yayın sunucusu) çeker."""
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
    # 1. YAYIN SUNUCUSUNU (baseurl) BUL
    base_url = get_base_url(DIRECT_API_URL)
    
    # Direkt API çalışmazsa Githack üzerinden yönlendirmeyi dene
    if not base_url:
        try:
            r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
            # HTML içindeki URL'yi regex ile bul (örn: https://site.com)
            found_domain = re.search(r'(https?://[^\s\'"]+)', r.text).group(1).rstrip('/')
            base_url = get_base_url(found_domain + "/domain.php")
        except:
            pass

    if not base_url:
        print("❌ HATA: Yayın sunucusu hiçbir kaynaktan alınamadı.")
        return

    # Maç listesinin çekileceği ana site kök dizini
    match_source_site = "/".join(base_url.split("/")[:3])

    print(f"🚀 Yayın Sunucusu: {base_url}")
    print(f"📡 Maç Listesi Kaynağı: {match_source_site}")

    m3u_content = ["#EXTM3U"]
    
    # 2. CANLI MAÇLARI VE RESİMLERİ ÇEK
    try:
        resp = requests.get(match_source_site, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        items = soup.find_all("div", class_="channel-item")
        for item in items:
            # ID Çekme (data-src veya onclick içinden)
            src = item.get("data-src", "") or item.get("onclick", "")
            cid_match = re.search(r'id=([^&\'"]+)', src)
            
            if cid_match:
                cid = cid_match.group(1)
                
                # Takım isimlerini al
                teams = item.find_all("span", class_="team-name")
                name = " - ".join([t.get_text(strip=True) for t in teams]) if teams else cid
                
                # Saat ve Lig bilgisini isme ekleyelim (Opsiyonel)
                m_time = item.find("span", class_="match-time")
                time_str = f"[{m_time.get_text(strip=True)}] " if m_time else ""
                full_name = f"{time_str}{name}"

                # --- LOGO AYIKLAMA ---
                # HTML'deki img etiketini bul
                img_tag = item.find("img")
                logo_url = ""
                if img_tag:
                    # Bazı siteler 'src' yerine 'data-src' kullanır, ikisine de bakalım
                    logo_url = img_tag.get("src") or img_tag.get("data-src") or ""
                    
                    # Eğer logo linki eksikse (relative path), site adresini başına ekle
                    if logo_url and not logo_url.startswith("http"):
                        logo_url = match_source_site.rstrip('/') + "/" + logo_url.lstrip('/')

                # M3U Formatına Ekle
                m3u_content.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="CANLI MAÇLAR",{full_name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    except Exception as e:
        print(f"⚠️ Maç listesi çekilirken hata oluştu: {e}")

    # 3. SABİT KANALLAR (Manuel Logo Eklemek İstersen Burayı Düzenle)
    # Format: "cid": ["Kanal Adı", "Logo_URL"]
    fixed_channels = {
        "patron": ["beIN Sports 1", "https://i.ibb.co/logo1.png"],
        "b2": ["beIN Sports 2", ""],
        "ss1": ["S Sport 1", ""],
        "t1": ["Tivibu Spor 1", ""]
    }

    for cid, info in fixed_channels.items():
        name, logo = info
        m3u_content.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="7/24 Kanallar",{name}')
        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
        m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    # DOSYAYA YAZ
    filename = "karsilasmalar4.m3u"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    print(f"✅ {filename} başarıyla güncellendi. (Toplam {len(m3u_content)//4} kanal)")

if __name__ == "__main__":
    main()
