import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOMAIN_API = "https://maqrizi.com/domain.php"

SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", "beIN Sports 5": "yayinb5.m3u8", "beIN Sports Haber": "yayinbeinh.m3u8",
    "beIN Sports MAX 1": "yayinbm1.m3u8", "beIN Sports MAX 2": "yayinbm2.m3u8",
    "S Sport 1": "yayinss.m3u8", "S Sport 2": "yayinss2.m3u8", 
    "Smart Spor 1": "yayinsmarts.m3u8", "Smart Spor 2": "yayinsms2.m3u8",
    "Tivibu Spor 1": "yayint1.m3u8", "Tivibu Spor 2": "yayint2.m3u8", 
    "Tivibu Spor 3": "yayint3.m3u8", "Tivibu Spor 4": "yayint4.m3u8",
    "TRT Spor": "yayintrtspor.m3u8", "TRT Spor Yıldız": "yayintrtspor2.m3u8", 
    "TRT 1": "yayintrt1.m3u8", "A Spor": "yayinas.m3u8", "ATV": "yayinatv.m3u8",
    "TV 8": "yayintv8.m3u8", "TV 8.5": "yayintv85.m3u8", "Sky Sports F1": "yayinf1.m3u8",
    "Eurosport 1": "yayineu1.m3u8", "Eurosport 2": "yayineu2.m3u8",
    "TABII Spor": "yayinex7.m3u8", "TABII Spor 1": "yayinex1.m3u8", 
    "TABII Spor 2": "yayinex2.m3u8", "TABII Spor 3": "yayinex3.m3u8",
    "TABII Spor 4": "yayinex4.m3u8", "TABII Spor 5": "yayinex5.m3u8", 
    "TABII Spor 6": "yayinex6.m3u8", "NBA TV": "yayinnba.m3u8",
    "FB TV": "yayinfb.m3u8", "GS TV": "yayingstve.m3u8", "BJK TV": "yayinbjk.m3u8"
}

def find_active_domain():
    for i in range(63, 85):
        url = f"https://{i}betorspintv.live/"
        try:
            # Sitenin gerçekten ayakta olup olmadığını kontrol et
            r = requests.get(url, timeout=3, verify=False)
            if r.status_code == 200:
                return url
        except:
            continue
    return "https://63betorspintv.live/"

def main():
    active_url = find_active_domain()
    # Oynatıcılar için gerekli User-Agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # M3U Header (Tivimate, VLC ve IPTV Smarters için uyumlu format)
    m3u_content = f'#EXTM3U x-tvg-url="" url-tvg=""\n'
    
    try:
        print(f"🔗 Aktif Kaynak: {active_url}")
        # Sunucudan ana yayın linkini al
        base_url = requests.get(DOMAIN_API, timeout=10).json().get("baseurl")
        
        print(f"📺 {len(SABIT_KANALLAR)} kanal için linkler 'Referer' desteğiyle oluşturuluyor...")
        
        for name, filename in SABIT_KANALLAR.items():
            # Oynatıcının siteyi kandırması için linkin sonuna başlıkları ekliyoruz
            # Format: link.m3u8|User-Agent=...&Referer=...
            p_link = f"{base_url}{filename}|User-Agent={user_agent}&Referer={active_url}&Origin={active_url.rstrip('/')}"
            
            m3u_content += f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}\n'
            m3u_content += f'{p_link}\n'

        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        
        print("-" * 30)
        print(f"✅ DOSYA HAZIR! Lütfen betorspin.m3u8 dosyasını VLC ile açıp dene.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
