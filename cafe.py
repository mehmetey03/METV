import re
import requests
import urllib3
from datetime import datetime
import json

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Kanal adları ve logoları
CHANNEL_INFO = {
    "saspor": {"name": "A Spor", "logo": "https://www.sporcafe15.xyz/assets/images/channels/aspor.png", "tvg-id": "aspor"},
    "sbeinsports-1": {"name": "BeIN Sports 1", "logo": "https://www.sporcafe15.xyz/assets/images/channels/beinsports1.png", "tvg-id": "bein1"},
    "sbeinsports-2": {"name": "BeIN Sports 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/beinsports2.png", "tvg-id": "bein2"},
    "sbeinsports-3": {"name": "BeIN Sports 3", "logo": "https://www.sporcafe15.xyz/assets/images/channels/beinsports3.png", "tvg-id": "bein3"},
    "sbeinsports-4": {"name": "BeIN Sports 4", "logo": "https://www.sporcafe15.xyz/assets/images/channels/beinsports4.png", "tvg-id": "bein4"},
    "sbeinsports-5": {"name": "BeIN Sports 5", "logo": "https://www.sporcafe15.xyz/assets/images/channels/beinsports5.png", "tvg-id": "bein5"},
    "sbeinsportshaber": {"name": "BeIN Sports Haber", "logo": "https://www.sporcafe15.xyz/assets/images/channels/beinsportshaber.png", "tvg-id": "beinhd"},
    "sdazn1": {"name": "DAZN 1", "logo": "https://www.sporcafe15.xyz/assets/images/channels/dazn1.jpg", "tvg-id": "dazn1"},
    "sdazn2": {"name": "DAZN 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/dazn2.png", "tvg-id": "dazn2"},
    "sexxen-1": {"name": "Exxen Spor 1", "logo": "https://www.sporcafe15.xyz/assets/images/channels/exxen.png", "tvg-id": "exxen1"},
    "sexxen-2": {"name": "Exxen Spor 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/exxen.png", "tvg-id": "exxen2"},
    "sexxen-3": {"name": "Exxen Spor 3", "logo": "https://www.sporcafe15.xyz/assets/images/channels/exxen.png", "tvg-id": "exxen3"},
    "sexxen-4": {"name": "Exxen Spor 4", "logo": "https://www.sporcafe15.xyz/assets/images/channels/exxen.png", "tvg-id": "exxen4"},
    "sexxen-5": {"name": "Exxen Spor 5", "logo": "https://www.sporcafe15.xyz/assets/images/channels/exxen.png", "tvg-id": "exxen5"},
    "sexxen-6": {"name": "Exxen Spor 6", "logo": "https://www.sporcafe15.xyz/assets/images/channels/exxen.png", "tvg-id": "exxen6"},
    "sssport": {"name": "S Sport", "logo": "https://www.sporcafe15.xyz/assets/images/channels/ssport_logo.png", "tvg-id": "ssport"},
    "sssport2": {"name": "S Sport 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/ssport2_logo.png", "tvg-id": "ssport2"},
    "sssplus1": {"name": "S Sport Plus 1", "logo": "https://www.sporcafe15.xyz/assets/images/channels/ssportplus_logo.png", "tvg-id": "ssportplus1"},
    "sssplus2": {"name": "S Sport Plus 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/ssportplus_logo.png", "tvg-id": "ssportplus2"},
    "ssmartspor": {"name": "Smart Spor", "logo": "https://www.sporcafe15.xyz/assets/images/channels/smartspor.jpg", "tvg-id": "smartspor"},
    "ssmartspor2": {"name": "Smart Spor 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/smartspor.jpg", "tvg-id": "smartspor2"},
    "stabiispor-1": {"name": "Tabii Spor 1", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tabiispor.png", "tvg-id": "tabii1"},
    "stabiispor-2": {"name": "Tabii Spor 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tabiispor.png", "tvg-id": "tabii2"},
    "stabiispor-3": {"name": "Tabii Spor 3", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tabiispor.png", "tvg-id": "tabii3"},
    "stabiispor-4": {"name": "Tabii Spor 4", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tabiispor.png", "tvg-id": "tabii4"},
    "stabiispor-5": {"name": "Tabii Spor 5", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tabiispor.png", "tvg-id": "tabii5"},
    "stivibuspor-1": {"name": "Tivibu Spor 1", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tivibu.png", "tvg-id": "tivibu1"},
    "stivibuspor-2": {"name": "Tivibu Spor 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tivibu.png", "tvg-id": "tivibu2"},
    "stivibuspor-3": {"name": "Tivibu Spor 3", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tivibu.png", "tvg-id": "tivibu3"},
    "stivibuspor-4": {"name": "Tivibu Spor 4", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tivibu.png", "tvg-id": "tivibu4"},
    "strt1": {"name": "TRT 1", "logo": "https://www.sporcafe15.xyz/assets/uploads/trt1-21284924-0-0-250-250.png", "tvg-id": "trt1"},
    "strtspor": {"name": "TRT Spor", "logo": "https://www.sporcafe15.xyz/assets/images/channels/trtspor.png", "tvg-id": "trtspor"},
    "strtspor2": {"name": "TRT Spor 2", "logo": "https://www.sporcafe15.xyz/assets/images/channels/trtspor2.png", "tvg-id": "trtspor2"},
    "stv8": {"name": "TV8", "logo": "https://www.sporcafe15.xyz/assets/images/channels/tv8_logo.png", "tvg-id": "tv8"}
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
        print(f"    ✗ Error: {e}")
        return None

def get_active_domain():
    """Aktif domain'i bul"""
    print("🔍 Searching for active domain...")
    for i in range(15, 4, -1):
        url = f"https://www.sporcafe{i}.xyz/"
        print(f"  Trying: {url}")
        html = fetch_url(url)
        if html and len(html) > 100:
            print(f"  ✓ Active domain: {url}")
            return {'url': url, 'html': html}
    return None

def get_stream_domain(html):
    """HTML'den stream domain'ini bul"""
    patterns = [
        r'https?:\/\/(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        r'https?:\/\/(main\.[0-9a-zA-Z\-]+\.click)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return f"https://{match.group(1)}"
    return None

def get_all_channels_from_html(html):
    """HTML'den tüm kanal ID'lerini çıkar"""
    pattern = r'data-stream-url="([^"]+)"'
    matches = re.findall(pattern, html)
    unique_channels = list(set(matches))
    
    if unique_channels:
        print(f"  Found {len(unique_channels)} channels in HTML")
        return unique_channels
    
    # Default list
    return list(CHANNEL_INFO.keys())

def get_stream_links(domain_info):
    """Stream linklerini al"""
    print("🔗 Fetching stream links...")
    
    stream_domain = get_stream_domain(domain_info['html'])
    if not stream_domain:
        stream_domain = "https://main.uxsyplayer1.click"
        print(f"  Using default: {stream_domain}")
    else:
        print(f"  Stream domain: {stream_domain}")
    
    all_channels = get_all_channels_from_html(domain_info['html'])
    
    results = {}
    successful = 0
    
    print(f"  Processing {len(all_channels)} channels...")
    
    for i, channel in enumerate(all_channels, 1):
        channel_name = CHANNEL_INFO.get(channel, {}).get('name', channel)
        print(f"  [{i:2d}/{len(all_channels)}] {channel_name}")
        
        channel_url = f"{stream_domain}/index.php?id={channel}"
        html = fetch_url(channel_url)
        
        if html:
            ads_patterns = [
                r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'var\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
            ]
            
            for pattern in ads_patterns:
                ads_match = re.search(pattern, html)
                if ads_match:
                    base_url = ads_match.group(1)
                    if not base_url.endswith('/'):
                        base_url += '/'
                    
                    stream_url = f"{base_url}{channel}/playlist.m3u8"
                    results[channel] = stream_url
                    successful += 1
                    print(f"      ✓ Found")
                    break
    
    print(f"\n  📊 Success: {successful}/{len(all_channels)} streams")
    
    return {
        'referer': domain_info['url'],
        'stream_domain': stream_domain,
        'channels': results,
        'total': len(all_channels),
        'successful': successful
    }

def generate_m3u(stream_info):
    """M3U playlist oluştur"""
    print("\n📝 Generating M3U playlist...")
    
    output = ["#EXTM3U"]
    
    # Sort channels by name
    sorted_channels = sorted(
        stream_info['channels'].items(),
        key=lambda x: CHANNEL_INFO.get(x[0], {}).get('name', x[0])
    )
    
    for channel_id, stream_url in sorted_channels:
        channel_info = CHANNEL_INFO.get(channel_id, {})
        channel_name = channel_info.get('name', channel_id)
        channel_logo = channel_info.get('logo', '')
        tvg_id = channel_info.get('tvg-id', channel_id.replace('s', '').replace('-', ''))
        
        # Determine group
        group = "SPOR"
        if 'beinsports' in channel_id:
            group = "BeIN SPORTS"
        elif 'dazn' in channel_id:
            group = "DAZN"
        elif 'ssport' in channel_id:
            group = "S SPORT"
        elif 'trt' in channel_id:
            group = "TRT"
        elif 'exxen' in channel_id:
            group = "EXXEN"
        elif 'tivibu' in channel_id:
            group = "TIVIBU"
        elif 'tabii' in channel_id:
            group = "TABII"
        
        # Create EXTINF line
        if channel_logo:
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{channel_name}" tvg-logo="{channel_logo}" group-title="{group}",{channel_name}'
        else:
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{channel_name}" group-title="{group}",{channel_name}'
        
        output.append(extinf)
        output.append(f'#EXTVLCOPT:http-referrer={stream_info["referer"]}')
        output.append(stream_url)
    
    return "\n".join(output)

def main():
    print("=" * 60)
    print("SPORCAFE M3U GENERATOR")
    print("=" * 60)
    
    # Get active domain
    print("\n[1/3] Finding active domain...")
    domain_info = get_active_domain()
    if not domain_info:
        print("\n✗ ERROR: No active domain found!")
        print("#EXTM3U\n#EXTINF:-1,Error: No active domain found")
        return
    
    print(f"✓ Domain: {domain_info['url']}")
    
    # Get stream links
    print("\n[2/3] Fetching stream links...")
    stream_info = get_stream_links(domain_info)
    
    if not stream_info or not stream_info['channels']:
        print("\n✗ ERROR: No stream links found!")
        print("#EXTM3U\n#EXTINF:-1,Error: No stream links found")
        return
    
    print(f"✓ Found {stream_info['successful']} streams")
    
    # Generate M3U
    print("\n[3/3] Generating M3U playlist...")
    m3u_content = generate_m3u(stream_info)
    
    # Save files
    with open('sporcafe.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    print("✓ M3U file saved: sporcafe.m3u")
    
    # Save JSON
    json_data = {
        'generated': datetime.now().isoformat(),
        'domain': domain_info['url'],
        'channels_count': stream_info['successful'],
        'channels': [
            {
                'id': channel_id,
                'name': CHANNEL_INFO.get(channel_id, {}).get('name', channel_id),
                'url': stream_url,
                'tvg_id': CHANNEL_INFO.get(channel_id, {}).get('tvg-id', ''),
                'logo': CHANNEL_INFO.get(channel_id, {}).get('logo', '')
            }
            for channel_id, stream_url in stream_info['channels'].items()
        ]
    }
    
    with open('channels.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print("✓ JSON file saved: channels.json")
    
    # Show results
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"Domain: {domain_info['url']}")
    print(f"Channels: {stream_info['successful']}")
    print(f"File: sporcafe.m3u")
    print("=" * 60)
    
    # Show first 5 channels as example
    print("\nExample M3U format:")
    print("-" * 40)
    lines = m3u_content.split('\n')
    for line in lines[:8]:  # Show first 2 channels
        print(line)

if __name__ == "__main__":
    main()
