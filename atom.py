import requests
import re
import json

# AtomSporTV
START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://url24.link/'
}

def get_base_domain():
    """Ana domain'i bul"""
    try:
        response = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        
        if 'location' in response.headers:
            location1 = response.headers['location']
            response2 = requests.get(location1, headers=headers, allow_redirects=False, timeout=10)
            
            if 'location' in response2.headers:
                base_domain = response2.headers['location'].strip().rstrip('/')
                print(f"Ana Domain: {base_domain}")
                return base_domain
        
        return "https://www.atomsportv480.top"
        
    except Exception as e:
        print(f"Domain hatası: {e}")
        return "https://www.atomsportv480.top"

def get_channel_m3u8(channel_id, base_domain):
    """PHP mantığı ile m3u8 linkini al"""
    try:
        # 1. matches?id= endpoint
        matches_url = f"{base_domain}/matches?id={channel_id}"
        response = requests.get(matches_url, headers=headers, timeout=10)
        html = response.text
        
        # 2. fetch URL'sini bul
        fetch_match = re.search(r'fetch\("(.*?)"', html)
        if not fetch_match:
            # Alternatif pattern
            fetch_match = re.search(r'fetch\(\s*["\'](.*?)["\']', html)
        
        if fetch_match:
            fetch_url = fetch_match.group(1).strip()
            
            # 3. fetch URL'sine istek yap
            custom_headers = headers.copy()
            custom_headers['Origin'] = base_domain
            custom_headers['Referer'] = base_domain
            
            if not fetch_url.endswith(channel_id):
                fetch_url = fetch_url + channel_id
            
            response2 = requests.get(fetch_url, headers=custom_headers, timeout=10)
            fetch_data = response2.text
            
            # 4. m3u8 linkini bul
            m3u8_match = re.search(r'"deismackanal":"(.*?)"', fetch_data)
            if m3u8_match:
                m3u8_url = m3u8_match.group(1).replace('\\', '')
                return m3u8_url
            
            # Alternatif pattern
            m3u8_match = re.search(r'"(?:stream|url|source)":\s*"(.*?\.m3u8)"', fetch_data)
            if m3u8_match:
                return m3u8_match.group(1).replace('\\', '')
        
        return None
        
    except Exception as e:
        print(f"  ❌ {channel_id}: {e}")
        return None

def get_channels_from_api():
    """API veya başka kaynaktan kanalları çek"""
    print("\nAPI'dan kanal listesi çekiliyor...")
    
    # Farklı endpoint'leri dene
    endpoints = [
        "https://www.atomsportv480.top/",
        "https://www.atomsportv480.top/channel.html",
        "https://www.atomsportv480.top/matches",
    ]
    
    all_channels = []
    
    for endpoint in endpoints:
        try:
            print(f"\n{endpoint} deneniyor...")
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                html = response.text
                
                # Pattern 1: matches?id=XXX
                matches1 = re.findall(r'matches\?id=([^"\'\s&]+)', html)
                
                # Pattern 2: href="matches?id=XXX"
                matches2 = re.findall(r'href="matches\?id=([^"]+)"', html)
                
                # Pattern 3: data-id veya data-match
                matches3 = re.findall(r'data-(?:id|match)="([^"]+)"', html)
                
                # Pattern 4: onclick içinde
                matches4 = re.findall(r"onclick=[\"'].*?matches\?id=([^\"'\s&]+)", html)
                
                all_matches = matches1 + matches2 + matches3 + matches4
                
                if all_matches:
                    unique_matches = list(set(all_matches))
                    print(f"  {len(unique_matches)} kanal bulundu")
                    
                    for match_id in unique_matches[:20]:  # İlk 20
                        if match_id and len(match_id) > 3:
                            # Kanal adını formatla
                            name = match_id.replace('-', ' ').replace('_', ' ').title()
                            
                            if 'bein' in match_id.lower():
                                name = match_id.upper().replace('-', ' ')
                            elif 'trt' in match_id.lower():
                                name = match_id.upper()
                            elif 'futboi' in match_id:
                                name = name.replace('Futboi', '').strip() + ' (Futbol)'
                            elif 'basketboi' in match_id:
                                name = name.replace('Basketboi', '').strip() + ' (Basketbol)'
                            
                            # Grup belirle
                            group = "TV Kanalları"
                            if any(x in match_id.lower() for x in ['futboi', 'futbol']):
                                group = "Futbol"
                            elif any(x in match_id.lower() for x in ['basketboi', 'basketbol']):
                                group = "Basketbol"
                            elif 'tenis' in match_id.lower():
                                group = "Tenis"
                            elif 'voleybol' in match_id.lower():
                                group = "Voleybol"
                            elif 'hokey' in match_id.lower():
                                group = "Buz Hokeyi"
                            
                            all_channels.append({
                                'id': match_id,
                                'name': name,
                                'group': group
                            })
                    
                    return all_channels
                    
        except Exception as e:
            print(f"  Hata: {e}")
            continue
    
    # Hiç kanal bulunamazsa statik listeyi kullan
    print("\nAPI'dan kanal bulunamadı, statik liste kullanılıyor...")
    return get_static_channels()

