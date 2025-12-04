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

def get_yayinlink_m3u8(channel_id):
    """https://analyticsjs.sbs/load/yayinlink.php?id=XXX endpoint'inden m3u8 al"""
    try:
        yayinlink_url = f"https://analyticsjs.sbs/load/yayinlink.php?id={channel_id}"
        
        yayin_headers = headers.copy()
        yayin_headers['Referer'] = 'https://www.atomsportv480.top/'
        yayin_headers['Origin'] = 'https://www.atomsportv480.top'
        
        response = requests.get(yayinlink_url, headers=yayin_headers, timeout=10)
        
        if response.status_code == 200:
            # Doğrudan m3u8 linki dönüyor olabilir
            content = response.text.strip()
            
            # Eğer m3u8 içeriyorsa
            if '.m3u8' in content:
                return content
            # JSON formatında olabilir
            elif 'http' in content and 'm3u8' in content:
                # Linki bulmaya çalış
                match = re.search(r'(https?://[^\s]+\.m3u8[^\s]*)', content)
                if match:
                    return match.group(1)
        
        return None
        
    except Exception as e:
        #print(f"  ❌ yayinlink hatası: {e}")
        return None

def get_channel_m3u8_new(channel_id, base_domain):
    """Yeni PHP mantığı ile m3u8 linkini al"""
    try:
        # Önce yayinlink.php'yi dene
        m3u8_url = get_yayinlink_m3u8(channel_id)
        if m3u8_url:
            return m3u8_url
        
        # Eski yöntem (matches?id=)
        matches_url = f"{base_domain}/matches?id={channel_id}"
        response = requests.get(matches_url, headers=headers, timeout=10)
        html = response.text
        
        # fetch URL'sini bul
        fetch_match = re.search(r'fetch\("(.*?)"', html)
        if fetch_match:
            fetch_url = fetch_match.group(1).strip()
            
            custom_headers = headers.copy()
            custom_headers['Origin'] = base_domain
            custom_headers['Referer'] = base_domain
            
            if not fetch_url.endswith(channel_id):
                fetch_url = fetch_url + channel_id
            
            response2 = requests.get(fetch_url, headers=custom_headers, timeout=10)
            fetch_data = response2.text
            
            # m3u8 linkini bul
            m3u8_match = re.search(r'"deismackanal":"(.*?)"', fetch_data)
            if m3u8_match:
                return m3u8_match.group(1).replace('\\', '')
        
        return None
        
    except Exception as e:
        return None

# HTML'den tüm kanal ID'lerini çıkar (verdiğiniz HTML)
html_content = """
[YUKARIDAKİ HTML BURAYA]
"""

def extract_all_channel_ids_from_html(html_text):
    """HTML'den tüm kanal ID'lerini çıkar"""
    print("HTML'den kanal ID'leri çıkarılıyor...")
    
    # Tüm matches?id= pattern'lerini bul
    pattern1 = r'matches\?id=([^"\'\s&]+)'
    matches1 = re.findall(pattern1, html_text)
    
    # Tüm href="matches?id=XXX" pattern'lerini bul
    pattern2 = r'href="matches\?id=([^"]+)"'
    matches2 = re.findall(pattern2, html_text)
    
    # Tüm pattern'leri birleştir
    all_matches = matches1 + matches2
    
    # Benzersiz ID'leri al
    unique_ids = list(set(all_matches))
    
    print(f"Toplam {len(unique_ids)} benzersiz kanal ID'si bulundu")
    
    # ID'leri gruplara ayır
    channels = []
    
    for channel_id in unique_ids:
        # Kanal adını belirle
        channel_name = get_channel_name(channel_id)
        
        # Grubu belirle
        group = get_channel_group(channel_id, channel_name)
        
        channels.append({
            'id': channel_id,
            'name': channel_name,
            'group': group
        })
    
    return channels

