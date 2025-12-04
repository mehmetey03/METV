import re
import requests
import urllib3
from datetime import datetime
import json

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Kanal adları mapping'i - global olarak tanımla
CHANNEL_NAMES = {
    "saspor": "A Spor",
    "sbeinsports-1": "beIN Sports 1",
    "sbeinsports-2": "beIN Sports 2",
    "sbeinsports-3": "beIN Sports 3",
    "sbeinsports-4": "beIN Sports 4",
    "sbeinsports-5": "beIN Sports 5",
    "sbeinsportshaber": "beIN Sports Haber",
    "sdazn1": "DAZN 1",
    "sdazn2": "DAZN 2",
    "sexxen-1": "Exxen Spor 1",
    "sexxen-2": "Exxen Spor 2",
    "sexxen-3": "Exxen Spor 3",
    "sexxen-4": "Exxen Spor 4",
    "sexxen-5": "Exxen Spor 5",
    "sexxen-6": "Exxen Spor 6",
    "sssport": "S Sport",
    "sssport2": "S Sport 2",
    "sssplus1": "S Sport Plus 1",
    "sssplus2": "S Sport Plus 2",
    "ssmartspor": "Smart Spor",
    "ssmartspor2": "Smart Spor 2",
    "stabiispor-1": "Tabii Spor 1",
    "stabiispor-2": "Tabii Spor 2",
    "stabiispor-3": "Tabii Spor 3",
    "stabiispor-4": "Tabii Spor 4",
    "stabiispor-5": "Tabii Spor 5",
    "stivibuspor-1": "Tivibu Spor 1",
    "stivibuspor-2": "Tivibu Spor 2",
    "stivibuspor-3": "Tivibu Spor 3",
    "stivibuspor-4": "Tivibu Spor 4",
    "strt1": "TRT 1",
    "strtspor": "TRT Spor",
    "strtspor2": "TRT Spor 2",
    "stv8": "TV8",
    "sbeinsportsmax-1": "beIN Sports MAX 1",
    "sbeinsportsmax-2": "beIN Sports MAX 2",
    "seurosport1": "Eurosport 1",
    "seurosport2": "Eurosport 2",
    "sf1": "F1 TV",
    "sufcfightpass": "UFC Fight Pass",
    "smotorsporttv": "Motor Sport TV",
    "smotorvisiontv": "Motor Vision TV",
    "sssportplus1": "S Sport Plus 1"
}

