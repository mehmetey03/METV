import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# AYARLAR
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"
MAIN_SITE = "https://hepbetspor16.cfd"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": f"{MAIN_SITE}/",
    "Accept-Language": "tr-TR,tr;q=0.9"
}

def get_base_url():
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except: 
        return "https://obv.d72577a9dd0ec28.sbs/"

def main():
    base_url = get_base_url()
    print(f"📡 Bağlanılıyor: {MAIN_SITE}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    m3u_list = ["#EXTM3U"]
    
    try:
        response = requests.get(MAIN_SITE, headers=HEADERS, timeout=15, verify=False)
        html = response.text

        # Daha esnek bir yakalama deseni: 
        # id'yi, takımları ve ligi tek seferde blok bazlı değil, içerik bazlı arıyoruz.
        # Bu desen 'channel-item' içindeki verileri parça parça toplar.
        
        # 1. Önce tüm kanal bloklarını ayır
        items = re.findall(r'<div class="channel-item".*?data-src="/ch\.html\?id=(.*?)".*?>(.*?)</div>\s*</div>', html, re.DOTALL)
        
        found_count = 0
        for cid, content in items:
            # Takım isimlerini ayıkla
            teams = re.findall(r'<span class="team-name">(.*?)</span>', content)
            # Lig bilgisini ayıkla (varsa)
            league_match = re.search(r'<span class="league-text">(.*?)</span>', content)
            # Saat bilgisini ayıkla (varsa)
            time_match = re.search(r'<span class="match-time">(.*?)</span>', content)
            
            # Verileri temizle ve birleştir
            name = " - ".join(teams) if teams else f"Kanal {cid}"
            league = f"[{league_match.group(1)}] " if league_match else ""
            m_time = f" ({time_match.group(1)})" if time_match else ""
            
            # M3U Formatına ekle
            m3u_list.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{league}{name}{m_time}')
            m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_list.append(f'#EXTVLCOPT:http-referrer={MAIN_SITE}/')
            m3u_list.append(f'{base_url}{cid}/mono.m3u8')
            found_count += 1

        # Dosyayı kaydet
        with open("patron_v4.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
            
        print(f"✅ İşlem bitti. Toplam {found_count} maç listeye eklendi.")
        if found_count > 0:
            print(f"📂 'patron_v4.m3u' dosyası oluşturuldu.")

    except Exception as e:
        print(f"💥 Hata oluştu: {e}")

if __name__ == "__main__":
    main()
