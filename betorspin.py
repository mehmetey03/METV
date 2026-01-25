import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://maqrizi.com/domain.php"
# Maç verilerini içeren gizli JSON kaynağı (Genelde bu tür sitelerde olur)
# Eğer bu çalışmazsa, ana sayfayı tekrar daha güçlü bir User-Agent ile tarayacağız.
TARGET_SITE = "https://63betorspintv.live/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://google.com"
}

SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", 
    "beIN Sports 3": "yayinb3.m3u8", "S Sport 1": "yayinss.m3u8", 
    "S Sport 2": "yayinss2.m3u8", "Tivibu Spor 1": "yayint1.m3u8",
    "Smart Spor": "yayinsmarts.m3u8", "TRT Spor": "yayintrtspor.m3u8"
}

def main():
    m3u_content = ["#EXTM3U"]
    
    try:
        print("📡 Sunucu adresi ve maçlar çekiliyor...")
        # 1. Sunucu Adresini Al
        base_url = requests.get(API_URL, headers=HEADERS, timeout=10).json().get("baseurl")
        
        # 2. Sayfayı Çek (Session kullanarak çerezleri kabul edelim)
        session = requests.Session()
        response = session.get(TARGET_SITE, headers=HEADERS, timeout=15)
        html_content = response.text

        # 3. Regex ile Maçları Yakala (HTML parse etmek yerine doğrudan metin içinde ara)
        # Sitedeki <a> class="single-match" yapısını metin olarak tarıyoruz
        pattern = r'href="channel\?id=(.*?)".*?<div class="event">(.*?)</div>.*?<div class="home">(.*?)</div>.*?<div class="away">(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL)

        count = 0
        for cid, time, home, away in matches:
            cid = cid.strip()
            display_name = f"{time.strip()} | {home.strip()} - {away.strip()}"
            
            m3u_content.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{display_name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET_SITE}')
            
            link = f"{base_url}{cid}.m3u8" if ".m3u8" not in cid else f"{base_url}{cid}"
            m3u_content.append(link)
            count += 1

        # 4. Sabit Kanalları Ekle
        for name, file in SABIT_KANALLAR.items():
            m3u_content.append(f'#EXTINF:-1 group-title="📺 TV KANALLARI",{name}')
            m3u_content.append(f"{base_url}{file}")

        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
            
        print(f"✅ İşlem Tamam! {count} Canlı Maç + {len(SABIT_KANALLAR)} Sabit Kanal eklendi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
