import re
import requests
import json
from datetime import datetime
import urllib3
from html.parser import HTMLParser

# Uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimpleHTMLParser(HTMLParser):
    """Basit HTML parser - BeautifulSoup bağımlılığını kaldırmak için"""
    def __init__(self):
        super().__init__()
        self.channels = []
        self.current_channel = {}
        self.in_channel_item = False
        self.in_channel_name = False
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'div' and 'class' in attrs_dict and 'channel-item' in attrs_dict['class']:
            self.in_channel_item = True
            self.current_channel = {
                'data-stream-url': attrs_dict.get('data-stream-url', ''),
                'name': '',
                'logo': ''
            }
        
        elif self.in_channel_item:
            if tag == 'img' and 'src' in attrs_dict:
                self.current_channel['logo'] = attrs_dict['src']
            elif tag == 'div' and 'class' in attrs_dict and 'channel-name' in attrs_dict['class']:
                self.in_channel_name = True
                
    def handle_data(self, data):
        if self.in_channel_name:
            self.current_channel['name'] = data.strip()
            
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_channel_item:
            if self.current_channel['data-stream-url']:
                self.channels.append(self.current_channel.copy())
            self.in_channel_item = False
            self.in_channel_name = False

def fetch_url(url, max_retries=3):
    """URL'den içerik çekme fonksiyonu"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"  ✗ Failed to fetch {url}: {e}")
                return None
            continue
    
    return None

def get_active_domain():
    """Aktif domain'i bulma"""
    print("🔍 Searching for active domain...")
    
    # Öncelikli domainler
    domains_to_check = [
        "https://sporcafelive.com/",
        "https://sporcafe.live/",
        "https://sporcafe.tv/",
        "https://www.sporcafe1.xyz/",
        "https://www.sporcafe2.xyz/",
        "https://www.sporcafe3.xyz/",
        "https://www.sporcafe4.xyz/",
        "https://www.sporcafe5.xyz/",
        "https://www.sporcafe6.xyz/",
        "https://www.sporcafe7.xyz/",
        "https://www.sporcafe8.xyz/",
        "https://www.sporcafe9.xyz/",
        "https://www.sporcafe10.xyz/",
        "https://www.sporcafe11.xyz/",
        "https://www.sporcafe12.xyz/",
        "https://www.sporcafe13.xyz/",
        "https://www.sporcafe14.xyz/",
        "https://www.sporcafe15.xyz/",
    ]
    
    for url in domains_to_check:
        print(f"  Checking: {url}")
        html = fetch_url(url)
        if html and ('channel-item' in html or 'data-stream-url' in html):
            print(f"  ✓ Active domain found: {url}")
            return {'url': url, 'html': html}
    
    print("  ✗ No active domain found")
    return None

def extract_channels_from_html(html):
    """HTML'den kanal bilgilerini çıkart"""
    parser = SimpleHTMLParser()
    parser.feed(html)
    return parser.channels

