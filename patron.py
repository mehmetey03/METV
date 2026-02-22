import requests
import re
import os
import urllib3
import json
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAK ADRESLERİ
# 1. Adım: Buradan ana sitenin ne olduğunu buluruz
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
# 2. Adım: Bulduğumuz sitenin sonuna bu yolu ekleyip baseurl'i çekeriz
DOMAIN_API_PATH = "/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_active_domain():
    """GitHack üzerinden güncel giriş adresini esnek bir şekilde arar."""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15, verify=False)
        # Daha esnek bir regex: Tırnak içindeki http ile başlayan ilk URL'yi al
        match = re.search(r'(https?://[^\s\'"]+)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except Exception as e:
        print(f"⚠️ GitHack'ten domain çekilemedi: {e}")
    return None

def get_base_url(domain):
    """Bulunan site üzerinden domain.php'ye gidip baseurl JSON verisini alır."""
    try:
        api_url = f"{domain}{DOMAIN_API_PATH}"
        r = requests.get(api_url, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        # JSON içindeki baseurl'i temizle
        base = data.get("baseurl", "")
        if base:
            return base.replace("\\", "").strip().rstrip('/') + "/"
    except Exception as e:
        print(f"⚠️ {domain}{DOMAIN_API_PATH} üzerinden baseurl alınamadı: {e}")
    return None

def main():
    # 1. ZİNCİR: GitHack -> Aktif Site
    active_domain = get_active_domain()
    if not active_domain:
        print("❌ HATA: GitHack üzerinden aktif domain bulunamadı.")
        return

    # 2. ZİNCİR: Aktif Site -> domain.php -> BaseURL
    base_url = get_base_url(active_domain)
    if not base_url:
        print("❌ HATA: API üzerinden yayın sunucusu (baseurl) alınamadı.")
        return
    
    print(f"✅ Aktif Domain: {active_domain}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    m3u_content = ["#EXTM3U"]
    
    # 3. ZİNCİR: Maçları ve Kanalları Oluştur
    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        match_items = soup.find_all("div", class_="channel-item")
        
        for item in match_items:
            src = item.get("data-src", "")
            cid_match = re.search(r'id=([^&]+)', src)
            if not cid_match: continue
            cid = cid_match.group(1)

            # Bilgi ayıklama
            teams = item.find_all("span", class_="team-name")
            home = teams[0].get_text(strip=True) if len(teams) > 0 else "Kanal"
            away = teams[1].get_text(strip=True) if len(teams) > 1 else ""
            league = item.find("span", class_="league-text").get_text(strip=True) if item.find("span", class_="league-text") else "Canlı"
            mtime = item.find("span", class_="match-time").get_text(strip=True) if item.find("span", class_="match-time") else ""

            display_name = f"{home} - {away} [{mtime}] ({league})".strip()
            
            m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{display_name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            
    except Exception as e:
        print(f"⚠️ Maç listesi oluşturma hatası: {e}")

    # Sabit Kanallar (Hepsi dinamik base_url kullanır)
    fixed_channels = {
        "patron": "beIN Sports 1", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
        "ss1": "S Sport 1", "ss2": "S Sport 2", "t1": "Tivibu Spor 1"
    }

    for cid, name in fixed_channels.items():
        m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
        m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    # Dosyaya Yaz
    if len(m3u_content) > 1:
        with open("karsilasmalar4.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        print(f"📂 karsilasmalar4.m3u güncellendi. ({len(m3u_content)//4} kanal)")

if __name__ == "__main__":
    main()
