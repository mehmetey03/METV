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
    """Verilen API linkinden baseurl'i çeker."""
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
    # Önce direkt API'yi deneyelim çünkü en sağlamı o
    base_url = get_base_url(DIRECT_API_URL)
    
    # Eğer o çalışmazsa GitHack üzerinden bulmaya çalışalım
    if not base_url:
        try:
            r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
            found_domain = re.search(r'(https?://[^\s\'"]+)', r.text).group(1).rstrip('/')
            base_url = get_base_url(found_domain + "/domain.php")
        except:
            pass

    if not base_url:
        print("❌ HATA: Yayın sunucusu hiçbir kaynaktan alınamadı.")
        return

    # Maç listesinin çekileceği asıl site (Genellikle baseurl ile aynı kök domaindir)
    # Örn: https://obv.d72577a9dd0ec28.sbs/ -> https://obv.d72577a9dd0ec28.sbs
    match_source_site = "/".join(base_url.split("/")[:3])

    print(f"🚀 Yayın Sunucusu: {base_url}")
    print(f"📡 Maç Listesi Kaynağı: {match_source_site}")

    m3u_content = ["#EXTM3U"]
    
    # 2. CANLI MAÇLARI ÇEK
    try:
        resp = requests.get(match_source_site, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Daha geniş kapsamlı arama: hem div.channel-item hem de a[href*='id=']
        matches_found = False
        
        # Yöntem A: Div yapısı
        items = soup.find_all("div", class_="channel-item")
        for item in items:
            src = item.get("data-src", "") or ""
            cid_match = re.search(r'id=([^&]+)', src)
            if cid_match:
                cid = cid_match.group(1)
                teams = item.find_all("span", class_="team-name")
                name = " - ".join([t.get_text(strip=True) for t in teams]) if teams else cid
                
                m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                matches_found = True

        # Yöntem B: Eğer div bulunamadıysa linkleri tara
        if not matches_found:
            for a in soup.find_all("a", href=re.compile(r'id=')):
                cid_match = re.search(r'id=([^&]+)', a['href'])
                if cid_match:
                    cid = cid_match.group(1)
                    name = a.get_text(strip=True) or cid
                    m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
                    m3u_content.append(f'{base_url}{cid}/mono.m3u8')
    except Exception as e:
        print(f"⚠️ Maç listesi çekilirken hata: {e}")

    # 3. SABİT KANALLAR
    fixed_channels = {
        "patron": "beIN Sports 1", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
        "ss1": "S Sport 1", "ss2": "S Sport 2", "t1": "Tivibu Spor 1"
    }

    for cid, name in fixed_channels.items():
        m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_content.append(f'#EXTVLCOPT:http-referrer={match_source_site}/')
        m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    # DOSYAYA YAZ
    with open("karsilasmalar4.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    print(f"✅ karsilasmalar4.m3u başarıyla güncellendi. (Toplam {len(m3u_content)//4} kanal)")

if __name__ == "__main__":
    main()
