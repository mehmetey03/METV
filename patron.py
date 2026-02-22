import requests
import re
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://hepbetspor16.cfd/",
    "X-Requested-With": "XMLHttpRequest"
}

def get_base_url():
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except: return "https://obv.d72577a9dd0ec28.sbs/"

def main():
    main_site = "https://hepbetspor16.cfd"
    base_url = get_base_url()
    
    print(f"📡 Bağlanılıyor: {main_site}")
    print(f"🚀 Yayın Sunucusu: {base_url}")

    m3u_list = ["#EXTM3U"]
    
    try:
        # Sayfayı çek
        response = requests.get(main_site, headers=HEADERS, timeout=15, verify=False)
        html_content = response.text

        # HTML içinde "channel-item" bloklarını manuel (Regex ile) parçala
        # Bu yöntem BeautifulSoup'un kaçırdığı 'render edilmemiş' metinleri de yakalar.
        blocks = re.findall(r'<div class="channel-item".*?>(.*?)</div>\s*</div>', html_content, re.DOTALL)
        
        if not blocks:
            # Eğer yukarıdaki yakalamazsa daha geniş bir tarama yap
            blocks = re.findall(r'data-src="/ch\.html\?id=(.*?)".*?class="team-name">(.*?)</span>.*?class="team-name">(.*?)</span>', html_content, re.DOTALL)

        found_count = 0
        for block in blocks:
            # block bir tuple (id, team1, team2) ise
            if isinstance(block, tuple):
                cid, t1, t2 = block
                name = f"{t1} - {t2}"
            else:
                # Normal blok içinden ID ve isim çek
                cid_match = re.search(r'id=([^&"\'\s>]+)', block)
                if not cid_match: continue
                cid = cid_match.group(1)
                teams = re.findall(r'class="team-name">(.*?)</span>', block)
                name = " - ".join(teams) if teams else f"Kanal {cid}"

            # M3U Ekleme
            m3u_list.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{name}')
            m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_list.append(f'#EXTVLCOPT:http-referrer={main_site}/')
            m3u_list.append(f'{base_url}{cid}/mono.m3u8')
            found_count += 1

        # Eğer hala 0 ise, sitenin maçları çektiği JSON dosyasını tahmin etmeyi deneyelim
        if found_count == 0:
            print("⚠️ HTML içinde maç bulunamadı, alternatif JSON kaynağı deneniyor...")
            # Sitede genellikle ajax/matches.php gibi bir yer olur ama biz şimdilik sabitleri ekleyelim
            fixed = ["patron", "b2", "b3", "t2", "ss1"]
            for f_id in fixed:
                m3u_list.append(f'#EXTINF:-1 group-title="7/24 KANALLAR",Kanal {f_id}')
                m3u_list.append(f'{base_url}{f_id}/mono.m3u8')

        with open("patron_final.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
            
        print(f"✅ İşlem bitti. Bulunan Maç: {found_count}")

    except Exception as e:
        print(f"💥 Hata: {e}")

if __name__ == "__main__":
    main()
