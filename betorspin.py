import requests
import re
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Adresler
DOMAIN_API = "https://maqrizi.com/domain.php"
TARGET_SITE = "https://63betorspintv.live/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE
}

# GÜNCELLENMİŞ KANAL LİSTESİ
SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", 
    "beIN Sports 2": "yayinb2.m3u8", 
    "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", 
    "beIN Sports 5": "yayinb5.m3u8", 
    "beIN Sports Haber": "yayinbeinh.m3u8",
    "beIN Sports MAX 1": "yayinbm1.m3u8",
    "beIN Sports MAX 2": "yayinbm2.m3u8",
    "S Sport 1": "yayinss.m3u8", 
    "S Sport 2": "yayinss2.m3u8", 
    "Smart Spor 1": "yayinsmarts.m3u8", 
    "Smart Spor 2": "yayinsms2.m3u8",
    "Tivibu Spor 1": "yayint1.m3u8",
    "Tivibu Spor 2": "yayint2.m3u8", 
    "Tivibu Spor 3": "yayint3.m3u8", 
    "Tivibu Spor 4": "yayint4.m3u8",
    "TRT Spor": "yayintrtspor.m3u8",
    "TRT Spor Yıldız": "yayintrtspor2.m3u8", 
    "TRT 1": "yayintrt1.m3u8",
    "A Spor": "yayinas.m3u8",
    "ATV": "yayinatv.m3u8",
    "TV 8": "yayintv8.m3u8",
    "TV 8.5": "yayintv85.m3u8",
    "Sky Sports F1": "yayinf1.m3u8",
    "Eurosport 1": "yayineu1.m3u8",
    "Eurosport 2": "yayineu2.m3u8",
    "TABII Spor": "yayinex7.m3u8",
    "TABII Spor 1": "yayinex1.m3u8", 
    "TABII Spor 2": "yayinex2.m3u8", 
    "TABII Spor 3": "yayinex3.m3u8",
    "TABII Spor 4": "yayinex4.m3u8", 
    "TABII Spor 5": "yayinex5.m3u8", 
    "TABII Spor 6": "yayinex6.m3u8",
    "NBA TV": "yayinnba.m3u8",
    "FB TV": "yayinfb.m3u8", 
    "GS TV": "yayingstve.m3u8", 
    "BJK TV": "yayinbjk.m3u8"
}

def find_matches_in_html(html_content):
    """HTML içinde maçları bulan basit fonksiyon"""
    matches = []
    
    # Tüm href="channel?id=..." ifadelerini bul
    channel_ids = re.findall(r'href=[\'"]?channel\?id=([^\'" >]+)', html_content)
    
    print(f"🔍 Bulunan channel?id= ifadeleri: {len(channel_ids)}")
    
    # Her channel ID için maç bilgilerini bulmaya çalış
    for cid in channel_ids:
        # Bu ID'nin etrafındaki HTML'i bul
        pattern = f'href=[\'"]?channel\\?id={re.escape(cid)}[\'"]?[^>]*>([\\s\\S]*?)</a>'
        block_match = re.search(pattern, html_content)
        
        if block_match:
            block_content = block_match.group(1)
            
            # Date bilgisini ara
            date_match = re.search(r'<div[^>]*class=[\'"]date[\'"][^>]*>([^<]+)<', block_content)
            date = date_match.group(1).strip() if date_match else ""
            
            # Event bilgisini ara
            event_match = re.search(r'<div[^>]*class=[\'"]event[\'"][^>]*>([^<]+)<', block_content)
            event = event_match.group(1).strip() if event_match else ""
            
            # Home bilgisini ara
            home_match = re.search(r'<div[^>]*class=[\'"]home[\'"][^>]*>([^<]+)<', block_content)
            home = home_match.group(1).strip() if home_match else ""
            
            # Away bilgisini ara
            away_match = re.search(r'<div[^>]*class=[\'"]away[\'"][^>]*>([^<]+)<', block_content)
            away = away_match.group(1).strip() if away_match else ""
            
            # Eğer home ve away varsa (ve kanal değilse), bu bir maçtır
            if home and away and home != away and len(home) < 50 and len(away) < 50:
                if "BEIN" not in home.upper() and "TRT" not in home.upper() and "SPOR" not in home.upper():
                    matches.append((cid, date, event, home, away))
    
    return matches

