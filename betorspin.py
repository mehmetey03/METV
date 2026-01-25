import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API ve Ayarlar
DOMAIN_API = "https://maqrizi.com/domain.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", "beIN Sports 5": "yayinb5.m3u8", "beIN Sports Haber": "yayinbeinh.m3u8",
    "beIN Sports MAX 1": "yayinbm1.m3u8", "beIN Sports MAX 2": "yayinbm2.m3u8",
    "S Sport 1": "yayinss.m3u8", "S Sport 2": "yayinss2.m3u8", "Smart Spor 1": "yayinsmarts.m3u8", 
    "Smart Spor 2": "yayinsms2.m3u8", "Tivibu Spor 1": "yayint1.m3u8", "Tivibu Spor 2": "yayint2.m3u8", 
    "Tivibu Spor 3": "yayint3.m3u8", "Tivibu Spor 4": "yayint4.m3u8", "TRT Spor": "yayintrtspor.m3u8",
    "TRT Spor Yıldız": "yayintrtspor2.m3u8", "TRT 1": "yayintrt1.m3u8", "A Spor": "yayinas.m3u8",
    "ATV": "yayinatv.m3u8", "TV 8": "yayintv8.m3u8", "TV 8.5": "yayintv85.m3u8", "Sky Sports F1": "yayinf1.m3u8",
    "Eurosport 1": "yayineu1.m3u8", "Eurosport 2": "yayineu2.m3u8", "TABII Spor": "yayinex7.m3u8",
    "TABII Spor 1": "yayinex1.m3u8", "TABII Spor 2": "yayinex2.m3u8", "TABII Spor 3": "yayinex3.m3u8",
    "TABII Spor 4": "yayinex4.m3u8", "TABII Spor 5": "yayinex5.m3u8", "TABII Spor 6": "yayinex6.m3u8",
    "NBA TV": "yayinnba.m3u8", "FB TV": "yayinfb.m3u8", "GS TV": "yayingstve.m3u8", "BJK TV": "yayinbjk.m3u8"
}

def get_active_info():
    """Hem yayın sunucusunu hem de site domainini dinamik bulur."""
    base = ""
    site = ""
    
    # 1. Yayın sunucusunu (baseurl) çek
    try:
        base = requests.get(DOMAIN_API, timeout=5).json().get("baseurl", "")
    except: pass
    
    # 2. Aktif site domainini tara (63-80 arası)
    for i in range(63, 81):
        test_url = f"https://{i}betorspintv.live/"
        try:
            r = requests.get(test_url, headers={"User-Agent": UA}, timeout=2, verify=False)
            if r.status_code == 200:
                site = test_url
                break
        except: continue
        
    return base, site

def main():
    base_url, site_url = get_active_info()
    
    if not base_url:
        print("❌ Yayın sunucusu alınamadı.")
        return

    m3u = ["#EXTM3U"]
    for name, file in SABIT_KANALLAR.items():
        m3u.append(f'#EXTINF:-1,{name}')
        # Linkin yanına hiçbir şey eklemiyoruz, sadece saf URL
        m3u.append(f"{base_url}{file}")

    with open("betorspin.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    
    print(f"✅ İşlem Tamam.")
    print(f"📡 Sunucu: {base_url}")
    print(f"🔗 Site: {site_url if site_url else 'Bulunamadı'}")

if __name__ == "__main__":
    main()
