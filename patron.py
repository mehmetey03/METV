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

# Daha güçlü Header seti
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
}

def get_main_site_url():
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
        match = re.search(r'(https?://[^\s\'"]+)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except: return None
    return None

def get_base_url():
    try:
        r = requests.get(DIRECT_API_URL, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            data = r.json()
            base = data.get("baseurl", "")
            return base.replace("\\", "").strip().rstrip('/') + "/"
    except: return None
    return None

def main():
    main_site = get_main_site_url()
    base_url = get_base_url()

    if not main_site or not base_url:
        print(f"❌ Kaynak hatası!")
        return

    print(f"📡 Ana Site: {main_site}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    m3u_content = ["#EXTM3U"]
    
    try:
        # Session kullanarak çerezleri tutalım
        session = requests.Session()
        # İlk istek: Çerezleri almak için
        session.get(main_site, headers=HEADERS, timeout=15, verify=False)
        
        # İkinci istek: Gerçek içeriği çekmek için
        resp = session.get(main_site, headers=HEADERS, timeout=15, verify=False)
        
        # Debug: Eğer 0 maç gelirse HTML'i incelemek için (Opsiyonel)
        # with open("debug.html", "w", encoding="utf-8") as f: f.write(resp.text)

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # HTML'de hem 'channel-item' hem de alternatif maç yapılarını arayalım
        items = soup.find_all("div", class_=re.compile(r"channel-item|match-card|match-item"))
        found_count = 0

        for item in items:
            # ID Bulma (onclick, data-src veya href içinden)
            item_str = str(item)
            cid_match = re.search(r'id=([^&\'"\s<>]+)', item_str)
            
            if cid_match:
                cid = cid_match.group(1)
                
                # Takım ve Bilgiler
                t_names = [t.get_text(strip=True) for t in item.find_all("span", class_="team-name")]
                league = item.find("span", class_="league-text")
                m_time = item.find("span", class_="match-time")
                
                name = " - ".join(t_names) if t_names else f"Kanal {cid}"
                league_txt = f"[{league.get_text(strip=True)}] " if league else ""
                time_txt = f" ({m_time.get_text(strip=True)})" if m_time else ""

                # Resim/Logo Ayıkla
                img = item.find("img")
                logo = ""
                if img:
                    logo = img.get("src") or img.get("data-src") or ""
                    if logo and not logo.startswith("http"):
                        logo = f"{main_site}/{logo.lstrip('/')}"

                # M3U Formatı
                m3u_content.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="CANLI MAÇLAR",{league_txt}{name}{time_txt}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={main_site}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                found_count += 1

        # Sabit Kanallar
        fixed = {"patron": "beIN Sports 1", "b2": "beIN Sports 2", "ss1": "S Sport 1"}
        for f_id, f_name in fixed.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 KANALLAR",{f_name}')
            m3u_content.append(f'{base_url}{f_id}/mono.m3u8')

        with open("karsilasmalar4.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        
        print(f"✅ Tamamlandı! {found_count} canlı maç + {len(fixed)} sabit kanal eklendi.")

    except Exception as e:
        print(f"⚠️ Hata: {e}")

if __name__ == "__main__":
    main()
