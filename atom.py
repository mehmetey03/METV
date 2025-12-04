import requests
import re

# Başlangıç URL'si
START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36'
}

def follow_redirects(start_url):
    """Yönlendirmeleri takip ederek asıl domain'i bul"""
    print(f"Yönlendirme takip ediliyor: {start_url}")
    
    try:
        # İlk istek
        response = requests.get(start_url, headers=headers, allow_redirects=False, timeout=10)
        
        # Location header'ını kontrol et
        if 'location' in response.headers:
            location1 = response.headers['location'].strip()
            print(f"1. Yönlendirme: {location1}")
            
            # İkinci istek
            response2 = requests.get(location1, headers=headers, allow_redirects=False, timeout=10)
            
            if 'location' in response2.headers:
                base_domain = response2.headers['location'].strip()
                print(f"2. Yönlendirme (Ana Domain): {base_domain}")
                return base_domain.rstrip('/')
        
        # Eğer yönlendirme yoksa veya farklı bir yapıdaysa
        print("Yönlendirme bulunamadı, direkt URL kullanılıyor")
        return "https://atomsportv480.top"
        
    except Exception as e:
        print(f"Yönlendirme hatası: {e}")
        return "https://atomsportv480.top"

def get_channel_list(base_domain):
    """Kanal listesini çek"""
    print(f"\nKanal listesi çekiliyor: {base_domain}")
    
    try:
        # Ana sayfayı çek
        response = requests.get(base_domain, headers=headers, timeout=10)
        html = response.text
        
        # matches?id= pattern'lerini bul
        matches = re.findall(r'matches\?id=([^"\'\s&]+)', html)
        
        if matches:
            unique_matches = list(set(matches))
            print(f"Bulunan kanallar: {len(unique_matches)}")
            
            # Her kanal için detaylı bilgi çek
            channels = []
            for match_id in unique_matches[:50]:  # İlk 50 kanal
                channel_info = get_channel_info(base_domain, match_id)
                if channel_info:
                    channels.append(channel_info)
            
            return channels
        else:
            print("HTML'de match bulunamadı, alternatif yaklaşım...")
            
            # Alternatif: Statik kanal listesi
            return get_static_channels()
            
    except Exception as e:
        print(f"Kanal listesi çekme hatası: {e}")
        return get_static_channels()

def get_channel_info(base_domain, channel_id):
    """Kanal bilgilerini ve m3u8 linkini al"""
    try:
        # matches endpoint'ini çağır
        matches_url = f"{base_domain}/matches?id={channel_id}"
        response = requests.get(matches_url, headers=headers, timeout=10)
        html = response.text
        
        # fetch URL'sini bul (PHP'deki gibi)
        fetch_match = re.search(r'fetch\("(.*?)"', html)
        if fetch_match:
            fetch_url = fetch_match.group(1).strip()
            
            # Origin ve Referer header'larını ekle
            custom_headers = headers.copy()
            custom_headers['Origin'] = base_domain
            custom_headers['Referer'] = base_domain
            
            # Fetch URL'sine istek yap
            if not fetch_url.endswith(channel_id):
                fetch_url = fetch_url + channel_id
            
            response2 = requests.get(fetch_url, headers=custom_headers, timeout=10)
            fetch_data = response2.text
            
            # m3u8 linkini bul
            m3u8_match = re.search(r'"deismackanal":"(.*?)"', fetch_data)
            if m3u8_match:
                m3u8_url = m3u8_match.group(1).replace('\\', '')
                
                # Kanal adını belirle
                channel_name = format_channel_name(channel_id)
                
                # Grup belirle
                group = "TV Kanalları"
                if any(sport in channel_id.lower() for sport in ['futboi', 'futbol']):
                    group = "Futbol"
                elif any(sport in channel_id.lower() for sport in ['basketboi', 'basketbol']):
                    group = "Basketbol"
                elif 'tenis' in channel_id.lower():
                    group = "Tenis"
                elif 'voleybol' in channel_id.lower():
                    group = "Voleybol"
                elif any(channel in channel_id.lower() for channel in ['bein', 'trt', 'aspor', 'tivibu', 's-sport']):
                    group = "TV Kanalları"
                
                return {
                    'id': channel_id,
                    'name': channel_name,
                    'group': group,
                    'url': m3u8_url,
                    'referer': base_domain
                }
        
        print(f"  ⚠️ {channel_id}: m3u8 linki bulunamadı")
        return None
        
    except Exception as e:
        print(f"  ❌ {channel_id}: Hata - {e}")
        return None

