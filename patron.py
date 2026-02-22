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
# Yedek API kontrol noktası (GitHack patlarsa veya boş dönerse)
DIRECT_API_URL = "https://patronsports1.cfd/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_active_domain():
    """GitHack üzerinden güncel giriş adresini esnek bir şekilde arar."""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
        match = re.search(r'(https?://[^\s\'"]+)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except:
        pass
    return None

def get_base_url(domain_url):
    """Verilen domain üzerinden domain.php JSON verisini çeker."""
    try:
        api_path = domain_url.rstrip('/') + "/domain.php"
        r = requests.get(api_path, headers=HEADERS, timeout=10, verify=False)
        # Yanıtın boş olmadığını kontrol et
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            base = data.get("baseurl", "")
            if base:
                return base.replace("\\", "").strip().rstrip('/') + "/"
    except:
        pass
    return None

def main():
    # 1. ADIM: GitHack'ten siteyi bul
    active_domain = get_active_domain()
    base_url = None

    if active_domain:
        print(f"📡 GitHack üzerinden bulunan site: {active_domain}")
        base_url = get_base_url(active_domain)

    # 2. ADIM: Eğer GitHack'ten gelen site boşsa veya API'si çalışmıyorsa DIRECT_API kullan
    if not base_url:
        print("⚠️ GitHack sitesi cevap vermedi, doğrudan API kontrol ediliyor...")
        # API'nin kendi domainini ayıkla (https://patronsports1.cfd)
        active_domain = "/".join(DIRECT_API_URL.split("/")[:3])
        base_url = get_base_url(active_domain)

    # 3. ADIM: Hala bulunamadıysa dur (Kesinlikle sabit URL yazılmadı)
    if not base_url:
        print("❌ HATA: Hiçbir kaynaktan yayın sunucusu (baseurl) alınamadı.")
        return

    print(f"✅ Aktif Site: {active_domain}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    m3u_content = ["#EXTM3U"]
    
    # 4. ADIM: Canlı Maçları Çek
    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        match_items = soup.find_all("div", class_="channel-item")
        
        for item in match_items:
            src = item.get("data-src", "")
            cid_match = re.search(r'id=([^&]+)', src)
            if not cid_match: continue
            cid = cid_match.group(1)

            # Bilgileri parse et
            teams = item.find_all("span", class_="team-name")
            home = teams[0].get_text(strip=True) if len(teams) > 0 else "Kanal"
            away = teams[1].get_text(strip=True) if len(teams) > 1 else ""
            league = item.find("span", class_="league-text").get_text(strip=True) if item.find("span", class_="league-text") else "Spor"
            mtime = item.find("span", class_="match-time").get_text(strip=True) if item.find("span", class_="match-time") else ""

            display_name = f"{home} - {away} [{mtime}] ({league})".strip()
            
            m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{display_name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            
    except:
        print("⚠️ Maç listesi çekilirken bir hata oluştu.")

    # 5. ADIM: Sabit Kanallar
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
        print(f"📂 karsilasmalar4.m3u başarıyla güncellendi.")

if __name__ == "__main__":
    main()
