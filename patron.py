import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://hepbetspor16.cfd/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

def get_base_url():
    try:
        r = requests.get("https://patronsports1.cfd/domain.php", headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except:
        return "https://obv.d72577a9dd0ec28.sbs/"

def main():
    source_url = "https://hepbetspor16.cfd"
    base_url = get_base_url()
    
    print(f"📡 Kaynak: {source_url}")
    print(f"🚀 Sunucu: {base_url}")

    try:
        response = requests.get(source_url, headers=HEADERS, timeout=15, verify=False)
        content = response.text

        # 1. Strateji: id= kısmını ve hemen peşinden gelen takımları yakala
        # HTML yapısındaki boşlukları ve satırları (.*?) ile yutuyoruz
        matches = re.findall(r'id=([a-zA-Z0-9_-]+)".*?class="team-name">(.*?)</span>.*?class="team-name">(.*?)</span>', content, re.DOTALL)
        
        m3u_content = ["#EXTM3U"]
        count = 0

        for cid, home, away in matches:
            title = f"LIVE | {home.strip()} - {away.strip()}"
            m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{title}')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            count += 1

        # 2. Strateji: Eğer yukarıdaki boş dönerse, sadece ID ve tekli isimleri ara
        if count == 0:
            simple_matches = re.findall(r'id=([a-zA-Z0-9_-]+)".*?class="team-name">(.*?)</span>', content, re.DOTALL)
            for cid, name in simple_matches:
                m3u_content.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",LIVE | {name.strip()}')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                count += 1

        # Sabit kanallar
        fixed = {"b1": "beIN Sports 1", "b2": "beIN Sports 2", "ss1": "S Sports 1"}
        for fid, fname in fixed.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 KANALLAR",{fname}')
            m3u_content.append(f'{base_url}{fid}/mono.m3u8')

        with open("patron_v6.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"✅ Sonuç: {count} maç yakalandı!")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
