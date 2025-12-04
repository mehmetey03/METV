import requests
import re

# AtomSporTV ana sayfası
ATOMSPORTV_URL = "https://atomsportv480.top/"
OUTPUT_FILE = "atom.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

# Orijinal HTML örneğinden aldığımız kanal listesi
STATIC_CHANNELS = [
    # Maçlar (Futbol)
    {"id": "arsenal-brentford-futboi", "name": "Arsenal vs Brentford", "group": "Futbol"},
    {"id": "17839903", "name": "Brighton & Hove Albion vs Aston Villa", "group": "Futbol TR"},
    {"id": "17839900", "name": "Burnley vs Crystal Palace", "group": "Futbol TR"},
    {"id": "leeds-united-chelsea-futboi", "name": "Leeds United vs Chelsea", "group": "Futbol TR"},
    {"id": "liverpool-sunderland-futboi", "name": "Liverpool vs Sunderland", "group": "Futbol TR"},
    {"id": "yalova-fk-gaziantep-fk-futboi", "name": "Yalova FK vs Gaziantep FK", "group": "Futbol"},
    {"id": "igdir-fk-orduspor-1967-sk-futboi", "name": "Iğdır FK vs Orduspor 1967 SK", "group": "Futbol"},
    {"id": "silifke-belediye-spor-antalyaspor-futboi", "name": "Silifke Belediye Spor vs Antalyaspor", "group": "Futbol"},
    {"id": "bologna-parma-futboi", "name": "Bologna vs Parma", "group": "Futbol"},
    {"id": "corum-fk-alanyaspor-futboi", "name": "Çorum FK vs Alanyaspor", "group": "Futbol"},
    {"id": "manchester-united-west-ham-united-futboi", "name": "Manchester United vs West Ham United", "group": "Futbol"},
    {"id": "lazio-milan-futboi", "name": "Lazio vs Milan", "group": "Futbol"},
    
    # Basketbol
    {"id": "anadolu-efes-real-madrid-basketboi", "name": "Anadolu Efes vs Real Madrid", "group": "Basketbol"},
    {"id": "zalgiris-kaunas-maccabi-tel-aviv-basketboi", "name": "Zalgiris Kaunas vs Maccabi Tel Aviv", "group": "Basketbol"},
    {"id": "olympiakos-fenerbahce-beko-basketboi", "name": "Olympiakos vs Fenerbahçe Beko", "group": "Basketbol"},
    
    # TV Kanalları (Orijinal HTML'den)
    {"id": "bein-sports-1", "name": "BEIN SPORTS 1", "group": "TV Kanalları", "type": "tv"},
    {"id": "bein-sports-2", "name": "BEIN SPORTS 2", "group": "TV Kanalları", "type": "tv"},
    {"id": "bein-sports-3", "name": "BEIN SPORTS 3", "group": "TV Kanalları", "type": "tv"},
    {"id": "bein-sports-4", "name": "BEIN SPORTS 4", "group": "TV Kanalları", "type": "tv"},
    {"id": "s-sport", "name": "S SPORT", "group": "TV Kanalları", "type": "tv"},
    {"id": "s-sport-2", "name": "S SPORT 2", "group": "TV Kanalları", "type": "tv"},
    {"id": "tivibu-spor-1", "name": "TİVİBU SPOR 1", "group": "TV Kanalları", "type": "tv"},
    {"id": "tivibu-spor-2", "name": "TİVİBU SPOR 2", "group": "TV Kanalları", "type": "tv"},
    {"id": "tivibu-spor-3", "name": "TİVİBU SPOR 3", "group": "TV Kanalları", "type": "tv"},
    {"id": "aspor", "name": "ASPOR", "group": "TV Kanalları", "type": "tv"},
    {"id": "trt-spor", "name": "TRT SPOR", "group": "TV Kanalları", "type": "tv"},
    {"id": "trt-yildiz", "name": "TRT YILDIZ", "group": "TV Kanalları", "type": "tv"},
    {"id": "trt1", "name": "TRT1", "group": "TV Kanalları", "type": "tv"},
]

