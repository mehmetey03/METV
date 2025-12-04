import re
import requests
import urllib3
from datetime import datetime

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_url(url):
    """URL'den içerik çek"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        return response.text
    except:
        return None

def get_active_domain():
    """Aktif domain'i PHP'deki gibi bul"""
    for i in range(15, 4, -1):  # 15'ten 5'e
        url = f"https://www.sporcafe{i}.xyz/"
        html = fetch_url(url)
        if html and ('channel-item' in html or 'data-stream-url' in html):
            return {'url': url, 'html': html}
    return None

def get_stream_links(domain_info):
    """Stream linklerini PHP'deki mantıkla al"""
    # Stream domain'ini bul
    stream_domain_match = re.search(
        r'https?:\/\/(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        domain_info['html']
    )
    
    if not stream_domain_match:
        return None
    
    stream_domain = f"https://{stream_domain_match.group(1)}"
    
    # Sabit kanal listesi - PHP'deki gibi
    channels = [
        "sbeinsports-1", "sbeinsports-2", "sbeinsports-3", "sbeinsports-4", "sbeinsports-5",
        "sbeinsportsmax-1", "sbeinsportsmax-2", "sssport", "sssport2", "ssmartspor",
        "ssmartspor2", "stivibuspor-1", "stivibuspor-2", "stivibuspor-3", "stivibuspor-4",
        "sbeinsportshaber", "saspor", "seurosport1", "seurosport2", "sf1",
        "sdazn1", "sdazn2", "sufcfightpass", "smotorsporttv", "smotorvisiontv",
        "stabiispor", "sssportplus1"
    ]
    
    results = {}
    for channel in channels:
        html = fetch_url(f"{stream_domain}/index.php?id={channel}")
        if html:
            ads_match = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', html)
            if ads_match:
                base_url = ads_match.group(1)
                if not base_url.endswith('/'):
                    base_url += '/'
                results[channel] = f"{base_url}{channel}/playlist.m3u8"
    
    return {'referer': domain_info['url'], 'channels': results}

def get_all_channels_from_html(html):
    """HTML'den tüm kanal ID'lerini çıkar"""
    # Regex ile tüm data-stream-url değerlerini bul
    pattern = r'data-stream-url="([^"]+)"'
    matches = re.findall(pattern, html)
    return list(set(matches))  # Benzersiz olanları döndür

