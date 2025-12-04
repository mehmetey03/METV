import requests
import re
import time

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
        return None

def get_all_possible_channels():
    """Sadece TV kanallarını oluştur"""
    print("TV kanal ID'leri oluşturuluyor...")
    
    channels = []
    
    # SADECE TV KANALLARI
    tv_channels = [
        # BEIN SPORTS
        ("bein-sports-1", "BEIN SPORTS 1"),
        ("bein-sports-2", "BEIN SPORTS 2"),
        ("bein-sports-3", "BEIN SPORTS 3"),
        ("bein-sports-4", "BEIN SPORTS 4"),
        
        # S SPORT
        ("s-sport", "S SPORT"),
        ("s-sport-2", "S SPORT 2"),
        
        # TİVİBU SPOR
        ("tivibu-spor-1", "TİVİBU SPOR 1"),
        ("tivibu-spor-2", "TİVİBU SPOR 2"),
        ("tivibu-spor-3", "TİVİBU SPOR 3"),
        
        # TRT
        ("trt-spor", "TRT SPOR"),
        ("trt-yildiz", "TRT YILDIZ"),
        ("trt1", "TRT 1"),
        
        # DİĞER
        ("aspor", "ASPOR"),
    ]
    
    for channel_id, name in tv_channels:
        channels.append({
            'id': channel_id,
            'name': name,
            'group': 'TV Kanalları'
        })
    
    print(f"Toplam {len(channels)} TV kanal ID'si oluşturuldu")
    return channels

def test_channels(channels, base_domain):
    """Kanaları test et ve çalışanları bul"""
    print(f"\n{len(channels)} kanal test ediliyor...")
    
    working_channels = []
    
    for i, channel in enumerate(channels):
        channel_id = channel["id"]
        channel_name = channel["name"]
        group = channel["group"]
        
        print(f"{i+1:2d}. {channel_name}...", end=" ", flush=True)
        
        m3u8_url = get_channel_m3u8(channel_id, base_domain)
        
        if m3u8_url:
            print(f"{GREEN}✓{RESET}")
            channel['url'] = m3u8_url
            working_channels.append(channel)
        else:
            print("✗")
    
    return working_channels

def create_m3u(working_channels, base_domain):
    """M3U dosyası oluştur"""
    print(f"\nM3U dosyası oluşturuluyor...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for channel in working_channels:
            channel_id = channel["id"]
            channel_name = channel["name"]
            m3u8_url = channel["url"]
            
            # EXTINF satırı
            f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" group-title="TV Kanalları",{channel_name}\n')
            
            # VLC seçenekleri
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            
            # URL
            f.write(m3u8_url + "\n")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {len(working_channels)} çalışan kanal eklendi.")

def main():
    print(f"{GREEN}AtomSporTV M3U Oluşturucu{RESET}")
    print("=" * 60)
    
    # 1. Ana domain'i bul
    print("\n1. Ana domain bulunuyor...")
    base_domain = get_base_domain()
    
    # 2. TV kanallarını oluştur
    print("\n2. TV kanal ID'leri oluşturuluyor...")
    all_channels = get_all_possible_channels()
    
    # 3. Kanalları test et
    print("\n3. Kanallar test ediliyor...")
    working_channels = test_channels(all_channels, base_domain)
    
    if not working_channels:
        print("\n❌ Hiç çalışan kanal bulunamadı!")
        return
    
    # 4. M3U oluştur
    print("\n4. M3U dosyası oluşturuluyor...")
    create_m3u(working_channels, base_domain)
    
    # 5. Sonuçları göster
    print("\n" + "=" * 60)
    print("ÇALIŞAN KANALLAR:")
    
    for channel in working_channels:
        print(f"  ✓ {channel['name']}")
    
    # 6. GitHub komutları
    print("\n" + "=" * 60)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "AtomSporTV M3U güncellemesi"')
    print("  git push")

if __name__ == "__main__":
    main()