def simple_extract_matches(html_content):
    """Daha basit bir extract yöntemi"""
    matches = []
    
    # Tüm <a> tag'larını bul
    a_tags = re.findall(r'<a[^>]*>.*?</a>', html_content, re.DOTALL)
    
    print(f"🔍 Toplam <a> tag'ı: {len(a_tags)}")
    
    for tag in a_tags:
        # channel?id içerenleri bul
        if 'channel?id=' in tag:
            # ID'yi çıkar
            id_match = re.search(r'channel\?id=([^"\']+)', tag)
            if id_match:
                cid = id_match.group(1)
                
                # İçerikteki text'i al
                # Date
                date_match = re.search(r'class=[\'"]date[\'"][^>]*>([^<]+)<', tag)
                date = date_match.group(1).strip() if date_match else ""
                
                # Event
                event_match = re.search(r'class=[\'"]event[\'"][^>]*>([^<]+)<', tag)
                event = event_match.group(1).strip() if event_match else ""
                
                # Home
                home_match = re.search(r'class=[\'"]home[\'"][^>]*>([^<]+)<', tag)
                home = home_match.group(1).strip() if home_match else ""
                
                # Away
                away_match = re.search(r'class=[\'"]away[\'"][^>]*>([^<]+)<', tag)
                away = away_match.group(1).strip() if away_match else ""
                
                # Teams alternatif (teams class'ı içinde home ve away)
                if not home or not away:
                    teams_match = re.search(r'class=[\'"]teams[\'"][^>]*>.*?class=[\'"]home[\'"][^>]*>([^<]+)<.*?class=[\'"]away[\'"][^>]*>([^<]+)<', tag, re.DOTALL)
                    if teams_match:
                        home = teams_match.group(1).strip()
                        away = teams_match.group(2).strip()
                
                if home and away and home != away:
                    # Kanal değil, maç olduğundan emin ol
                    if not any(x in home.upper() for x in ['BEIN', 'TRT', 'SPORT', 'TV', 'KANAL']):
                        matches.append((cid, date, event, home, away))
    
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
            f.write(html_content[:50000])  # Sadece ilk 50k karakter
        print("📄 HTML kaydedildi: son_html.html (ilk 50k karakter)")
        
        # HTML'nin ilk 2000 karakterini göster
        print("\n🔍 HTML'nin ilk 2000 karakteri:")
        print("-" * 50)
        print(html_content[:2000])
        print("-" * 50)
        
        # İlk yöntemle maçları bul
        matches = find_matches_in_html(html_content)
        
        if not matches:
            print("⚠️ İlk yöntemle maç bulunamadı, alternatif yöntem deneniyor...")
            matches = simple_extract_matches(html_content)
        
        # Benzersiz maçları al
        unique_matches = []
        seen_ids = set()
        for match in matches:
            cid = match[0]
            if cid not in seen_ids:
                seen_ids.add(cid)
                unique_matches.append(match)
        
        print(f"✅ Toplam {len(unique_matches)} benzersiz canlı maç bulundu")
        
        match_count = 0
        for i, (cid, date, event, home, away) in enumerate(unique_matches):
            title = f"{date} | {event} | {home} - {away}"
            
            m3u_list.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{title}')
            m3u_list.append(f"{base_url}{cid}.m3u8")
            match_count += 1
            
            # İlk 5 maçı göster
            if i < 5:
                print(f"   {i+1}. {title} (ID: {cid})")

        # 3. Sabit Kanalları Ekle
        print(f"\n📺 {len(SABIT_KANALLAR)} Sabit spor kanalı ekleniyor...")
        added_channels = set()
        for name, file in SABIT_KANALLAR.items():
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
        
        # Ek kontrol
        print("\n🔍 DEBUG BİLGİLERİ:")
        print(f"HTML uzunluğu: {len(html_content)} karakter")
        
        # channel?id= ifadelerini say
        channel_count = len(re.findall(r'channel\?id=', html_content))
        print(f"'channel?id=' geçiş sayısı: {channel_count}")
        
        # single-match ifadelerini say
        single_match_count = len(re.findall(r'single-match', html_content, re.IGNORECASE))
        print(f"'single-match' geçiş sayısı: {single_match_count}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
