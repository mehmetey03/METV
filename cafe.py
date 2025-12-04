import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def fetch_url(url):
    """URL'den içerik çekme fonksiyonu"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_active_domain():
    """Aktif domain'i bulma - tüm olası domainleri kontrol et"""
    domains_to_check = []
    
    # 1-15 arası sporcafe domainleri
    for i in range(1, 16):
        domains_to_check.append(f"https://www.sporcafe{i}.xyz/")
    
    # Diğer olası domain pattern'leri
    other_patterns = [
        "https://sporcafe.live/",
        "https://sporcafe.tv/",
        "https://sporcafe.net/",
        "https://sporcafe.org/",
    ]
    
    domains_to_check.extend(other_patterns)
    
    for url in domains_to_check:
        print(f"Checking: {url}")
        html = fetch_url(url)
        if html and 'channel-item' in html:
            print(f"✓ Active domain found: {url}")
            return {'url': url, 'html': html}
    
    return None

def get_stream_links(domain_info):
    """Stream linklerini çekme"""
    # Birden fazla pattern ile stream domain'ini bulma
    patterns = [
        r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        r'https?://(main\.[0-9a-zA-Z\-]+\.click)',
        r'https?://(player\.uxsy[0-9a-zA-Z\-]+\.click)',
        r'https?://(stream\.uxsy[0-9a-zA-Z\-]+\.click)',
    ]
    
    stream_domain = None
    for pattern in patterns:
        match = re.search(pattern, domain_info['html'])
        if match:
            stream_domain = f"https://{match.group(1)}"
            break
    
    if not stream_domain:
        print("✗ Stream domain not found")
        return None
    
    print(f"✓ Stream domain: {stream_domain}")
    
    # Kanal ID'lerini HTML'den çekme
    soup = BeautifulSoup(domain_info['html'], 'html.parser')
    channel_items = soup.find_all('div', class_='channel-item')
    
    channels = []
    channel_data = {}
    
    for item in channel_items:
        stream_url = item.get('data-stream-url')
        if stream_url:
            channels.append(stream_url)
            
            # Kanal bilgilerini topla
            channel_name_div = item.find('div', class_='channel-name')
            channel_name = channel_name_div.text.strip() if channel_name_div else stream_url
            
            channel_logo = item.find('img')
            logo_url = channel_logo.get('src') if channel_logo else ''
            
            channel_data[stream_url] = {
                'name': channel_name,
                'logo': logo_url,
                'id': stream_url
            }
    
    # Benzersiz kanalları al
    unique_channels = list(set(channels))
    print(f"✓ Found {len(unique_channels)} unique channels")
    
    results = {}
    successful_channels = 0
    
    for channel in unique_channels:
        channel_url = f"{stream_domain}/index.php?id={channel}"
        html = fetch_url(channel_url)
        
        if html:
            # Birden fazla pattern ile adsBaseUrl'yi bulma
            ads_patterns = [
                r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'var\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
            ]
            
            for pattern in ads_patterns:
                ads_match = re.search(pattern, html)
                if ads_match:
                    stream_link = f"{ads_match.group(1)}{channel}/playlist.m3u8"
                    results[channel] = {
                        'url': stream_link,
                        'info': channel_data.get(channel, {'name': channel})
                    }
                    successful_channels += 1
                    print(f"  ✓ {channel_data.get(channel, {}).get('name', channel)}")
                    break
    
    print(f"✓ Successfully fetched {successful_channels}/{len(unique_channels)} streams")
    
    return {
        'referer': domain_info['url'],
        'stream_domain': stream_domain,
        'channels': results,
        'total_channels': len(unique_channels),
        'successful': successful_channels
    }

def generate_m3u():
    """M3U playlist oluşturma"""
    print("=" * 50)
    print("SPORCAFE M3U PLAYLIST GENERATOR")
    print("=" * 50)
    
    # Aktif domain'i bul
    print("\n[1/3] Searching for active domain...")
    domain_info = get_active_domain()
    if not domain_info:
        print("#EXTM3U")
        print("#EXTINF:-1,Error: No active domain found")
        return False
    
    # Stream linklerini al
    print("\n[2/3] Fetching stream links...")
    stream_links = get_stream_links(domain_info)
    if not stream_links or not stream_links['channels']:
        print("#EXTM3U")
        print("#EXTINF:-1,Error: Could not generate stream links")
        return False
    
    # M3U çıktısını oluştur
    print("\n[3/3] Generating M3U playlist...")
    
    # Başlık bilgileri
    print("#EXTM3U")
    print(f"#EXTM3U-url-tvg=\"http://example.com/epg.xml\"")
    print(f"#PLAYLIST:SPORCAFE Streams")
    print(f"#GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"#DOMAIN: {domain_info['url']}")
    print(f"#STREAM-DOMAIN: {stream_links['stream_domain']}")
    print(f"#CHANNELS: {stream_links['successful']}/{stream_links['total_channels']}")
    print()
    
    # Kanalları alfabetik sırala
    sorted_channels = sorted(
        stream_links['channels'].items(),
        key=lambda x: x[1]['info']['name']
    )
    
    for channel_id, data in sorted_channels:
        channel_info = data['info']
        channel_name = channel_info['name']
        
        # TVG ID için temizleme
        tvg_id = channel_id.lstrip('s').replace('-', '')
        
        # Logo URL'si
        logo = channel_info.get('logo', '')
        if logo and not logo.startswith('http'):
            logo = domain_info['url'].rstrip('/') + logo
        
        # EXTINF satırı
        if logo:
            print(f"#EXTINF:-1 tvg-id=\"{tvg_id}\" tvg-logo=\"{logo}\" group-title=\"SPORCAFE\",{channel_name}")
        else:
            print(f"#EXTINF:-1 tvg-id=\"{tvg_id}\" group-title=\"SPORCAFE\",{channel_name}")
        
        # Referer ve diğer opsiyonlar
        print(f"#EXTVLCOPT:http-referrer={stream_links['referer']}")
        print(f"#EXTVLCOPT:http-user-agent=Mozilla/5.0")
        
        # Stream URL
        print(f"{data['url']}\n")
    
    print("#EOF")
    
    # JSON çıktısı da oluştur (opsiyonel)
    with open('channels.json', 'w', encoding='utf-8') as f:
        json_data = {
            'generated': datetime.now().isoformat(),
            'domain': domain_info['url'],
            'stream_domain': stream_links['stream_domain'],
            'channels': [
                {
                    'id': channel_id,
                    'name': data['info']['name'],
                    'url': data['url'],
                    'logo': data['info'].get('logo', ''),
                    'tvg_id': channel_id.lstrip('s').replace('-', '')
                }
                for channel_id, data in sorted_channels
            ]
        }
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    return True

def main():
    """Ana fonksiyon"""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    success = generate_m3u()
    
    if success:
        print("\n" + "=" * 50)
        print("✓ M3U playlist successfully generated!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("✗ Failed to generate M3U playlist")
        print("=" * 50)

if __name__ == "__main__":
    main()