def fetch_url(url):
    """URL'den içerik çek"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        return response.text
    except Exception as e:
        print(f"    ✗ Error fetching {url}: {e}")
        return None

def get_active_domain():
    """Aktif domain'i PHP'deki gibi bul"""
    print("🔍 Searching for active domain...")
    for i in range(15, 4, -1):  # 15'ten 5'e
        url = f"https://www.sporcafe{i}.xyz/"
        print(f"  Trying: {url}")
        html = fetch_url(url)
        if html:
            # Basit kontrol - herhangi bir HTML içeriği varsa kabul et
            if len(html) > 100:  # Minimum 100 karakter
                print(f"  ✓ Active domain found: {url}")
                return {'url': url, 'html': html}
            else:
                print(f"    ✗ Empty or too short response")
        else:
            print(f"    ✗ Could not fetch")
    
    print("  ✗ No active domain found")
    return None

def get_stream_domain(html):
    """HTML'den stream domain'ini bul"""
    patterns = [
        r'https?:\/\/(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        r'https?:\/\/(main\.[0-9a-zA-Z\-]+\.click)',
        r'https?:\/\/(player\.[0-9a-zA-Z\-]+\.click)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return f"https://{match.group(1)}"
    
    return None

def get_all_channels_from_html(html):
    """HTML'den tüm kanal ID'lerini çıkar"""
    # Regex ile tüm data-stream-url değerlerini bul
    pattern = r'data-stream-url="([^"]+)"'
    matches = re.findall(pattern, html)
    unique_channels = list(set(matches))
    
    if unique_channels:
        print(f"  Found {len(unique_channels)} channels in HTML")
        return unique_channels
    
    # Eğer bulamazsak, sabit listeyi kullan
    print("  Using default channel list")
    return [
        "saspor", "sbeinsports-1", "sbeinsports-2", "sbeinsports-3", 
        "sbeinsports-4", "sbeinsportshaber", "sdazn1", "sdazn2",
        "sexxen-1", "sexxen-2", "sexxen-3", "sexxen-4", "sexxen-5", "sexxen-6",
        "sssport", "sssport2", "sssplus1", "sssplus2",
        "ssmartspor", "ssmartspor2", "stabiispor-1", "stabiispor-2",
        "stabiispor-3", "stabiispor-4", "stabiispor-5",
        "stivibuspor-1", "stivibuspor-2", "stivibuspor-3", "stivibuspor-4",
        "strt1", "strtspor", "strtspor2", "stv8"
    ]

def get_stream_links_all_channels(domain_info):
    """Tüm kanallar için stream linklerini al"""
    print("🔗 Fetching stream links...")
    
    # Stream domain'ini bul
    stream_domain = get_stream_domain(domain_info['html'])
    
    if not stream_domain:
        print("  ✗ Could not find stream domain in HTML")
        # Varsayılan bir domain deneyelim
        stream_domain = "https://main.uxsyplayer1.click"
        print(f"  Using default: {stream_domain}")
    
    print(f"  ✓ Stream domain: {stream_domain}")
    
    # HTML'den tüm kanal ID'lerini çıkar
    all_channels = get_all_channels_from_html(domain_info['html'])
    
    if not all_channels:
        print("  ✗ No channels found")
        return None
    
    results = {}
    successful = 0
    
    print(f"  Processing {len(all_channels)} channels...")
    
    for i, channel in enumerate(all_channels, 1):
        channel_name = CHANNEL_NAMES.get(channel, channel)
        print(f"  [{i:2d}/{len(all_channels)}] {channel_name}")
        
        channel_url = f"{stream_domain}/index.php?id={channel}"
        html = fetch_url(channel_url)
        
        if html:
            # adsBaseUrl'yi bul
            ads_patterns = [
                r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'var\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'baseUrl\s*=\s*[\'"]([^\'"]+)'
            ]
            
            found = False
            for pattern in ads_patterns:
                ads_match = re.search(pattern, html)
                if ads_match:
                    base_url = ads_match.group(1)
                    if not base_url.endswith('/'):
                        base_url += '/'
                    
                    stream_url = f"{base_url}{channel}/playlist.m3u8"
                    results[channel] = stream_url
                    successful += 1
                    print(f"      ✓ Stream found")
                    found = True
                    break
            
            if not found:
                print(f"      ✗ No stream URL found")
        else:
            print(f"      ✗ Could not fetch channel page")
    
    print(f"\n  📊 Results: {successful}/{len(all_channels)} streams fetched")
    
    return {
        'referer': domain_info['url'],
        'stream_domain': stream_domain,
        'channels': results,
        'total': len(all_channels),
        'successful': successful
    }

def generate_m3u(stream_info):
    """M3U playlist oluştur"""
    if not stream_info or not stream_info['channels']:
        return "#EXTM3U\n#EXTINF:-1,Error: Could not generate stream links"
    
    output_lines = ["#EXTM3U"]
    
    # Başlık bilgileri
    output_lines.append(f"#PLAYLIST:SPORCAFE TV")
    output_lines.append(f"#GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"#DOMAIN: {stream_info['referer']}")
    output_lines.append(f"#CHANNELS: {stream_info['successful']}/{stream_info['total']}")
    output_lines.append("")
    
    # Kanalları isme göre sırala
    sorted_channels = sorted(
        stream_info['channels'].items(),
        key=lambda x: CHANNEL_NAMES.get(x[0], x[0])
    )
    
    for channel_id, stream_url in sorted_channels:
        channel_name = CHANNEL_NAMES.get(channel_id, channel_id)
        
        # Grup belirle
        group = "SPOR"
        if 'beinsports' in channel_id:
            group = "BEIN SPORTS"
        elif 'dazn' in channel_id:
            group = "DAZN"
        elif 'ssport' in channel_id:
            group = "S SPORT"
        elif 'trt' in channel_id:
            group = "TRT"
        elif 'exxen' in channel_id:
            group = "EXXEN"
        
        # EXTINF satırı
        output_lines.append(f'#EXTINF:-1 tvg-id="{channel_id}" group-title="{group}",{channel_name}')
        output_lines.append(f'#EXTVLCOPT:http-referrer={stream_info["referer"]}')
        output_lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0')
        output_lines.append(stream_url)
        output_lines.append("")
    
    output_lines.append("#EOF")
    
    return "\n".join(output_lines)

def save_files(m3u_content, stream_info):
    """Dosyaları kaydet"""
    try:
        # M3U dosyasını kaydet
        with open('sporcafe.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print("✓ M3U file saved: sporcafe.m3u")
        
        # JSON dosyasını kaydet
        json_data = {
            'generated': datetime.now().isoformat(),
            'domain': stream_info['referer'],
            'stream_domain': stream_info.get('stream_domain', ''),
            'total_channels': stream_info['total'],
            'successful_channels': stream_info['successful'],
            'channels': [
                {
                    'id': channel_id,
                    'name': CHANNEL_NAMES.get(channel_id, channel_id),
                    'url': stream_url,
                    'group': 'BEIN SPORTS' if 'beinsports' in channel_id else 
                            'DAZN' if 'dazn' in channel_id else 
                            'S SPORT' if 'ssport' in channel_id else 
                            'TRT' if 'trt' in channel_id else 
                            'SPOR'
                }
                for channel_id, stream_url in stream_info['channels'].items()
            ]
        }
        
        with open('channels.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print("✓ JSON file saved: channels.json")
        
        return True
        
    except Exception as e:
        print(f"✗ Error saving files: {e}")
        return False

def main():
    print("=" * 60)
    print("SPORCAFE M3U PLAYLIST GENERATOR")
    print("=" * 60)
    
    # 1. Aktif domain'i bul
    print("\n[1/3] Finding active domain...")
    domain_info = get_active_domain()
    
    if not domain_info:
        print("\n✗ ERROR: No active domain found!")
        print("=" * 60)
        print("#EXTM3U\n#EXTINF:-1,Error: No active domain found")
        return
    
    print(f"✓ Active domain: {domain_info['url']}")
    
    # 2. Stream linklerini al
    print("\n[2/3] Fetching stream links...")
    stream_info = get_stream_links_all_channels(domain_info)
    
    if not stream_info or not stream_info['channels']:
        print("\n✗ ERROR: Could not fetch stream links!")
        print("=" * 60)
        print("#EXTM3U\n#EXTINF:-1,Error: Could not generate stream links")
        return
    
    print(f"✓ Successfully fetched {stream_info['successful']} streams")
    
    # 3. M3U playlist oluştur
    print("\n[3/3] Generating M3U playlist...")
    m3u_content = generate_m3u(stream_info)
    
    # 4. Dosyaları kaydet
    save_files(m3u_content, stream_info)
    
    # 5. Sonuçları göster
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Active Domain: {domain_info['url']}")
    print(f"Stream Domain: {stream_info.get('stream_domain', 'N/A')}")
    print(f"Total Channels: {stream_info['total']}")
    print(f"Successful Streams: {stream_info['successful']}")
    print(f"M3U File: sporcafe.m3u")
    print(f"JSON File: channels.json")
    print("=" * 60)
    
    # Örnek kanalları göster
    print("\nSample channels in playlist:")
    print("-" * 40)
    channels_list = list(stream_info['channels'].items())[:8]
    for channel_id, _ in channels_list:
        name = CHANNEL_NAMES.get(channel_id, channel_id)
        print(f"  • {name}")
    
    if stream_info['successful'] > 8:
        print(f"  ... and {stream_info['successful'] - 8} more channels")
    
    print("\n✅ Playlist is ready! Use 'sporcafe.m3u' in your media player.")

if __name__ == "__main__":
    main()