def get_channel_name(channel_id):
    """Kanal ID'sinden isim oluştur"""
    # Özel isimlendirmeler
    name_map = {
        # TV Kanalları
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
        
        # Futbol Maçları
        'arsenal-brentford-futboi': 'Arsenal vs Brentford',
        'leeds-united-chelsea-futboi': 'Leeds United vs Chelsea',
        'liverpool-sunderland-futboi': 'Liverpool vs Sunderland',
        'yalova-fk-gaziantep-fk-futboi': 'Yalova FK vs Gaziantep FK',
        'igdir-fk-orduspor-1967-sk-futboi': 'Iğdır FK vs Orduspor 1967',
        'silifke-belediye-spor-antalyaspor-futboi': 'Silifke vs Antalyaspor',
        'bologna-parma-futboi': 'Bologna vs Parma',
        'corum-fk-alanyaspor-futboi': 'Çorum FK vs Alanyaspor',
        'manchester-united-west-ham-united-futboi': 'Man United vs West Ham',
        'lazio-milan-futboi': 'Lazio vs Milan',
        
        # Basketbol Maçları
        'anadolu-efes-real-madrid-basketboi': 'Anadolu Efes vs Real Madrid',
        'zalgiris-kaunas-maccabi-tel-aviv-basketboi': 'Zalgiris vs Maccabi',
        'olympiakos-fenerbahce-beko-basketboi': 'Olympiakos vs Fenerbahçe',
    }
    
    if channel_id in name_map:
        return name_map[channel_id]
    
    # Sayısal ID'ler için
    if channel_id.isdigit():
        return f"Maç {channel_id}"
    
    # Genel format
    name = channel_id.replace('-', ' ').replace('_', ' ').title()
    
    # Spor türlerini düzelt
    if 'futboi' in channel_id:
        name = name.replace('Futboi', '').strip()
    elif 'basketboi' in channel_id:
        name = name.replace('Basketboi', '').strip()
    
    return name

def get_channel_group(channel_id, channel_name):
    """Kanal grubunu belirle"""
    # TV Kanalları
    tv_keywords = ['bein-sports', 's-sport', 'tivibu', 'trt', 'aspor']
    if any(keyword in channel_id for keyword in tv_keywords):
        return "TV Kanalları"
    
    # Futbol
    if 'futboi' in channel_id or 'futbol' in channel_name.lower():
        return "Futbol"
    
    # Basketbol
    if 'basketboi' in channel_id or 'basketbol' in channel_name.lower():
        return "Basketbol"
    
    # Tenis
    if 'tenis' in channel_id.lower():
        return "Tenis"
    
    # Voleybol
    if 'voleybol' in channel_id.lower():
        return "Voleybol"
    
    # Buz Hokeyi
    if 'hokey' in channel_id.lower():
        return "Buz Hokeyi"
    
    # Masa Tenisi
    if 'masa' in channel_id.lower():
        return "Masa Tenisi"
    
    # e-Sporlar
    if 'espor' in channel_id.lower():
        return "e-Sporlar"
    
    return "Diğer"

def test_channels_and_get_m3u8(channels, base_domain, limit=None):
    """Kanalları test et ve m3u8 linklerini al"""
    if not channels:
        print("❌ Test edilecek kanal yok!")
        return []
    
    if limit:
        channels = channels[:limit]
    
    print(f"\n{len(channels)} kanal test ediliyor...")
    
    working_channels = []
    
    for i, channel in enumerate(channels):
        channel_id = channel["id"]
        channel_name = channel["name"]
        group = channel["group"]
        
        print(f"{i+1:3d}. {channel_name[:40]:40s}...", end=" ", flush=True)
        
        # m3u8 linkini al
        m3u8_url = get_channel_m3u8_new(channel_id, base_domain)
        
        if m3u8_url:
            print(f"{GREEN}✓{RESET}")
            channel['url'] = m3u8_url
            working_channels.append(channel)
        else:
            print("✗")
        
        # Her 5 kanalda bir bekle
        if (i + 1) % 5 == 0:
            time.sleep(0.3)
    
    return working_channels

