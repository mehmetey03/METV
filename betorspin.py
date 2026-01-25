import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
DOMAIN_API = "https://maqrizi.com/domain.php"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

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

def find_working_domain():
    """Çalışan domain'i hızlıca bulur."""
    print("🔍 Aktif site adresi taranıyor...")
    for i in range(63, 85):
        url = f"https://{i}betorspintv.live/"
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=2, verify=False)
            if r.status_code == 200:
                print(f"✅ Bulundu: {url}")
                return url
        except:
            continue
    return "https://63betorspintv.live/"

def main():
    try:
        # 1. Yayın Sunucusunu (BaseURL) Al
        base_url = "https://bnw.zirvedesin119.lat/" # Yedek
        try:
            res = requests.get(DOMAIN_API, timeout=5).json()
            base_url = res.get("baseurl", base_url)
        except:
            print("⚠️ API çalışmıyor, yedek sunucu kullanılıyor.")

        # 2. Referrer Domaini Bul
        ref_url = find_working_domain()
        
        # 3. M3U İçeriğini Oluştur
        m3u_content = "#EXTM3U\n"
        
        for name, file in SABIT_KANALLAR.items():
            full_url = f"{base_url}{file}"
            
            # Hem VLC hem de diğer Playerlar için header eklemeleri
            m3u_content += f'#EXTINF:-1 group-title="BetOrSpin",{name}\n'
            # Bazı playerlar için opsiyonel komutlar
            m3u_content += f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n'
            m3u_content += f'#EXTVLCOPT:http-referrer={ref_url}\n'
            # Link sonuna eklenen headerlar (En sağlam yöntemdir)
            m3u_content += f'{full_url}|User-Agent={USER_AGENT}&Referer={ref_url}\n'

        # 4. Kaydet
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("-" * 40)
        print(f"🚀 Başarılı! {len(SABIT_KANALLAR)} kanal eklendi.")
        print(f"📂 Dosya: betorspin.m3u8")
        print("-" * 40)

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
