import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
DOMAIN_API = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE,
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

# Eksiksiz 34 Kanal
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
    "ATV": "yayinatv.m3u8", "Kanal D": "yayinkd.m3u8", "Star TV": "yayinstar.m3u8", "Show TV": "yayinshow.m3u8",
    "Now TV": "yayinnow.m3u8", "TV8": "yayintv8.m3u8", "Kanal 7": "yayink7.m3u8"
}

def main():
    m3u_list = ["#EXTM3U"]
    
    try:
        # 1. Domain Al
        print("📡 Yayın adresi güncelleniyor...")
        base_url = requests.get(DOMAIN_API, timeout=10).json().get("baseurl")
        
        # 2. Sayfayı Ham Metin Olarak Çek
        print("⚽ Canlı maçlar taranıyor...")
        response = requests.get(TARGET_SITE, headers=HEADERS, timeout=15, verify=False)
        html = response.text
        
        # Regex ile 'single-match' bloklarını tek tek ayıkla
        # Bu pattern senin yukarıda attığın HTML yapısına tam uyumlu hazırlandı
        matches = re.findall(r'href="channel\?id=(.*?)".*?<div class="event">(.*?)</div>.*?<div class="home">(.*?)</div>.*?<div class="away">(.*?)</div>', html, re.DOTALL)
        
        match_count = 0
        for cid, time, home, away in matches:
            clean_cid = cid.split('"')[0].strip() # URL kirli gelirse temizle
            title = f"{time.strip()} | {home.strip()} - {away.strip()}"
            
            m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
            m3u_list.append(f"{base_url}{clean_cid}.m3u8")
            match_count += 1

        # 3. Sabit Kanalları Ekle
        print(f"📺 {len(SABIT_KANALLAR)} Sabit kanal listeye işleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_list.append(f'#EXTINF:-1 group-title="📺 TÜM KANALLAR",{name}')
            m3u_list.append(f"{base_url}{file}")

        # 4. Dosyaya Yaz
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print(f"✅ BİTTİ! {match_count} Canlı Maç ve {len(SABIT_KANALLAR)} kanal eklendi.")
        if match_count == 0:
            print("⚠️ Not: Maçlar hala 0 geliyorsa site bot korumasını artırmış olabilir.")

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")

if __name__ == "__main__":
    main()
