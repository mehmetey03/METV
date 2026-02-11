import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "https://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def get_active_domain():
    try:
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        match = re.search(r'URL=(https?://[^">]+)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except: pass
    return "https://hepbetspor5.cfd"

def resolve_base_url(active_domain):
    # Belirttiğin 'patron' kanalı üzerinden sunucuyu doğrula
    target = f"{active_domain}/ch.html?id=patron"
    try:
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        # Yeni linklerde sunucu adresini yakala
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
    except: pass
    return "https://9vy.d72577a9dd0ec19.sbs/"

def main():
    active_domain = get_active_domain()
    base_url = resolve_base_url(active_domain)
    
    print(f"🔗 Aktif Domain: {active_domain}")
    print(f"📡 Yayın Sunucusu: {base_url}")

    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        
        # --- 1. CANLI MAÇLAR TARAMA (Daha Geniş Kapsamlı) ---
        # Sitedeki tüm 'id=' içeren linkleri tara (hem matches-tab hem genel)
        all_links = soup.find_all("a", href=re.compile(r'id='))
        match_count = 0

        for a in all_links:
            href = a["href"]
            cid_match = re.search(r'id=([^&]+)', href)
            
            if cid_match:
                cid = cid_match.group(1)
                
                # Kanal adını bulmaya çalış (farklı class isimlerini dene)
                name_tag = a.find(class_="channel-name") or a.find(class_="name") or a.find("span")
                status_tag = a.find(class_="channel-status") or a.find(class_="status")
                
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    status = status_tag.get_text(strip=True) if status_tag else "CANLI"
                    
                    # Eğer kanal zaten sabit listede yoksa ekle (tekrarı önlemek için)
                    m3u_content.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{status} | {name}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                    # ch.html veya channel.html fark etmeksizin stream linkini oluştur
                    m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                    match_count += 1

        # --- 2. SABİT KANAL LİSTESİ (Güncellenmiş ID'ler) ---
        fixed_channels = {
            "patron": "Patron TV (beIN 1)",
            "zirve": "Zirve TV",
            "trgoals": "TR Goals",
            "b2": "beIN Sports 2",
            "b3": "beIN Sports 3",
            "ss1": "S Sports 1",
            "ss2": "S Sports 2",
            "t1": "Tivibu Spor 1",
            "tv85": "TV8.5",
            "trtspor": "TRT Spor"
        }

        for cid, name in fixed_channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        with open("karsilasmalar3.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 Başarılı! 'karsilasmalar3.m3u' oluşturuldu.")
        print(f"📊 Toplam {match_count} maç ve {len(fixed_channels)} sabit kanal eklendi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
