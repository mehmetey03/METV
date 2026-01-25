import requests
import urllib3

# SSL uyarılarını sustur
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOMAIN_API = "https://maqrizi.com/domain.php"

# Senin Sabit Kanal Listen
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
    """63'ten başlayarak çalışan betorspin adresini bulur."""
    for i in range(63, 80): # 63 ile 80 arası numaraları dene
        url = f"https://{i}betorspintv.live/"
        try:
            # Sadece header kontrolü yap (hız için)
            r = requests.head(url, timeout=2, verify=False)
            if r.status_code < 400:
                print(f"🔗 Aktif domain bulundu: {url}")
                return url
        except:
            continue
    return "https://63betorspintv.live/" # Bulamazsa varsayılan

def main():
    m3u_list = ["#EXTM3U"]
    active_url = find_active_domain()
    
    session = requests.Session()
    # İstediğin kimlik bilgileri (Headers)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": active_url.rstrip('/'),
        "Referer": active_url,
        "Accept": "*/*"
    })

    try:
        print("📡 Yayın sunucusu alınıyor...")
        # Domain API'den baseurl al
        base_url = session.get(DOMAIN_API, timeout=10).json().get("baseurl")
        
        print(f"📺 {len(SABIT_KANALLAR)} Sabit kanal listeye işleniyor...")
        for name, filename in SABIT_KANALLAR.items():
            # M3U formatına ekle
            m3u_list.append(f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}')
            m3u_list.append(f"{base_url}{filename}")

        # Dosyayı kaydet
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print("-" * 30)
        print(f"✅ BİTTİ! betorspin.m3u8 dosyası güncellendi.")
        print(f"📡 Kullanılan Kaynak: {active_url}")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
