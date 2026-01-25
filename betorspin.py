import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sitenin veriyi çektiği gizli API
API_URL = "https://maqrizi.com/domain.php"
TARGET_REFERER = "https://63betorspintv.live/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET_REFERER
}

# Paylaştığın koddan alınan kanal listesi
KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8",
    "beIN Sports 2": "yayinb2.m3u8",
    "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8",
    "beIN Sports 5": "yayinb5.m3u8",
    "beIN Sports Haber": "yayinbm1.m3u8",
    "beIN Sports Max 2": "yayinbm2.m3u8",
    "S Sport 1": "yayinss.m3u8",
    "S Sport 2": "yayinss2.m3u8",
    "Tivibu Spor 1": "yayint1.m3u8",
    "Tivibu Spor 2": "yayint2.m3u8",
    "Tivibu Spor 3": "yayint3.m3u8",
    "Tivibu Spor 4": "yayint4.m3u8",
    "Smart Spor": "yayinsmarts.m3u8",
    "Smart Spor 2": "yayinsms2.m3u8",
    "EuroSport 1": "yayineu1.m3u8",
    "EuroSport 2": "yayineu2.m3u8",
    "A Spor": "yayinas.m3u8",
    "ATV": "yayinatv.m3u8",
    "TV8": "yayintv8.m3u8",
    "TV8.5": "yayintv85.m3u8",
    "NBA TV": "yayinnbatv.m3u8",
    "Exxen 1": "yayinex1.m3u8",
    "Exxen 2": "yayinex2.m3u8",
    "Exxen 3": "yayinex3.m3u8",
    "Exxen 4": "yayinex4.m3u8",
    "Exxen 5": "yayinex5.m3u8",
    "Exxen 6": "yayinex6.m3u8",
    "Exxen 7": "yayinex7.m3u8",
    "Exxen 8": "yayinex8.m3u8",
    "TRT Spor": "yayintrtspor.m3u8",
    "TRT Spor 2": "yayintrtspor2.m3u8",
    "TRT 1": "yayintrt1.m3u8",
    "F1 TV": "yayinf1.m3u8"
}

def main():
    m3u_content = ["#EXTM3U"]
    
    try:
        print(f"📡 Yayın sunucusu API'den alınıyor: {API_URL}")
        response = requests.get(API_URL, headers=HEADERS, timeout=15, verify=False)
        data = response.json()
        base_url = data.get("baseurl")

        if base_url:
            print(f"✅ Güncel Sunucu Adresi: {base_url}")
            
            for name, file in KANALLAR.items():
                m3u_content.append(f'#EXTINF:-1 group-title="BetOrSpin Kanallar",{name}')
                m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={TARGET_REFERER}')
                m3u_content.append(f"{base_url}{file}")
            
            print(f"📝 {len(KANALLAR)} kanal başarıyla eklendi.")
        else:
            print("❌ API'den baseurl alınamadı.")

    except Exception as e:
        print(f"❌ Hata: {e}")

    # Dosyayı kaydet
    with open("betorspin.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    print("💾 betorspin.m3u8 dosyası güncellendi.")

if __name__ == "__main__":
    main()