def get_stream_domain(html):
    """HTML'den stream domain'ini bul"""
    patterns = [
        r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        r'https?://(main\.[0-9a-zA-Z\-]+\.click)',
        r'https?://(player\.[0-9a-zA-Z\-]+\.click)',
        r'https?://(stream\.[0-9a-zA-Z\-]+\.click)',
        r'https?://(cdn\.[0-9a-zA-Z\-]+\.click)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            return f"https://{match.group(1)}"
    
    return None

def get_stream_links(domain_info, channels):
    """Stream linklerini çek"""
    stream_domain = get_stream_domain(domain_info['html'])
    
    if not stream_domain:
        print("  ✗ Stream domain not found in HTML")
        return None
    
    print(f"  ✓ Stream domain: {stream_domain}")
    
    results = {}
    successful = 0
    
    for channel in channels:
        channel_id = channel['data-stream-url']
        channel_name = channel['name']
        
        if not channel_id:
            continue
            
        print(f"  Fetching: {channel_name} ({channel_id})")
        
        channel_url = f"{stream_domain}/index.php?id={channel_id}"
        html = fetch_url(channel_url)
        
        if html:
            # adsBaseUrl'yi bul
            ads_patterns = [
                r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'var\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'const\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
                r'let\s+adsBaseUrl\s*=\s*[\'"]([^\'"]+)',
            ]
            
            for pattern in ads_patterns:
                ads_match = re.search(pattern, html)
                if ads_match:
                    base_url = ads_match.group(1)
                    if not base_url.endswith('/'):
                        base_url += '/'
                    
                    stream_url = f"{base_url}{channel_id}/playlist.m3u8"
                    results[channel_id] = {
                        'url': stream_url,
                        'name': channel_name,
                        'logo': channel['logo']
                    }
                    successful += 1
                    print(f"    ✓ Found stream URL")
                    break
            else:
                print(f"    ✗ No stream URL found")
        else:
            print(f"    ✗ Failed to fetch channel page")
    
    print(f"  ✓ Successfully fetched {successful}/{len(channels)} streams")
    
    return {
        'referer': domain_info['url'],
        'stream_domain': stream_domain,
        'channels': results,
        'total': len(channels),
        'successful': successful
    }

def generate_m3u_playlist(stream_info):
    """M3U playlist oluştur"""
    print("📝 Generating M3U playlist...")
    
    output = []
    
    # M3U header
    output.append("#EXTM3U")
    output.append("#EXTM3U-url-tvg=\"\"")
    output.append(f"#PLAYLIST:SPORCAFE TV")
    output.append(f"#GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"#DOMAIN: {stream_info['referer']}")
    output.append(f"#CHANNELS: {stream_info['successful']}/{stream_info['total']}")
    output.append("")
    
    # Kanalları isme göre sırala
    sorted_channels = sorted(
        stream_info['channels'].items(),
        key=lambda x: x[1]['name']
    )
    
    for channel_id, channel_data in sorted_channels:
        channel_name = channel_data['name']
        stream_url = channel_data['url']
        
        # Logo URL'sini tamamla
        logo_url = channel_data['logo']
        if logo_url and not logo_url.startswith('http'):
            if logo_url.startswith('/'):
                logo_url = stream_info['referer'].rstrip('/') + logo_url
            else:
                logo_url = stream_info['referer'].rstrip('/') + '/' + logo_url
        
        # TVG ID oluştur
        tvg_id = channel_id.replace('s', '').replace('-', '').lower()
        
        # EXTINF satırı
        if logo_url:
            extinf_line = f"#EXTINF:-1 tvg-id=\"{tvg_id}\" tvg-logo=\"{logo_url}\" group-title=\"SPOR\",{channel_name}"
        else:
            extinf_line = f"#EXTINF:-1 tvg-id=\"{tvg_id}\" group-title=\"SPOR\",{channel_name}"
        
        output.append(extinf_line)
        output.append(f"#EXTVLCOPT:http-referrer={stream_info['referer']}")
        output.append(f"#EXTVLCOPT:http-user-agent=Mozilla/5.0")
        output.append(stream_url)
        output.append("")
    
    output.append("#EOF")
    
    return "\n".join(output)

def generate_json_output(stream_info):
    """JSON çıktısı oluştur"""
    channels_list = []
    
    for channel_id, channel_data in stream_info['channels'].items():
        channels_list.append({
            'id': channel_id,
            'name': channel_data['name'],
            'url': channel_data['url'],
            'logo': channel_data['logo'],
            'tvg_id': channel_id.replace('s', '').replace('-', '').lower(),
            'group': 'SPOR'
        })
    
    json_data = {
        'generated': datetime.now().isoformat(),
        'domain': stream_info['referer'],
        'stream_domain': stream_info['stream_domain'],
        'total_channels': stream_info['total'],
        'successful_channels': stream_info['successful'],
        'channels': channels_list
    }
    
    return json.dumps(json_data, ensure_ascii=False, indent=2)

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("SPORCAFE M3U PLAYLIST GENERATOR")
    print("=" * 60)
    
    # 1. Aktif domain'i bul
    domain_info = get_active_domain()
    if not domain_info:
        print("\n✗ ERROR: Could not find active domain")
        print("#EXTM3U\n#EXTINF:-1,Error: No active domain found")
        return
    
    print()
    
    # 2. Kanal bilgilerini çıkar
    print("📺 Extracting channel information...")
    channels = extract_channels_from_html(domain_info['html'])
    
    if not channels:
        print("  ✗ No channels found in HTML")
        print("\n#EXTM3U\n#EXTINF:-1,Error: No channels found")
        return
    
    print(f"  ✓ Found {len(channels)} channels")
    
    # 3. Stream linklerini al
    stream_info = get_stream_links(domain_info, channels)
    
    if not stream_info or not stream_info['channels']:
        print("\n✗ ERROR: Could not fetch stream links")
        print("#EXTM3U\n#EXTINF:-1,Error: Could not generate stream links")
        return
    
    print()
    
    # 4. M3U playlist oluştur
    m3u_content = generate_m3u_playlist(stream_info)
    
    # 5. JSON çıktısı oluştur (opsiyonel)
    json_content = generate_json_output(stream_info)
    
    # 6. Dosyalara yaz
    try:
        with open('sporcafe.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        print(f"✓ M3U playlist saved: sporcafe.m3u")
        
        with open('channels.json', 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"✓ JSON data saved: channels.json")
        
    except Exception as e:
        print(f"✗ Error saving files: {e}")
    
    # 7. M3U içeriğini konsola yazdır
    print("\n" + "=" * 60)
    print("M3U PLAYLIST CONTENT:")
    print("=" * 60)
    print(m3u_content)
    
    print("\n" + "=" * 60)
    print("✓ Generation completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