def format_channel_name(channel_id):
    """Kanal ID'sinden okunabilir isim oluştur"""
    # Özel isimlendirmeler
    special_names = {
        'bein-sports-1': 'BEIN SPORTS 1',
        'bein-sports-2': 'BEIN SPORTS 2', 
        'bein-sports-3': 'BEIN SPORTS 3',
        'bein-sports-4': 'BEIN SPORTS 4',
        's-sport': 'S SPORT',
        's-sport-2': 'S SPORT 2',
        'tivibu-spor-1': 'TİVİBU SPOR 1',
        'tivibu-spor-2': 'TİVİBU SPOR 2',
        'tivibu-spor-3': 'TİVİBU SPOR 3',
        'aspor': 'ASPOR',
        'trt-spor': 'TRT SPOR',
        'trt-yildiz': 'TRT YILDIZ',
        'trt1': 'TRT 1',
        'arsenal-brentford-futboi': 'Arsenal vs Brentford',
        'leeds-united-chelsea-futboi': 'Leeds United vs Chelsea',
        'liverpool-sunderland-futboi': 'Liverpool vs Sunderland',
        'anadolu-efes-real-madrid-basketboi': 'Anadolu Efes vs Real Madrid',
        'zalgiris-kaunas-maccabi-tel-aviv-basketboi': 'Zalgiris vs Maccabi Tel Aviv',
        'olympiakos-fenerbahce-beko-basketboi': 'Olympiakos vs Fenerbahçe',
    }
    
    if channel_id in special_names:
        return special_names[channel_id]
    
    # Genel format
    name = channel_id.replace('-', ' ').replace('_', ' ').title()
    
    # Futbol/Basketbol maçları için özel format
    if 'futboi' in channel_id:
        name = name.replace('Futboi', '').strip() + ' (Futbol)'
    elif 'basketboi' in channel_id:
        name = name.replace('Basketboi', '').strip() + ' (Basketbol)'
    
    return name

def get_static_channels():
    """Statik kanal listesi (fallback)"""
    print("Statik kanal listesi kullanılıyor...")
    
    static_channels = [
        # TV Kanalları
        {'id': 'bein-sports-1', 'name': 'BEIN SPORTS 1', 'group': 'TV Kanalları'},
        {'id': 'bein-sports-2', 'name': 'BEIN SPORTS 2', 'group': 'TV Kanalları'},
        {'id': 'bein-sports-3', 'name': 'BEIN SPORTS 3', 'group': 'TV Kanalları'},
        {'id': 'bein-sports-4', 'name': 'BEIN SPORTS 4', 'group': 'TV Kanalları'},
        {'id': 's-sport', 'name': 'S SPORT', 'group': 'TV Kanalları'},
        {'id': 's-sport-2', 'name': 'S SPORT 2', 'group': 'TV Kanalları'},
        {'id': 'tivibu-spor-1', 'name': 'TİVİBU SPOR 1', 'group': 'TV Kanalları'},
        {'id': 'tivibu-spor-2', 'name': 'TİVİBU SPOR 2', 'group': 'TV Kanalları'},
        {'id': 'tivibu-spor-3', 'name': 'TİVİBU SPOR 3', 'group': 'TV Kanalları'},
        {'id': 'aspor', 'name': 'ASPOR', 'group': 'TV Kanalları'},
        {'id': 'trt-spor', 'name': 'TRT SPOR', 'group': 'TV Kanalları'},
        {'id': 'trt-yildiz', 'name': 'TRT YILDIZ', 'group': 'TV Kanalları'},
        {'id': 'trt1', 'name': 'TRT 1', 'group': 'TV Kanalları'},
        
        # Örnek maçlar
        {'id': 'arsenal-brentford-futboi', 'name': 'Arsenal vs Brentford', 'group': 'Futbol'},
        {'id': 'leeds-united-chelsea-futboi', 'name': 'Leeds United vs Chelsea', 'group': 'Futbol'},
        {'id': 'liverpool-sunderland-futboi', 'name': 'Liverpool vs Sunderland', 'group': 'Futbol'},
        {'id': 'anadolu-efes-real-madrid-basketboi', 'name': 'Anadolu Efes vs Real Madrid', 'group': 'Basketbol'},
        {'id': 'zalgiris-kaunas-maccabi-tel-aviv-basketboi', 'name': 'Zalgiris vs Maccabi Tel Aviv', 'group': 'Basketbol'},
    ]
    
    # URL'leri oluştur
    for channel in static_channels:
        channel['url'] = f"https://atomsportv480.top/matches?id={channel['id']}"
        channel['referer'] = "https://atomsportv480.top"
    
    return static_channels