def get_static_channels():
    """Statik kanal listesi (fallback)"""
    print("Statik kanal listesi oluşturuluyor...")
    
    channels = []
    
    # TV KANALLARI
    tv_channels = [
        ("bein-sports-1", "BEIN SPORTS 1"),
        ("bein-sports-2", "BEIN SPORTS 2"),
        ("bein-sports-3", "BEIN SPORTS 3"),
        ("bein-sports-4", "BEIN SPORTS 4"),
        ("s-sport", "S SPORT"),
        ("s-sport-2", "S SPORT 2"),
        ("tivibu-spor-1", "TİVİBU SPOR 1"),
        ("tivibu-spor-2", "TİVİBU SPOR 2"),
        ("tivibu-spor-3", "TİVİBU SPOR 3"),
        ("aspor", "ASPOR"),
        ("trt-spor", "TRT SPOR"),
        ("trt-yildiz", "TRT YILDIZ"),
        ("trt1", "TRT 1"),
    ]
    
    for channel_id, name in tv_channels:
        channels.append({
            'id': channel_id,
            'name': name,
            'group': 'TV Kanalları'
        })
    
    # ÖRNEK MAÇLAR
    matches = [
        ("arsenal-brentford-futboi", "Arsenal vs Brentford", "Futbol"),
        ("leeds-united-chelsea-futboi", "Leeds United vs Chelsea", "Futbol"),
        ("liverpool-sunderland-futboi", "Liverpool vs Sunderland", "Futbol"),
        ("anadolu-efes-real-madrid-basketboi", "Anadolu Efes vs Real Madrid", "Basketbol"),
        ("zalgiris-kaunas-maccabi-tel-aviv-basketboi", "Zalgiris vs Maccabi Tel Aviv", "Basketbol"),
        ("olympiakos-fenerbahce-beko-basketboi", "Olympiakos vs Fenerbahçe", "Basketbol"),
    ]
    
    for channel_id, name, group in matches:
        channels.append({
            'id': channel_id,
            'name': name,
            'group': group
        })
    
    return channels

def create_m3u(channels, base_domain):
    """M3U dosyası oluştur"""
    print(f"\nM3U dosyası oluşturuluyor...")
    
    successful_channels = []
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Gruplara göre sırala
        groups = {}
        for channel in channels:
            group = channel.get("group", "Diğer")
            if group not in groups:
                groups[group] = []
            groups[group].append(channel)
        
        # Her grup için
        for group_name, group_channels in groups.items():
            print(f"\n{group_name}:")
            
            for channel in group_channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                
                print(f"  {channel_name}...", end=" ")
                
                # m3u8 linkini al
                m3u8_url = get_channel_m3u8(channel_id, base_domain)
                
                if m3u8_url:
                    print(f"✓")
                    
                    # EXTINF satırı
                    f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" group-title="{group_name}",{channel_name}\n')
                    
                    # VLC seçenekleri
                    f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
                    f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
                    
                    # URL
                    f.write(m3u8_url + "\n")
                    
                    successful_channels.append(channel)
                else:
                    print(f"✗ (link bulunamadı)")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Başarılı kanal sayısı: {len(successful_channels)}")
    
    return successful_channels

def main():
    print(f"{GREEN}AtomSporTV M3U Oluşturucu{RESET}")
    print("=" * 60)
    
    # 1. Ana domain'i bul
    print("\n1. Ana domain bulunuyor...")
    base_domain = get_base_domain()
    
    # 2. Kanal listesini al
    print("\n2. Kanal listesi alınıyor...")
    channels = get_channels_from_api()
    
    print(f"\nToplam {len(channels)} kanal bulundu")
    
    # 3. M3U oluştur
    print("\n3. M3U dosyası oluşturuluyor...")
    successful_channels = create_m3u(channels, base_domain)
    
    # 4. Sonuçları göster
    print("\n" + "=" * 60)
    print("BAŞARILI KANALLAR:")
    
    groups = {}
    for channel in successful_channels:
        group = channel.get("group", "Diğer")
        if group not in groups:
            groups[group] = []
        groups[group].append(channel["name"])
    
    for group_name, channel_names in groups.items():
        print(f"\n{group_name} ({len(channel_names)} kanal):")
        for name in channel_names:
            print(f"  ✓ {name}")
    
    # 5. GitHub komutları
    print("\n" + "=" * 60)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "AtomSporTV M3U güncellemesi"')
    print("  git push")

if __name__ == "__main__":
    main()
