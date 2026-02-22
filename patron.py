import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://hepbetspor16.cfd/"
}

def get_base_url():
    """Yayın sunucusunu API üzerinden almayı dener."""
    try:
        r = requests.get("https://patronsports1.cfd/domain.php", headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except:
        return "https://obv.d72577a9dd0ec28.sbs/"

def main():
    active_domain = "https://hepbetspor16.cfd"
    base_url = get_base_url()
    
    print(f"📡 Kaynak Site: {active_domain}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    # Sabit Kanal Listesi (Senin istediğin 7/24 kanallar)
    fixed_channels = {
        "b1": "beIN Sports 1",
        "b2": "beIN Sports 2",
        "b3": "beIN Sports 3",
        "ss1": "S Sports 1",
        "ss2": "S Sports 2",
        "t1": "Tivibu Sports 1",
        "as": "A Spor",
        "trtspor": "TRT Spor"
    }

    try:
        print("🔍 Canlı maçlar taranıyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=15, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        match_count = 0

        # CANLI MAÇLARI BULMA (Senin gönderdiğin yeni mantığa göre)
        # Sitedeki tüm linkleri (<a>) gez, içinde 'id=' olanları ve maç ismi taşıyanları bul
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # ID'yi yakala (id=... kısmından)
            cid_match = re.search(r'id=([^&"\'\s>]+)', href)
            
            # Takım isimlerini ara (farklı class isimleri olabilir, hepsini deniyoruz)
            name_tag = a.find(class_=re.compile(r"(team-name|channel-name|match-name)"))
            
            if cid_match and name_tag:
                cid = cid_match.group(1)
                # Eğer birden fazla takım ismi varsa (Ev Sahibi - Deplasman) birleştir
                teams = a.find_all(class_="team-name")
                if len(teams) >= 2:
                    title = f"LIVE | {teams[0].get_text(strip=True)} - {teams[1].get_text(strip=True)}"
                else:
                    title = f"LIVE | {name_tag.get_text(strip=True)}"

                # M3U Ekleme
                m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{title}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                match_count += 1

        # SABİT KANALLARI EKLE
        for cid, name in fixed_channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 KANALLAR",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # Dosyayı Kaydet
        with open("patron_live.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"✅ Başarılı! {match_count} adet maç + {len(fixed_channels)} sabit kanal eklendi.")
        print("📂 Dosya: patron_live.m3u")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
