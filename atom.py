import requests
import re

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
        #print(f"  ❌ {channel_id}: {e}")
        return None

def extract_channels_from_html(html_content):
    """HTML'den tüm kanal ID'lerini çıkar"""
    print("HTML'den kanal ID'leri çıkarılıyor...")
    
    channels = []
    
    # Pattern 1: matches?id=XXX
    matches1 = re.findall(r'matches\?id=([^"\'\s&]+)', html_content)
    
    # Pattern 2: href="matches?id=XXX"
    matches2 = re.findall(r'href="matches\?id=([^"]+)"', html_content)
    
    # Pattern 3: data-matchtype içerenler
    matches3 = re.findall(r'data-matchtype="[^"]*".*?href="matches\?id=([^"]+)"', html_content, re.DOTALL)
    
    # Tüm eşleşmeleri birleştir
    all_matches = matches1 + matches2 + matches3
    
    if all_matches:
        # Benzersiz değerleri al
        unique_matches = list(set(all_matches))
        print(f"HTML'den {len(unique_matches)} benzersiz kanal ID'si bulundu")
        
        for channel_id in unique_matches:
            if channel_id and len(channel_id) > 3:
                # Kanal adını belirle
                channel_name = format_channel_name(channel_id)
                
                # Grup belirle
                group = determine_group(channel_id, channel_name)
                
                channels.append({
                    'id': channel_id,
                    'name': channel_name,
                    'group': group
                })
    
    return channels

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
        'olympiakos-fenerbahce-beko-basketboi': 'Olympiakos vs Fenerbahçe Beko',
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

def determine_group(channel_id, channel_name):
    """Kanal grubunu belirle"""
    # TV kanalları
    tv_keywords = ['bein', 'trt', 'aspor', 'tivibu', 's-sport', 'sport', 'tv']
    if any(keyword in channel_id.lower() for keyword in tv_keywords):
        return "TV Kanalları"
    
    # Spor türleri
    if 'futboi' in channel_id or 'futbol' in channel_name.lower():
        return "Futbol"
    elif 'basketboi' in channel_id or 'basketbol' in channel_name.lower():
        return "Basketbol"
    elif 'tenis' in channel_id.lower() or 'tenis' in channel_name.lower():
        return "Tenis"
    elif 'voleybol' in channel_id.lower() or 'voleybol' in channel_name.lower():
        return "Voleybol"
    elif 'hokey' in channel_id.lower() or 'hokey' in channel_name.lower():
        return "Buz Hokeyi"
    elif 'masa' in channel_id.lower() or 'masa' in channel_name.lower():
        return "Masa Tenisi"
    elif 'espor' in channel_id.lower() or 'e-spor' in channel_name.lower():
        return "e-Sporlar"
    
    return "Diğer"

def get_dynamic_channels():
    """Dinamik olarak yüklenen kanalları al"""
    print("\nDinamik kanallar alınıyor...")
    
    try:
        # Fetch API endpoint'inden veri al
        fetch_url = "https://analyticsjs.sbs/load/matches.php"
        response = requests.get(fetch_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            html = response.text
            return extract_channels_from_html(html)
        else:
            print(f"Fetch API hatası: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Fetch hatası: {e}")
        return []

def get_static_html():
    """Statik HTML'yi al (debug için)"""
    print("Statik HTML analiz ediliyor...")
    
    # Burada verdiğiniz HTML'yi kullanacağız
    html_content = """
    [YUKARIDAKİ HTML İÇERİĞİ BURAYA GELECEK]
    """
    
    return extract_channels_from_html(html_content)

def test_and_create_m3u(channels, base_domain, max_test=None):
    """Kanalları test et ve M3U oluştur"""
    if not channels:
        print("❌ Test edilecek kanal yok!")
        return []
    
    if max_test:
        channels = channels[:max_test]
    
    print(f"\n{len(channels)} kanal test ediliyor...")
    
    working_channels = []
    
    for i, channel in enumerate(channels):
        channel_id = channel["id"]
        channel_name = channel["name"]
        group = channel["group"]
        
        print(f"{i+1:3d}. {channel_name[:40]:40s}...", end=" ", flush=True)
        
        m3u8_url = get_channel_m3u8(channel_id, base_domain)
        
        if m3u8_url:
            print(f"{GREEN}✓{RESET}")
            channel['url'] = m3u8_url
            working_channels.append(channel)
        else:
            print("✗")
    
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
        for group_name, group_channels in groups.items():
            print(f"{group_name}: {len(group_channels)} kanal")
            
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
    print(f"Toplam {len(working_channels)} çalışan kanal eklendi.")

def main():
    print(f"{GREEN}AtomSporTV M3U Oluşturucu - HTML Parser{RESET}")
    print("=" * 70)
    
    # 1. Ana domain'i bul
    print("\n1. Ana domain bulunuyor...")
    base_domain = get_base_domain()
    
    # 2. Dinamik kanalları al
    print("\n2. Dinamik kanallar alınıyor...")
    dynamic_channels = get_dynamic_channels()
    
    # 3. Eğer dinamik kanal yoksa, statik HTML'yi kullan
    if not dynamic_channels:
        print("Dinamik kanal bulunamadı, verilen HTML kullanılıyor...")
        
        # Verdiğiniz HTML'yi dosyadan oku
        try:
            with open("atom_page.html", "r", encoding="utf-8") as f:
                html_content = f.read()
                dynamic_channels = extract_channels_from_html(html_content)
        except:
            print("HTML dosyası bulunamadı, örnek HTML kullanılıyor...")
            # Burada sizin verdiğiniz HTML kısmını kullanabiliriz
            # Şimdilik boş bırakalım
    
    print(f"\nToplam {len(dynamic_channels)} kanal bulundu")
    
    if not dynamic_channels:
        print("❌ Hiç kanal bulunamadı!")
        return
    
    # 4. İlk 50 kanalı test et
    print("\n3. Kanallar test ediliyor...")
    working_channels = test_and_create_m3u(dynamic_channels, base_domain, max_test=50)
    
    # 5. M3U oluştur
    print("\n4. M3U dosyası oluşturuluyor...")
    create_m3u_file(working_channels, base_domain)
    
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
        for name in channel_names[:10]:  # İlk 10'u göster
            print(f"  ✓ {name}")
        
        if len(channel_names) > 10:
            print(f"  ... ve {len(channel_names) - 10} kanal daha")
    
    # 7. GitHub komutları
    print("\n" + "=" * 70)
    print("GitHub komutları:")
    print(f"  git add {OUTPUT_FILE}")
    print('  git commit -m "AtomSporTV M3U güncellemesi"')
    print("  git push")

if __name__ == "__main__":
    main()
