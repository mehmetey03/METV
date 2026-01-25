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

# GÜNCELLENMİŞ KANAL LİSTESİ - HTML'de gördüklerimize göre
SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", 
    "beIN Sports 2": "yayinb2.m3u8", 
    "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", 
    "beIN Sports 5": "yayinb5.m3u8", 
    "beIN Sports Haber": "yayinbeinh.m3u8",
    "beIN Sports MAX 1": "yayinbm1.m3u8",  # YENİ EKLENDİ
    "beIN Sports MAX 2": "yayinbm2.m3u8",  # YENİ EKLENDİ
    "S Sport 1": "yayinss.m3u8", 
    "S Sport 2": "yayinss2.m3u8", 
    "Smart Spor 1": "yayinsmarts.m3u8", 
    "Smart Spor 2": "yayinsms2.m3u8",      # YENİ EKLENDİ (yayinsmarts2 yerine yayinsms2)
    "Tivibu Spor 1": "yayint1.m3u8",
    "Tivibu Spor 2": "yayint2.m3u8", 
    "Tivibu Spor 3": "yayint3.m3u8", 
    "Tivibu Spor 4": "yayint4.m3u8",
    "TRT Spor": "yayintrtspor.m3u8",
    "TRT Spor Yıldız": "yayintrtspor2.m3u8", 
    "TRT 1": "yayintrt1.m3u8",            # YENİ EKLENDİ
    "A Spor": "yayinas.m3u8",             # YENİ EKLENDİ (yayinasp yerine yayinas)
    "ATV": "yayinatv.m3u8",              # YENİ EKLENDİ
    "TV 8": "yayintv8.m3u8",             # YENİ EKLENDİ
    "TV 8.5": "yayintv85.m3u8",
    "Sky Sports F1": "yayinf1.m3u8",     # YENİ EKLENDİ
    "Eurosport 1": "yayineu1.m3u8",      # YENİ EKLENDİ (yayineuro1 yerine yayineu1)
    "Eurosport 2": "yayineu2.m3u8",      # YENİ EKLENDİ (yayineuro2 yerine yayineu2)
    "TABII Spor": "yayinex7.m3u8",       # YENİ EKLENDİ
    "TABII Spor 1": "yayinex1.m3u8", 
    "TABII Spor 2": "yayinex2.m3u8", 
    "TABII Spor 3": "yayinex3.m3u8",
    "TABII Spor 4": "yayinex4.m3u8", 
    "TABII Spor 5": "yayinex5.m3u8", 
    "TABII Spor 6": "yayinex6.m3u8",
    # Diğer kanallar
    "NBA TV": "yayinnba.m3u8",
    "FB TV": "yayinfb.m3u8", 
    "GS TV": "yayingstve.m3u8", 
    "BJK TV": "yayinbjk.m3u8"
}

def extract_matches_from_html(html_content):
    """HTML'den maçları çıkaran özel fonksiyon"""
    matches = []
    
    # Önce tüm single-match bloklarını bul
    single_match_pattern = r'<a[^>]*class="[^"]*single-match[^"]*"[^>]*>.*?</a>'
    match_blocks = re.findall(single_match_pattern, html_content, re.DOTALL | re.IGNORECASE)
    
    print(f"🔍 Bulunan maç blokları: {len(match_blocks)}")
    
    for block in match_blocks:
        try:
            # Channel ID'yi bul
            id_match = re.search(r'href="channel\?id=([^"]+)"', block)
            if not id_match:
                continue
                
            cid = id_match.group(1).strip()
            
            # Date bilgisini bul
            date_match = re.search(r'<div[^>]*class="date"[^>]*>([^<]+)</div>', block)
            date = date_match.group(1).strip() if date_match else ""
            
            # Event bilgisini bul
            event_match = re.search(r'<div[^>]*class="event"[^>]*>([^<]+)</div>', block)
            event = event_match.group(1).strip() if event_match else ""
            
            # Home takımını bul
            home_match = re.search(r'<div[^>]*class="home"[^>]*>([^<]+)</div>', block)
            home = home_match.group(1).strip() if home_match else ""
            
            # Away takımını bul
            away_match = re.search(r'<div[^>]*class="away"[^>]*>([^<]+)</div>', block)
            away = away_match.group(1).strip() if away_match else ""
            
            # Eğer home ve away varsa, bu bir maçtır
            if home and away and "BEIN SPORTS" not in home.upper() and "TRT" not in home.upper():
                matches.append((cid, date, event, home, away))
                
        except Exception as e:
            continue
    
    return matches

def main():
    m3u_list = ["#EXTM3U"]
    
    try:
        # 1. Yayın Sunucusunu Al
        print("📡 Sunucu adresi alınıyor...")
        domain_response = requests.get(DOMAIN_API, timeout=10)
        print(f"📡 Domain API Yanıtı: {domain_response.status_code}")
        
        if domain_response.status_code != 200:
            print("❌ Domain API'ye erişilemedi!")
            return
            
        domain_data = domain_response.json()
        base_url = domain_data.get("baseurl")
        
        if not base_url:
            print("❌ Base URL bulunamadı!")
            return
            
        print(f"📡 Sunucu URL: {base_url}")
        
        # 2. Canlı Maçları HTML İçinden Ayıkla
        print("⚽ Canlı maç listesi deşifre ediliyor...")
        response = requests.get(TARGET_SITE, headers=HEADERS, timeout=15, verify=False)
        
        if response.status_code != 200:
            print(f"❌ Siteye erişilemedi! Status: {response.status_code}")
            return
            
        html_content = response.text
        
        # HTML'yi dosyaya kaydet (debug için)
        with open("son_html.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("📄 HTML kaydedildi: son_html.html")
        
        # Maçları çıkar
        matches = extract_matches_from_html(html_content)
        
        print(f"✅ Toplam {len(matches)} canlı maç bulundu")
        
        match_count = 0
        for i, (cid, date, event, home, away) in enumerate(matches):
            title = f"{date} | {event} | {home} - {away}"
            
            m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
            m3u_list.append(f"{base_url}{cid}.m3u8")
            match_count += 1
            
            # İlk 3 maçı göster
            if i < 3:
                print(f"   {i+1}. {title}")

        # 3. Sabit Kanalları Ekle
        print(f"\n📺 {len(SABIT_KANALLAR)} Sabit spor kanalı ekleniyor...")
        added_channels = set()
        for name, file in SABIT_KANALLAR.items():
            # Dosya adının geçerli olup olmadığını kontrol et
            if file and file.strip():
                m3u_list.append(f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}')
                m3u_list.append(f"{base_url}{file}")
                added_channels.add(name)
        
        print(f"📺 Eklenen kanallar: {len(added_channels)} adet")

        # 4. Dosyaya Kaydet
        output_file = "betorspin.m3u8"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print("-" * 50)
        print(f"✅ İŞLEM BAŞARILI!")
        print(f"👉 {match_count} Canlı Maç bulundu")
        print(f"👉 {len(added_channels)} Sabit spor kanalı eklendi")
        print(f"📂 {output_file} dosyası hazır")
        print("-" * 50)
        
        # Ek bilgiler
        print("\n🔍 KONTROL LİSTESİ:")
        print("1. 'son_html.html' dosyasını açın")
        print("2. 'channel?id=' ifadelerini arayın")
        print("3. Eksik kanalları kontrol edin")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
