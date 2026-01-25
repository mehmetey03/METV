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

# Kanal listesi aynı...

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
        
        # ÇOK BASİT regex - sadece href'leri bul
        print("🔍 Basit regex ile maçlar aranıyor...")
        
        # Önce tüm href="channel?id=..." ifadelerini bul
        channel_ids = re.findall(r'href="channel\?id=([^"]+)"', html_content)
        
        # Benzersiz ID'leri al
        unique_ids = list(set(channel_ids))
        print(f"🔍 Bulunan kanal ID'leri: {len(unique_ids)} adet")
        
        # İlk 5 ID'yi göster
        for i, cid in enumerate(unique_ids[:5]):
            print(f"   {i+1}. ID: {cid}")
        
        # HTML'den maç bilgilerini çıkarmak için daha basit bir yaklaşım
        # Her maç bloğunu ayrı ayrı işle
        maç_blokları = re.split(r'<a class="single-match', html_content)[1:]  # İlk elemanı atla
        
        print(f"🔍 Ayrıştırılan maç blokları: {len(maç_blokları)}")
        
        match_count = 0
        for blok in maç_blokları[:10]:  # İlk 10 bloğu kontrol et
            # ID'yi bul
            id_match = re.search(r'href="channel\?id=([^"]+)"', blok)
            if id_match:
                cid = id_match.group(1)
                
                # Diğer bilgileri bul
                date_match = re.search(r'<div class="date">([^<]+)</div>', blok)
                event_match = re.search(r'<div class="event">([^<]+)</div>', blok)
                home_match = re.search(r'<div class="home">([^<]+)</div>', blok)
                away_match = re.search(r'<div class="away">([^<]+)</div>', blok)
                
                if date_match and event_match and home_match and away_match:
                    date = date_match.group(1).strip()
                    event = event_match.group(1).strip()
                    home = home_match.group(1).strip()
                    away = away_match.group(1).strip()
                    
                    title = f"{date} | {event} | {home} - {away}"
                    
                    m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
                    m3u_list.append(f"{base_url}{cid}.m3u8")
                    match_count += 1
                    
                    print(f"   📝 Maç eklendi: {title}")

        # Kalan kod aynı...
        # ... (sabit kanallar ve dosya kaydetme)
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
