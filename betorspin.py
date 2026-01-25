import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Adresi
DOMAIN_API = "https://maqrizi.com/domain.php"
FIXED_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

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

def get_dynamic_data():
    """Yayın sunucusunu ve güncel site adresini bulur."""
    base = ""
    site = ""
    # 1. Maqrizi üzerinden baseurl al
    try:
        base = requests.get(DOMAIN_API, timeout=5).json().get("baseurl", "")
    except: pass
    
    # 2. Aktif domaini tara (63, 64, 65...)
    for i in range(63, 85):
        url = f"https://{i}betorspintv.live/"
        try:
            r = requests.get(url, timeout=2, verify=False)
            if r.status_code == 200:
                site = url
                break
        except: continue
    return base, site

def main():
    base_url, site_url = get_dynamic_data()
    
    if not base_url:
        print("❌ Hata: Yayın sunucusu çekilemedi.")
        return

    m3u = ["#EXTM3U"]
    for name, file in SABIT_KANALLAR.items():
        # İstediğin Özel Format
        m3u.append(f'#EXTINF:-1 group-title="BetOrSpin Kanallar",{name}')
        m3u.append(f'#EXTVLCOPT:http-user-agent={FIXED_UA}')
        m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
        m3u.append(f"{base_url}{file}")

    with open("betorspin.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    
    print("-" * 30)
    print(f"✅ Liste Oluşturuldu!")
    print(f"🔗 Kullanılan Referer: {site_url}")
    print(f"📡 Kullanılan Sunucu: {base_url}")
    print("-" * 30)

if __name__ == "__main__":
    main()
