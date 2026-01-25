import requests
import re
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOMAIN_API = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"

def main():
    m3u_list = ["#EXTM3U"]
    session = requests.Session()
    
    # Tarayıcı gibi davranmak için kapsamlı header seti
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://63betorspintv.live/",
        "Upgrade-Insecure-Requests": "1"
    })

    try:
        print("📡 Sunucu adresi alınıyor...")
        base_url = session.get(DOMAIN_API, timeout=10).json().get("baseurl")
        
        print("⚽ Canlı maç listesi deşifre ediliyor...")
        # Siteyi ziyaret et
        response = session.get(TARGET_SITE, timeout=15, verify=False)
        html_content = response.text

        # Paylaştığın HTML yapısına uygun "Cerrahi" Regex
        # <a class="single-match show" href="channel?id=..." ... <div class="event">...</div> ... <div class="home">...</div> ... <div class="away">...</div>
        pattern = r'href="channel\?id=(.*?)".*?<div class="event">(.*?)</div>.*?<div class="home">(.*?)</div>.*?<div class="away">(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL)

        if not matches:
            # Alternatif: Eğer yukarıdaki regex yakalamazsa daha esnek bir arama yap
            pattern = r'href="channel\?id=(.*?)".*?class="event">(.*?)<.*?class="home">(.*?)<.*?class="away">(.*?)<'
            matches = re.findall(pattern, html_content, re.DOTALL)

        for cid, event, home, away in matches:
            # HTML temizliği (Gereksiz boşlukları sil)
            clean_cid = cid.strip()
            clean_event = event.strip()
            clean_home = home.strip()
            clean_away = away.strip()
            
            title = f"{clean_event} | {clean_home} - {clean_away}"
            
            m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
            m3u_list.append(f"{base_url}{clean_cid}.m3u8")

        # Sabit Kanalları Ekle (HTML'deki mantığa göre)
        print(f"📺 Sabit spor kanalları ekleniyor...")
        sabit_kanallar = {
            "beIN Sports 1": "yayinzirve", "beIN Sports 2": "yayinb2", 
            "beIN Sports 3": "yayinb3", "beIN Sports 4": "yayinb4",
            "beIN Sports 5": "yayinb5", "S Sport 1": "yayinss"
        }
        
        for name, cid in sabit_kanallar.items():
            m3u_list.append(f'#EXTINF:-1 group-title="📺 KANALLAR",{name}')
            m3u_list.append(f"{base_url}{cid}.m3u8")

        # Dosyaya Yaz
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print("-" * 30)
        print(f"✅ İŞLEM BAŞARILI!")
        print(f"👉 {len(matches)} Canlı Maç bulundu.")
        print(f"📂 betorspin.m3u8 dosyası hazır.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