def try_get_live_matches():
    """
    Canlı maçları çekmeyi dene
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    try:
        print(f"Canlı veri çekilmeye çalışılıyor: {ATOMSPORTV_URL}")
        response = requests.get(ATOMSPORTV_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # matches?id= ile başlayan tüm linkleri bul
            matches = re.findall(r'matches\?id=([^"\s&]+)', content)
            if matches:
                unique_matches = list(set(matches))
                print(f"Canlı olarak {len(unique_matches)} maç/kanal bulundu")
                
                channels = []
                for match_id in unique_matches:
                    # Kanal adını belirle
                    channel_name = match_id.replace('-', ' ').title()
                    
                    # Özel isimlendirmeler
                    if 'bein-sports' in match_id:
                        channel_name = match_id.upper().replace('-', ' ')
                    elif 'trt' in match_id:
                        channel_name = match_id.upper()
                    elif 'aspor' in match_id:
                        channel_name = 'ASPOR'
                    elif 's-sport' in match_id:
                        channel_name = match_id.upper().replace('-', ' ')
                    elif 'tivibu' in match_id:
                        channel_name = match_id.upper().replace('-', ' ')
                    
                    # Grup belirle
                    group = "TV Kanalları"
                    if any(sport in match_id for sport in ['futboi', 'futbol']):
                        group = "Futbol"
                    elif any(sport in match_id for sport in ['basketboi', 'basketbol']):
                        group = "Basketbol"
                    elif 'tenis' in match_id.lower():
                        group = "Tenis"
                    elif 'voleybol' in match_id.lower():
                        group = "Voleybol"
                    
                    channels.append({
                        "id": match_id,
                        "name": channel_name,
                        "group": group
                    })
                
                return channels
            
        print("Canlı veri alınamadı, statik liste kullanılacak")
        return []
        
    except Exception as e:
        print(f"Canlı veri hatası: {e}")
        return []

def create_m3u(channels):
    """
    M3U dosyası oluştur
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Gruplara göre sırala
        groups = {}
        for channel in channels:
            group = channel.get("group", "Diğer")
            if group not in groups:
                groups[group] = []
            groups[group].append(channel)
        
        # Her grup için kanalları yaz
        for group_name, group_channels in groups.items():
            print(f"{group_name}: {len(group_channels)} kanal")
            
            for channel in group_channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                
                # M3U8 URL'si
                m3u8_url = f"{ATOMSPORTV_URL}matches?id={channel_id}"
                
                # EXTINF satırı
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" group-title="{group_name}",{channel_name}\n')
                
                # VLC seçenekleri
                f.write(f'#EXTVLCOPT:http-referrer={ATOMSPORTV_URL}\n')
                f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n')
                
                # URL
                f.write(m3u8_url + "\n")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {len(channels)} kanal eklendi.")

def main():
    print(f"{GREEN}AtomSporTV M3U Oluşturucu{RESET}")
    print("=" * 50)
    
    # 1. Önce canlı veriyi dene
    print("\n1. Canlı veri çekiliyor...")
    live_channels = try_get_live_matches()
    
    # 2. Canlı veri varsa onu kullan, yoksa statik listeyi kullan
    if live_channels:
        print(f"   {len(live_channels)} canlı kanal bulundu")
        channels_to_use = live_channels
    else:
        print("   Canlı veri bulunamadı, statik liste kullanılıyor...")
        channels_to_use = STATIC_CHANNELS
    
    # 3. M3U oluştur
    print("\n2. M3U dosyası oluşturuluyor...")
    create_m3u(channels_to_use)
    
    # 4. Örnek çıktı göster
    print("\n" + "=" * 50)
    print("İlk 10 kanal:")
    for i, channel in enumerate(channels_to_use[:10]):
        print(f"  {i+1}. [{channel.get('group', 'Diğer')}] {channel['name']}")
    
    print("\n" + "=" * 50)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "AtomSporTV M3U güncellemesi"')
    print("  git push")
    
    # 5. Dosya içeriğini göster (ilk 5 satır)
    print(f"\n{OUTPUT_FILE} dosyasının ilk 5 satırı:")
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(f"  {line.rstrip()}")
                else:
                    break
    except:
        pass

if __name__ == "__main__":
    main()
