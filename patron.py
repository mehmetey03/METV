import requests
import re
import urllib3
from bs4 import BeautifulSoup

# SSL ve Header Ayarları
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Kaynaklar
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DIRECT_API_URL = "https://patronsports1.cfd/domain.php"

def get_base_url(api_link):
    try:
        r = requests.get(api_link, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            return r.json().get("baseurl", "").replace("\\", "").strip().rstrip('/') + "/"
    except: return None

def main():
    base_url = get_base_url(DIRECT_API_URL)
    if not base_url:
        # Githack üzerinden yedek deneme
        try:
            r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
            found = re.search(r'(https?://[^\s\'"]+)', r.text).group(1)
            base_url = get_base_url(found.rstrip('/') + "/domain.php")
        except: pass

    if not base_url:
        print("❌ Sunucu bulunamadı.")
        return

    match_source_site = "/".join(base_url.split("/")[:3])
    m3u_content = ["#EXTM3U"]

    try:
        # Siteye bağlan ve HTML'i al
        resp = requests.get(match_source_site, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # HTML İÇİNDEKİ TÜM MAÇ KARTLARINI TARA
        # Hem 'channel-item' hem de alternatif 'match-card' yapılarını kontrol et
        items = soup.find_all("div", class_=["channel-item", "match-item"])
        
        for item in items:
            # 1. Link/ID Bulma (data-src, href veya onclick)
            data_str = str(item)
            cid_match = re.search(r'id=([^&\'"\s]+)', data_str)
            if not cid_match: continue
            cid = cid_match.group(1)

            # 2. Takım İsimleri
            t_names = [t.get_text(strip=True) for t in item.find_all("span", class_="team-name")]
            match_name = " vs ".join(t_names) if t_names else cid

            # 3. Logo/Resim Yakalama
            img = item.find("img")
            logo = ""
            if img:
                logo = img.get("data-src") or img.get("src") or ""
                if logo and not logo.startswith("http"):
                    logo = match_source_site.rstrip('/') + "/" + logo.lstrip('/')

            # 4. Lig ve Saat (Ekstra Bilgi)
            l_text = item.find("span", class_="league-text")
            league = f"[{l_text.get_text(strip=True)}] " if l_text else ""

            # M3U Ekleme
            m3u_content.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="CANLI MAÇLAR",{league}{match_name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    except Exception as e:
        print(f"⚠️ Hata: {e}")

    # Sabit Kanallar
    fixed = {"patron": "beIN Sports 1", "b2": "beIN Sports 2", "ss1": "S Sport 1"}
    for c_id, c_name in fixed.items():
        m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{c_name}')
        m3u_content.append(f'{base_url}{c_id}/mono.m3u8')

    with open("karsilasmalar4.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    print(f"✅ Bitti! Toplam {len(m3u_content)//4} kanal/maç dosyaya eklendi.")

if __name__ == "__main__":
    main()
