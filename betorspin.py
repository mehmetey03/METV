import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    
    # Gerçek bir tarayıcı oturumu simüle et
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive"
    })

    try:
        print("📡 Yayın sunucusu alınıyor...")
        base_url = session.get(DOMAIN_API, timeout=10).json().get("baseurl")
        
        print("⚽ Maç listesi için güvenlik kontrolü geçiliyor...")
        # Önce ana sayfaya bir "merhaba" deyip çerezleri alalım
        first_step = session.get(TARGET_SITE, timeout=15, verify=False)
        
        # Şimdi içeriği tekrar isteyelim (Çerezlerle birlikte)
        response = session.get(TARGET_SITE, timeout=15, verify=False)
        html = response.text

        # HTML içinde maçları yakala
        # Not: Bazı maçlarda tırnaklar farklı olabiliyor, o yüzden regex'i esnettik.
        pattern = r'href=["\']channel\?id=(.*?)["\'].*?class=["\']event["\']>(.*?)<.*?class=["\']home["\']>(.*?)<.*?class=["\']away["\']>(.*?)<'
        matches = re.findall(pattern, html, re.DOTALL)

        for cid, event, home, away in matches:
            # HTML temizliği
            clean_cid = cid.strip()
            title = f"{event.strip()} | {home.strip()} - {away.strip()}"
            
            m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
            m3u_list.append(f"{base_url}{clean_cid}.m3u8")

        print(f"📺 {len(SABIT_KANALLAR)} Sabit spor kanalı ekleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_list.append(f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}')
            m3u_list.append(f"{base_url}{file}")

        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print("-" * 30)
        print(f"✅ TAMAMLANDI! {len(matches)} Canlı Maç ve {len(SABIT_KANALLAR)} kanal eklendi.")

    except Exception as e:
        print(f"❌ Kritik bir hata oluştu: {e}")

if __name__ == "__main__":
    main()