def create_m3u(channels):
    """M3U dosyası oluştur"""
    print(f"\nM3U dosyası oluşturuluyor: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Gruplara göre sırala
        groups = {}
        for channel in channels:
            group = channel.get("group", "Diğer")
            if group not in groups:
                groups[group] = []
            groups[group].append(channel)
        
        # Toplam kanal sayısı
        total_channels = sum(len(channels) for channels in groups.values())
        
        # Her grup için kanalları yaz
        for group_name, group_channels in groups.items():
            print(f"  {group_name}: {len(group_channels)} kanal")
            
            for channel in group_channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                channel_url = channel.get("url", f"https://atomsportv480.top/matches?id={channel_id}")
                referer = channel.get("referer", "https://atomsportv480.top")
                
                # EXTINF satırı
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" group-title="{group_name}",{channel_name}\n')
                
                # VLC seçenekleri
                f.write(f'#EXTVLCOPT:http-referrer={referer}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
                
                # URL (gerçek m3u8 linki varsa onu kullan, yoksa matches linkini)
                if 'm3u8' in channel_url or 'mp4' in channel_url or 'ts' in channel_url:
                    f.write(channel_url + "\n")
                else:
                    # Gerçek link bulunamadı, matches linkini kullan
                    f.write(channel_url + "\n")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {total_channels} kanal eklendi.")

def test_single_channel():
    """Tek bir kanalı test et"""
    print("\n" + "="*50)
    print("Tek kanal testi:")
    
    # Test için bir kanal ID'si
    test_id = "bein-sports-1"
    base_domain = follow_redirects(START_URL)
    
    print(f"\nTest kanalı: {test_id}")
    channel_info = get_channel_info(base_domain, test_id)
    
    if channel_info:
        print(f"  ✓ Kanal adı: {channel_info['name']}")
        print(f"  ✓ Grup: {channel_info['group']}")
        print(f"  ✓ URL: {channel_info['url'][:80]}...")
        return True
    else:
        print(f"  ✗ Kanal bilgisi alınamadı")
        return False

def main():
    print(f"{GREEN}AtomSporTV M3U Oluşturucu (PHP Mantığı){RESET}")
    print("=" * 60)
    
    # 1. Önce tek kanal testi yap
    print("\n1. Sistem test ediliyor...")
    test_passed = test_single_channel()
    
    if not test_passed:
        print("\n⚠️ Test başarısız, statik liste kullanılacak")
        channels = get_static_channels()
    else:
        # 2. Yönlendirmeleri takip et
        print("\n2. Ana domain bulunuyor...")
        base_domain = follow_redirects(START_URL)
        
        # 3. Kanal listesini çek
        print("\n3. Kanal listesi alınıyor...")
        channels = get_channel_list(base_domain)
    
    # 4. M3U oluştur
    print("\n4. M3U dosyası oluşturuluyor...")
    create_m3u(channels)
    
    # 5. Örnek çıktı
    print("\n" + "=" * 60)
    print("İlk 10 kanal:")
    for i, channel in enumerate(channels[:10]):
        group = channel.get('group', 'Diğer')
        name = channel['name']
        print(f"  {i+1}. [{group}] {name}")
    
    # 6. GitHub komutları
    print("\n" + "=" * 60)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "AtomSporTV M3U güncellemesi"')
    print("  git push")

if __name__ == "__main__":
    main()
