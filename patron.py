import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://hepbetspor16.cfd/",
    "X-Requested-With": "XMLHttpRequest"
}

def get_base_url():
    try:
        r = requests.get("https://patronsports1.cfd/domain.php", headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except: 
        return "https://obv.d72577a9dd0ec28.sbs/"

def main():
    main_site = "https://hepbetspor16.cfd"
    base_url = get_base_url()
    
    print(f"📡 Bağlanılıyor: {main_site}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    try:
        # Sayfayı çek
        response = requests.get(main_site, headers=HEADERS, timeout=15, verify=False)
        html_content = response.text
        
        # Tüm maçları bul - DÜZELTİLMİŞ REGEX
        # data-src içinden id'yi ve takım isimlerini çek
        pattern = r'data-src="/ch\.html\?id=([^"]+)".*?team-name">([^<]+)</span>.*?team-name">([^<]+)</span>'
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        print(f"🔍 Bulunan maç sayısı: {len(matches)}")
        
        m3u_list = ["#EXTM3U"]
        
        for cid, team1, team2 in matches:
            name = f"{team1} - {team2}"
            print(f"📺 {name} (ID: {cid})")
            
            m3u_list.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
            m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_list.append(f'#EXTVLCOPT:http-referrer={main_site}/')
            m3u_list.append(f'{base_url}{cid}/mono.m3u8')
        
        # Dosyaya kaydet
        output_file = "patron_final.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
            
        print(f"\n✅ İşlem tamamlandı!")
        print(f"📊 Toplam maç: {len(matches)}")
        print(f"💾 Dosya: {output_file}")

    except Exception as e:
        print(f"💥 Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