def create_m3u_file(working_channels, base_domain):
    """M3U dosyası oluştur"""
    if not working_channels:
        print("❌ M3U oluşturmak için çalışan kanal yok!")
        return
    
    print(f"\nM3U dosyası oluşturuluyor: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Gruplara göre sırala
        groups = {}
        for channel in working_channels:
            group = channel.get("group", "Diğer")
            if group not in groups:
                groups[group] = []
            groups[group].append(channel)
        
        # Her grup için
        total_count = 0
        for group_name, group_channels in groups.items():
            print(f"{group_name}: {len(group_channels)} kanal")
            total_count += len(group_channels)
            
            for channel in group_channels:
                channel_id = channel["id"]
                channel_name = channel["name"]
                m3u8_url = channel["url"]
                
                # EXTINF satırı
                f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" group-title="{group_name}",{channel_name}\n')
                
                # VLC seçenekleri
                f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
                
                # URL
                f.write(m3u8_url + "\n")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {total_count} çalışan kanal eklendi.")
    
    return total_count

def main():
    print(f"{GREEN}AtomSporTV M3U Oluşturucu - Tüm Kanal Tarayıcı{RESET}")
    print("=" * 70)
    
    # 1. Ana domain'i bul
    print("\n1. Ana domain bulunuyor...")
    base_domain = get_base_domain()
    
    # 2. HTML'yi dosyadan oku
    print("\n2. HTML dosyası okunuyor...")
    try:
        with open("atom_page.html", "r", encoding="utf-8") as f:
            html_text = f.read()
        
        # 3. HTML'den tüm kanal ID'lerini çıkar
        print("\n3. HTML'den kanal ID'leri çıkarılıyor...")
        all_channels = extract_all_channel_ids_from_html(html_text)
        
    except FileNotFoundError:
        print("❌ atom_page.html dosyası bulunamadı!")
        print("\nLütfen HTML'yi 'atom_page.html' adıyla kaydedin veya")
        print("aşağıdaki linkten HTML'yi indirin:")
        print("https://gist.githubusercontent.com/...")
        return
    
    if not all_channels:
        print("❌ HTML'den kanal ID'si çıkarılamadı!")
        return
    
    # 4. Kanalları test et (ilk 60 kanal)
    print("\n4. Kanallar test ediliyor (bu biraz zaman alabilir)...")
    working_channels = test_channels_and_get_m3u8(all_channels, base_domain, limit=60)
    
    if not working_channels:
        print("❌ Hiç çalışan kanal bulunamadı!")
        return
    
    # 5. M3U oluştur
    print("\n5. M3U dosyası oluşturuluyor...")
    total_count = create_m3u_file(working_channels, base_domain)
    
    # 6. Sonuçları göster
    print("\n" + "=" * 70)
    print("ÇALIŞAN KANALLAR:")
    
    groups = {}
    for channel in working_channels:
        group = channel.get("group", "Diğer")
        if group not in groups:
            groups[group] = []
        groups[group].append(channel["name"])
    
    for group_name, channel_names in groups.items():
        print(f"\n{group_name} ({len(channel_names)}):")
        for i, name in enumerate(channel_names[:10], 1):
            print(f"  {i:2d}. {name}")
        
        if len(channel_names) > 10:
            print(f"  ... ve {len(channel_names) - 10} kanal daha")
    
    # 7. GitHub komutları
    print("\n" + "=" * 70)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "AtomSporTV M3U güncellemesi"')
    print("  git push")
    
    # 8. Örnek çıktı
    print("\n" + "=" * 70)
    print("M3U dosyasından örnek satırlar:")
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:8]):
                if line.strip():
                    print(f"  {line.rstrip()}")
    except:
        pass

if __name__ == "__main__":
    main()
