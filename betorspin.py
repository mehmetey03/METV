import cloudscraper
import re
import requests

# Sunucu adresini almak için standart requests yeterli
DOMAIN_API = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"

SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", "beIN Sports 5": "yayinb5.m3u8", "beIN Sports Haber": "yayinbeinh.m3u8",
    "S Sport 1": "yayinss.m3u8", "S Sport 2": "yayinss2.m3u8", "Tivibu Spor 1": "yayint1.m3u8",
    "Tivibu Spor 2": "yayint2.m3u8", "Tivibu Spor 3": "yayint3.m3u8", "Tivibu Spor 4": "yayint4.m3u8",
    "Exxen Spor 1": "yayinex1.m3u8", "Exxen Spor 2": "yayinex2.m3u8", "Exxen Spor 3": "yayinex3.m3u8",
    "Exxen Spor 4": "yayinex4.m3u8", "Exxen Spor 5": "yayinex5.m3u8", "Exxen Spor 6": "yayinex6.m3u8",
    "Smart Spor 1": "yayinsmarts.m3u8", "Smart Spor 2": "yayinsmarts2.m3u8", "TRT Spor": "yayintrtspor.m3u8",
    "TRT Spor Yıldız": "yayintrtspor2.m3u8", "TV 8.5": "yayintv85.m3u8", "A Spor": "yayinasp.m3u8",
    "Eurosport 1": "yayineuro1.m3u8", "Eurosport 2": "yayineuro2.m3u8", "NBA TV": "yayinnba.m3u8",
    "FB TV": "yayinfb.m3u8", "GS TV": "yayingstve.m3u8", "BJK TV": "yayinbjk.m3u8",
    "Smart Spor HD": "yayinsmarts.m3u8", "A Spor HD": "yayinasp.m3u8", "TRT Spor HD": "yayintrtspor.m3u8", "TV 8.5 HD": "yayintv85.m3u8"
}

def main():
    m3u_list = ["#EXTM3U"]
    # Bot korumasını aşan özel istemci
    scraper = cloudscraper.create_scraper() 
    
    try:
        print("📡 Sunucu adresi alınıyor...")
        base_url = requests.get(DOMAIN_API).json().get("baseurl")
        
        print("⚽ Canlı maç listesi deşifre ediliyor (Güvenlik duvarı aşılıyor)...")
        # Siteyi gerçek bir kullanıcı gibi ziyaret et
        response = scraper.get(TARGET_SITE, timeout=20)
        html_content = response.text

        # Senin attığın HTML yapısına tam uyumlu regex
        pattern = r'href="channel\?id=(.*?)".*?<div class="event">(.*?)</div>.*?<div class="home">(.*?)</div>.*?<div class="away">(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL)

        for cid, event, home, away in matches:
            title = f"{event.strip()} | {home.strip()} - {away.strip()}"
            m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
            m3u_list.append(f"{base_url}{cid.strip()}.m3u8")

        print(f"📺 {len(SABIT_KANALLAR)} Sabit spor kanalı ekleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_list.append(f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}')
            m3u_list.append(f"{base_url}{file}")

        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print("-" * 30)
        print(f"✅ BİTTİ! {len(matches)} Canlı Maç yakalandı.")
        print(f"📂 betorspin.m3u8 dosyası oluşturuldu.")

    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()