def get_stream_links_all_channels(domain_info):
    """Tüm kanallar için stream linklerini al"""
    # Stream domain'ini bul
    stream_domain_match = re.search(
        r'https?:\/\/(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        domain_info['html']
    )
    
    if not stream_domain_match:
        # Alternatif pattern
        stream_domain_match = re.search(
            r'https?:\/\/(main\.[0-9a-zA-Z\-]+\.click)',
            domain_info['html']
        )
        if not stream_domain_match:
            return None
    
    stream_domain = f"https://{stream_domain_match.group(1)}"
    
    # HTML'den tüm kanal ID'lerini çıkar
    all_channels = get_all_channels_from_html(domain_info['html'])
    
    if not all_channels:
        # Eğer bulamazsak, sabit listeyi kullan
        all_channels = [
            "saspor", "sbeinsports-1", "sbeinsports-2", "sbeinsports-3", 
            "sbeinsports-4", "sbeinsportshaber", "sdazn1", "sdazn2",
            "sexxen-1", "sexxen-2", "sexxen-3", "sexxen-4", "sexxen-5", "sexxen-6",
            "sssport", "sssport2", "sssplus1", "sssplus2",
            "ssmartspor", "ssmartspor2", "stabiispor-1", "stabiispor-2",
            "stabiispor-3", "stabiispor-4", "stabiispor-5",
            "stivibuspor-1", "stivibuspor-2", "stivibuspor-3", "stivibuspor-4",
            "strt1", "strtspor", "strtspor2", "stv8"
        ]
    
    results = {}
    successful = 0
    
    print(f"Found {len(all_channels)} channels to process")
    
    for i, channel in enumerate(all_channels, 1):
        print(f"  Processing {i}/{len(all_channels)}: {channel}")
        
        html = fetch_url(f"{stream_domain}/index.php?id={channel}")
        if html:
            # Birden fazla pattern deneyelim
            patterns = [
                r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'var\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'baseUrl\s*=\s*[\'"]([^\'"]+)'
            ]
            
            for pattern in patterns:
                ads_match = re.search(pattern, html)
                if ads_match:
                    base_url = ads_match.group(1)
                    if not base_url.endswith('/'):
                        base_url += '/'
                    
                    stream_url = f"{base_url}{channel}/playlist.m3u8"
                    results[channel] = stream_url
                    successful += 1
                    print(f"    ✓ Found stream URL")
                    break
            else:
                print(f"    ✗ No stream URL found")
        else:
            print(f"    ✗ Could not fetch channel page")
    
    print(f"\nSuccessfully fetched {successful}/{len(all_channels)} streams")
    
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
    
    output = ["#EXTM3U"]
    
    # Kanal adları için mapping
    channel_names = {
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
    
    # Kanalları sırala
    sorted_channels = sorted(stream_info['channels'].items())
    
    for channel_id, stream_url in sorted_channels:
        # Kanal adını al
        channel_name = channel_names.get(channel_id, channel_id)
        
        # Temiz ID oluştur
        clean_id = channel_id.lstrip('s').replace('-', ' ')
        
        output.append(f"#EXTINF:-1 tvg-id=\"{channel_id}\",{channel_name}")
        output.append(f"#EXTVLCOPT:http-referrer={stream_info['referer']}")
        output.append(f"{stream_url}\n")
    
    return "\n".join(output)

def main():
    print("=" * 60)
    print("SPORCAFE M3U GENERATOR - PHP STYLE")
    print("=" * 60)
    
    # 1. Aktif domain'i bul
    print("\n1. Finding active domain...")
    domain_info = get_active_domain()
    
    if not domain_info:
        # Alternatif domain'leri dene
        print("Trying alternative domains...")
        alt_domains = [
            "https://sporcafe.live/",
            "https://sporcafe.tv/",
            "https://sporcafe.org/",
        ]
        
        for url in alt_domains:
            print(f"  Trying: {url}")
            html = fetch_url(url)
            if html:
                domain_info = {'url': url, 'html': html}
                print(f"  ✓ Using: {url}")
                break
        
        if not domain_info:
            print("✗ No active domain found!")
            print("#EXTM3U\n#EXTINF:-1,Error: No active domain found")
            return
    
    print(f"✓ Active domain: {domain_info['url']}")
    
    # 2. Stream linklerini al
    print("\n2. Fetching stream links...")
    stream_info = get_stream_links_all_channels(domain_info)
    
    if not stream_info:
        print("✗ Could not fetch stream links")
        print("#EXTM3U\n#EXTINF:-1,Error: Could not generate stream links")
        return
    
    print(f"✓ Successfully fetched {stream_info['successful']} streams")
    
    # 3. M3U oluştur
    print("\n3. Generating M3U playlist...")
    m3u_content = generate_m3u(stream_info)
    
    # 4. Dosyaya yaz
    with open('sporcafe.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    # 5. JSON çıktısı oluştur
    import json
    json_data = {
        'generated': datetime.now().isoformat(),
        'domain': domain_info['url'],
        'channels_count': stream_info['successful'],
        'channels': [
            {
                'id': channel_id,
                'url': stream_url,
                'name': channel_names.get(channel_id, channel_id)
            }
            for channel_id, stream_url in stream_info['channels'].items()
        ]
    }
    
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Active Domain: {domain_info['url']}")
    print(f"Stream Domain: {stream_info.get('stream_domain', 'N/A')}")
    print(f"Channels Found: {stream_info['successful']}")
    print(f"M3U File: sporcafe.m3u")
    print(f"JSON File: channels.json")
    print("=" * 60)
    
    # İlk 5 kanalı göster
    print("\nSample channels:")
    print("-" * 40)
    channels_list = list(stream_info['channels'].items())[:5]
    for channel_id, url in channels_list:
        name = channel_names.get(channel_id, channel_id)
        print(f"  • {name}")

if __name__ == "__main__":
    main()
