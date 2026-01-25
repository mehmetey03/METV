import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Adresler
DOMAIN_API = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE
}

# Senin istediğin 34 Kanal (Tam Liste)
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
    
    try:
        # 1. Yayın Sunucusunu Al
        print("📡 Sunucu adresi alınıyor...")
        base_url = requests.get(DOMAIN_API, timeout=10).json().get("baseurl")
        print(f"📡 Sunucu URL: {base_url}")
        
        # 2. Canlı Maçları HTML İçinden Ayıkla
        print("⚽ Canlı maç listesi deşifre ediliyor...")
        response = requests.get(TARGET_SITE, headers=HEADERS, timeout=15, verify=False)
        html_content = response.text
        
        # Debug için HTML'nin bir kısmını kaydet
        with open("debug_html.html", "w", encoding="utf-8") as f:
            f.write(html_content[:5000])  # İlk 5000 karakteri kaydet
        
        # Daha basit ve esnek regex pattern
        # <a class="single-match show" href="channel?id=yayinex1" ... ile başlayan blokları bul
        pattern = r'<a class="single-match show" href="channel\?id=(.*?)".*?<div class="date">(.*?)</div>.*?<div class="event">(.*?)</div>.*?<div class="home">(.*?)</div>.*?<div class="away">(.*?)</div>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        print(f"🔍 Bulunan eşleşmeler: {len(matches)}")
        
        # Alternatif daha basit pattern
        if not matches:
            print("⚠️ İlk pattern ile eşleşme bulunamadı, alternatif pattern deneniyor...")
            # Daha genel pattern
            pattern2 = r'href="channel\?id=([^"]+)".*?class="date"[^>]*>([^<]+).*?class="event"[^>]*>([^<]+).*?class="home"[^>]*>([^<]+).*?class="away"[^>]*>([^<]+)'
            matches = re.findall(pattern2, html_content, re.DOTALL)
            print(f"🔍 Alternatif pattern ile bulunan eşleşmeler: {len(matches)}")
        
        # Debug için bulunan ilk eşleşmeyi göster
        if matches:
            print(f"📋 İlk eşleşme örneği: {matches[0]}")

        match_count = 0
        for match in matches:
            if len(match) >= 5:
                cid = match[0].strip()
                date = match[1].strip()
                event = match[2].strip()
                home = match[3].strip()
                away = match[4].strip()
                
                # Tarih bilgisini de ekleyelim
                title = f"{date} | {event} | {home} - {away}"
                
                m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
                m3u_list.append(f"{base_url}{cid}.m3u8")
                match_count += 1
                
                # Debug için ilk birkaç maçı göster
                if match_count <= 3:
                    print(f"   📝 {match_count}. maç: {title}")

        # 3. Sabit Kanalları Ekle
        print(f"\n📺 {len(SABIT_KANALLAR)} Sabit spor kanalı ekleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_list.append(f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}')
            m3u_list.append(f"{base_url}{file}")

        # 4. Dosyaya Kaydet
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print("-" * 30)
        print(f"✅ İŞLEM BAŞARILI!")
        print(f"👉 {match_count} Canlı Maç bulundu (UFC, Süper Lig, Premier Lig vb.)")
        print(f"👉 {len(SABIT_KANALLAR)} Sabit spor kanalı eklendi.")
        print("📂 betorspin.m3u8 dosyası hazır.")

    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
