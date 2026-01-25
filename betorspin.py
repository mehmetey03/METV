import requests
import re
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET = "https://63betorspintv.live"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": TARGET + "/"
}

def resolve_base_url(session):
    """Kanal sayfasından m3u8 sunucusunu bulmaya çalışır."""
    try:
        # Rastgele bir kanal sayfası (beIN 1 genelde en güncelidir)
        r = session.get(f"{TARGET}/channel?id=yayinzirve", headers=HEADERS, timeout=15, verify=False)
        
        # 1. Yöntem: Standart m3u8 pattern
        urls = re.findall(r'https?://[a-z0-9.-]+\.(?:sbs|xyz|live|me|site|club|net|com|pw)/', r.text)
        
        for link in urls:
            # Reklam/Analiz servislerini ele
            if not any(x in link for x in ["gstatic", "google", "doubleclick", "analytics", "jsdelivr", "hizliresim"]):
                return link
                
        # 2. Yöntem: HTML içinde saklanmış base64 veya direkt link araması
        # Eğer site linki gizliyorsa burada daha derin tarama yapılabilir.
    except Exception as e:
        print(f"⚠️ Sunucu çözme hatası: {e}")
    return None

def main():
    # Session kullanarak çerezleri (cookies) koru
    session = requests.Session()
    
    try:
        print(f"📡 {TARGET} taranıyor...")
        
        # Önce ana sayfaya git (Çerezleri almak için)
        session.get(TARGET, headers=HEADERS, timeout=10, verify=False)
        
        base_url = resolve_base_url(session)
        if not base_url:
            # Fallback: Eğer bulunamazsa sabit bir sunucu denemesi yapma (Riskli ama bazen gerekir)
            print("❌ Yayın sunucusu bulunamadı. Lütfen siteyi manuel kontrol edin.")
            return

        print(f"✅ Yayın sunucusu bulundu: {base_url}")

        r = session.get(TARGET, headers=HEADERS, timeout=10, verify=False)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        
        # İçerik alanlarını tara
        containers = soup.find_all("div", id=["matches-content", "channels-content"])
        
        if not containers:
            print("❌ İçerik divleri (matches-content) bulunamadı. Site yapısı değişmiş olabilir.")
            return

        for box in containers:
            group_name = "Canlı Maçlar" if box.get('id') == "matches-content" else "TV Kanalları"
            
            for a in box.find_all("a", href=re.compile(r'id=')):
                cid = re.search(r'id=([^&]+)', a["href"]).group(1)
                
                # İsimleri temizle
                name_div = a.find(class_="home") or a.find(class_="event")
                title = name_div.get_text(strip=True) if name_div else cid
                
                # Varsa saat bilgisini ekle
                status = a.find(class_="event")
                if status and group_name == "Canlı Maçlar":
                    title = f"{status.get_text(strip=True)} | {title}"

                m3u_content.append(f'#EXTINF:-1 group-title="{group_name}",{title}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET}/')
                m3u_content.append(f'{base_url}{cid}.m3u8')

        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        
        print(f"🏁 Başarılı: {len(m3u_content)//4} kanal eklendi.")

    except Exception as e:
        print(f"❌ Ana hata: {e}")

if __name__ == "__main__":
    main()
