import requests
import re
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını sustur
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SENİN VERDİĞİN KESİN BİLGİLER
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://google.com"
}

def get_main_domain():
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
        match = re.search(r'(https?://[^\s\'"]+)', r.text)
        return match.group(1).rstrip('/') if match else "https://hepbetspor16.cfd"
    except: return "https://hepbetspor16.cfd"

def get_base_url():
    try:
        # JSON'dan baseurl çekme (obv...sbs)
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        return data.get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except: return None

def main():
    main_site = get_main_domain()
    base_url = get_base_url()

    if not base_url:
        print("❌ Yayın sunucusu alınamadı!")
        return

    print(f"📡 Kaynak Site: {main_site}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    m3u_list = ["#EXTM3U"]
    
    try:
        response = requests.get(main_site, headers=HEADERS, timeout=15, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # HTML'deki 'channel-item' divlerini bul
        items = soup.find_all("div", class_="channel-item")
        
        for item in items:
            # 1. Yayın ID'sini Al (/ch.html?id=xxx)
            data_src = item.get("data-src", "")
            id_match = re.search(r'id=([^&]+)', data_src)
            
            if id_match:
                channel_id = id_match.group(1)
                
                # 2. Takımları Al
                teams = [t.get_text(strip=True) for t in item.find_all("span", class_="team-name")]
                match_name = " - ".join(teams) if teams else "Bilinmeyen Maç"
                
                # 3. Lig ve Saat Bilgisi
                league = item.find("span", class_="league-text")
                m_time = item.find("span", class_="match-time")
                
                league_txt = f"[{league.get_text(strip=True)}] " if league else ""
                time_txt = f" ({m_time.get_text(strip=True)})" if m_time else ""
                
                # 4. Logolar (Ev sahibi logosunu alalım)
                img_tag = item.find("img", class_="match-logo")
                logo_url = img_tag.get("src", "") if img_tag else ""

                # M3U Yazımı
                m3u_list.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="CANLI MAÇLAR",{league_txt}{match_name}{time_txt}')
                # Referer olarak ana siteyi ekle ki yayın açılsın
                m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_list.append(f'#EXTVLCOPT:http-referrer={main_site}/')
                m3u_list.append(f'{base_url}{channel_id}/mono.m3u8')

        # Dosyayı kaydet
        with open("patron_listesi.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
            
        print(f"✅ Başarılı! {len(m3u_list)//4} adet maç listeye eklendi.")

    except Exception as e:
        print(f"⚠️ Hata: {e}")

if __name__ == "__main__":
    main()
