import re
import requests
import json
from datetime import datetime
import urllib3
from html.parser import HTMLParser
import sys

# Uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChannelHTMLParser(HTMLParser):
    """HTML'den kanal bilgilerini çıkarmak için parser"""
    def __init__(self):
        super().__init__()
        self.channels = []
        self.current_channel = {}
        self.capture_data = False
        self.in_channel_div = False
        self.depth = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Kanal item'larını bul (data-stream-url attribute'una sahip div'ler)
        if tag == 'div' and 'data-stream-url' in attrs_dict:
            self.in_channel_div = True
            self.current_channel = {
                'data-stream-url': attrs_dict['data-stream-url'],
                'name': '',
                'logo': ''
            }
            self.depth = 1
            
        elif self.in_channel_div:
            self.depth += 1
            
            # Logo resmini bul
            if tag == 'img' and 'src' in attrs_dict:
                self.current_channel['logo'] = attrs_dict['src']
                
            # Kanal adı div'ini bul
            if tag == 'div' and 'class' in attrs_dict:
                if 'channel-name' in attrs_dict['class']:
                    self.capture_data = True
                    
    def handle_data(self, data):
        if self.capture_data and data.strip():
            self.current_channel['name'] = data.strip()
            
    def handle_endtag(self, tag):
        if self.in_channel_div:
            if tag == 'div':
                self.depth -= 1
                if self.depth == 0:
                    if self.current_channel['data-stream-url'] and self.current_channel['name']:
                        self.channels.append(self.current_channel.copy())
                    self.in_channel_div = False
                    self.capture_data = False
            elif self.capture_data and tag in ['div', 'span', 'p', 'a']:
                self.capture_data = False

def fetch_url(url, max_retries=2):
    """URL'den içerik çekme fonksiyonu"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }
    
    for attempt in range(max_retries):
        try:
            # Daha uzun timeout
            response = requests.get(
                url, 
                headers=headers, 
                timeout=(10, 30), 
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Encoding düzeltmesi
            if response.encoding is None:
                response.encoding = 'utf-8'
                
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"    ✗ Attempt {attempt + 1}/{max_retries}: {type(e).__name__}")
            if attempt == max_retries - 1:
                return None
            continue
    
    return None

def get_active_domain():
    """Aktif domain'i bulma - PHP kodundaki gibi 15'ten 5'e"""
    print("🔍 Searching for active domain...")
    
    # PHP kodundaki gibi 15'ten 5'e kontrol edelim
    for i in range(15, 4, -1):
        url = f"https://www.sporcafe{i}.xyz/"
        print(f"  Checking: {url}")
        
        html = fetch_url(url)
        if html:
            # "channel-item" class'ını ara
            if 'channel-item' in html or 'data-stream-url' in html or 'channel-name' in html:
                print(f"  ✓ Active domain found: {url}")
                return {'url': url, 'html': html}
            else:
                print(f"    ✗ No channel data found")
        else:
            print(f"    ✗ Could not fetch")
    
    print("  ✗ No active domain found")
    return None

def extract_channels(html):
    """HTML'den kanal bilgilerini çıkar"""
    print("📺 Extracting channels from HTML...")
    
    # İlk önce regex ile deneyelim
    channel_pattern = r'<div[^>]*class="[^"]*channel-item[^"]*"[^>]*data-stream-url="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*channel-name[^"]*"[^>]*>([^<]+)</div>'
    logo_pattern = r'<img[^>]*src="([^"]*)"[^>]*>'
    
    channels = []
    
    # Basit regex ile kanalları bul
    channel_matches = list(re.finditer(channel_pattern, html, re.DOTALL))
    
    if channel_matches:
        print(f"  ✓ Found {len(channel_matches)} channels with regex")
        
        for match in channel_matches:
            channel_id = match.group(1)
            channel_name = match.group(2).strip()
            
            # Logo'yu bul
            logo_match = re.search(logo_pattern, match.group(0))
            logo = logo_match.group(1) if logo_match else ''
            
            channels.append({
                'data-stream-url': channel_id,
                'name': channel_name,
                'logo': logo
            })
            
        return channels
    
    # Regex ile bulamazsak HTML parser kullan
    print("  Trying HTML parser...")
    parser = ChannelHTMLParser()
    try:
        parser.feed(html)
        if parser.channels:
            print(f"  ✓ Found {len(parser.channels)} channels with parser")
            return parser.channels
    except Exception as e:
        print(f"    ✗ Parser error: {e}")
    
    # Son çare: manuel arama
    print("  Trying manual extraction...")
    
    # data-stream-url'leri bul
    stream_urls = re.findall(r'data-stream-url="([^"]+)"', html)
    unique_urls = list(set(stream_urls))
    
    for url in unique_urls:
        # Kanal adını bulmak için basit yaklaşım
        name_pattern = f'data-stream-url="{re.escape(url)}"[^>]*>.*?<div[^>]*class="[^"]*channel-name[^"]*"[^>]*>([^<]+)</div>'
        name_match = re.search(name_pattern, html, re.DOTALL)
        channel_name = name_match.group(1).strip() if name_match else url
        
        channels.append({
            'data-stream-url': url,
            'name': channel_name,
            'logo': ''
        })
    
    if channels:
        print(f"  ✓ Found {len(channels)} channels manually")
    
    return channels

def get_stream_domain(html):
    """HTML'den stream domain'ini bul"""
    patterns = [
        r'(https?://main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        r'(https?://main\.[0-9a-zA-Z\-]+\.click)',
        r'(https?://player\.[0-9a-zA-Z\-]+\.click)',
        r'(https?://stream\.[0-9a-zA-Z\-]+\.click)',
        r'this\.adsBaseUrl\s*=\s*[\'"](https?://[^\'"]+)',
        r'var\s+adsBaseUrl\s*=\s*[\'"](https?://[^\'"]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html)
        if match:
            url = match.group(1) if match.groups() else match.group(0)
            # URL'yi temizle
            if url.endswith('/'):
                url = url[:-1]
            return url
    
    # Alternatif: index.php sayfalarından domain çıkar
    index_pattern = r'(https?://[^/]+)/index\.php\?id='
    match = re.search(index_pattern, html)
    if match:
        return match.group(1)
    
    return None

def get_stream_links(domain_info, channels):
    """Stream linklerini çek"""
    print("🔗 Fetching stream links...")
    
    # Stream domain'ini bul
    stream_domain = get_stream_domain(domain_info['html'])
    
    if not stream_domain:
        print("  ✗ Could not find stream domain")
        # Varsayılan bir domain deneyelim
        stream_domain = "https://main.uxsyplayer1.click"
        print(f"  Trying default: {stream_domain}")
    
    print(f"  ✓ Using stream domain: {stream_domain}")
    
    results = {}
    successful = 0
    failed_channels = []
    
    for i, channel in enumerate(channels, 1):
        channel_id = channel['data-stream-url']
        channel_name = channel['name']
        
        if not channel_id:
            continue
            
        print(f"  [{i}/{len(channels)}] {channel_name}...")
        
        # Channel URL'sini oluştur
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
                r'baseUrl\s*=\s*[\'"]([^\'"]+)',
            ]
            
            found = False
            for pattern in ads_patterns:
                ads_match = re.search(pattern, html)
                if ads_match:
                    base_url = ads_match.group(1)
                    
                    # URL'yi temizle
                    if not base_url.endswith('/'):
                        base_url += '/'
                    
                    # Stream URL'sini oluştur
                    stream_url = f"{base_url}{channel_id}/playlist.m3u8"
                    
                    results[channel_id] = {
                        'url': stream_url,
                        'name': channel_name,
                        'logo': channel['logo']
                    }
                    successful += 1
                    print(f"    ✓ Stream found")
                    found = True
                    break
            
            if not found:
                print(f"    ✗ No adsBaseUrl found")
                failed_channels.append(channel_name)
        else:
            print(f"    ✗ Could not fetch channel page")
            failed_channels.append(channel_name)
    
    print(f"\n  📊 Results: {successful}/{len(channels)} successful")
    
    if failed_channels:
        print(f"  ⚠ Failed channels: {', '.join(failed_channels[:5])}" + 
              (f" and {len(failed_channels)-5} more" if len(failed_channels) > 5 else ""))
    
    if not results:
        return None
    
    return {
        'referer': domain_info['url'],
        'stream_domain': stream_domain,
        'channels': results,
        'total': len(channels),
        'successful': successful
    }

def generate_m3u_playlist(stream_info):
    """M3U playlist oluştur"""
    print("\n📝 Generating M3U playlist...")
    
    output_lines = []
    
    # M3U header
    output_lines.append("#EXTM3U")
    output_lines.append(f"#PLAYLIST:SPORCAFE TV")
    output_lines.append(f"#GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append(f"#DOMAIN: {stream_info['referer']}")
    output_lines.append(f"#CHANNELS: {stream_info['successful']}/{stream_info['total']}")
    output_lines.append("")
    
    # Kanalları isme göre sırala
    sorted_channels = sorted(
        stream_info['channels'].items(),
        key=lambda x: x[1]['name']
    )
    
    for channel_id, channel_data in sorted_channels:
        channel_name = channel_data['name']
        stream_url = channel_data['url']
        logo = channel_data['logo']
        
        # Logo URL'sini tamamla
        logo_url = ""
        if logo:
            if logo.startswith('http'):
                logo_url = logo
            elif logo.startswith('/'):
                logo_url = stream_info['referer'].rstrip('/') + logo
            else:
                logo_url = stream_info['referer'].rstrip('/') + '/' + logo
        
        # TVG ID oluştur
        tvg_id = channel_id.lstrip('s').replace('-', '').lower()
        
        # Grup belirleme
        group = "SPOR"
        if 'beinsports' in channel_id:
            group = "BEIN SPORTS"
        elif 'dazn' in channel_id:
            group = "DAZN"
        elif 'ssport' in channel_id:
            group = "S SPORT"
        elif 'trt' in channel_id:
            group = "TRT"
        elif 'tivibu' in channel_id:
            group = "TIVIBU"
        
        # EXTINF satırı
        if logo_url:
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo_url}" group-title="{group}",{channel_name}'
        else:
            extinf = f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="{group}",{channel_name}'
        
        output_lines.append(extinf)
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
                    'name': data['name'],
                    'url': data['url'],
                    'logo': data['logo'],
                    'tvg_id': channel_id.lstrip('s').replace('-', '').lower()
                }
                for channel_id, data in stream_info['channels'].items()
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
    """Ana fonksiyon"""
    print("=" * 60)
    print("SPORCAFE M3U PLAYLIST GENERATOR v2.0")
    print("=" * 60)
    
    # 1. Aktif domain'i bul
    domain_info = get_active_domain()
    if not domain_info:
        print("\n" + "=" * 60)
        print("ERROR: No active domain found!")
        print("=" * 60)
        print("#EXTM3U\n#EXTINF:-1,Error: No active domain found")
        return
    
    print()
    
    # 2. Kanal bilgilerini çıkar
    channels = extract_channels(domain_info['html'])
    
    if not channels:
        print("\n" + "=" * 60)
        print("ERROR: No channels found in HTML!")
        print("Trying alternative method...")
        print("=" * 60)
        
        # HTML'i kaydedip inceleyelim
        with open('debug.html', 'w', encoding='utf-8') as f:
            f.write(domain_info['html'][:5000])  # İlk 5000 karakter
        
        # Manuel kanal listesi kullanalım
        manual_channels = [
            {'data-stream-url': 'saspor', 'name': 'A Spor', 'logo': '/assets/images/channels/aspor.png'},
            {'data-stream-url': 'sbeinsports-1', 'name': 'beIN Sports 1', 'logo': '/assets/images/channels/beinsports1.png'},
            {'data-stream-url': 'sbeinsports-2', 'name': 'beIN Sports 2', 'logo': '/assets/images/channels/beinsports2.png'},
            {'data-stream-url': 'sbeinsports-3', 'name': 'beIN Sports 3', 'logo': '/assets/images/channels/beinsports3.png'},
            {'data-stream-url': 'sbeinsports-4', 'name': 'beIN Sports 4', 'logo': '/assets/images/channels/beinsports4.png'},
            {'data-stream-url': 'sbeinsportshaber', 'name': 'beIN Sports Haber', 'logo': '/assets/images/channels/beinsportshaber.png'},
            {'data-stream-url': 'sdazn1', 'name': 'DAZN 1', 'logo': '/assets/images/channels/dazn1.jpg'},
            {'data-stream-url': 'sdazn2', 'name': 'DAZN 2', 'logo': '/assets/images/channels/dazn2.png'},
            {'data-stream-url': 'sssport', 'name': 'S Sport', 'logo': '/assets/images/channels/ssport_logo.png'},
            {'data-stream-url': 'sssport2', 'name': 'S Sport 2', 'logo': '/assets/images/channels/ssport2_logo.png'},
            {'data-stream-url': 'ssmartspor', 'name': 'Smart Spor', 'logo': '/assets/images/channels/smartspor.jpg'},
            {'data-stream-url': 'ssmartspor2', 'name': 'Smart Spor 2', 'logo': '/assets/images/channels/smartspor.jpg'},
            {'data-stream-url': 'strtspor', 'name': 'TRT Spor', 'logo': '/assets/images/channels/trtspor.png'},
            {'data-stream-url': 'strtspor2', 'name': 'TRT Spor 2', 'logo': '/assets/images/channels/trtspor2.png'},
        ]
        
        channels = manual_channels
        print(f"Using manual channel list: {len(channels)} channels")
    
    print(f"\n📊 Total channels to process: {len(channels)}")
    
    # 3. Stream linklerini al
    stream_info = get_stream_links(domain_info, channels)
    
    if not stream_info or not stream_info['channels']:
        print("\n" + "=" * 60)
        print("ERROR: Could not fetch any stream links!")
        print("=" * 60)
        print("#EXTM3U\n#EXTINF:-1,Error: Could not generate stream links")
        return
    
    print()
    
    # 4. M3U playlist oluştur
    m3u_content = generate_m3u_playlist(stream_info)
    
    # 5. Dosyaları kaydet
    save_files(m3u_content, stream_info)
    
    # 6. Kısa özet göster
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    print(f"Active Domain: {domain_info['url']}")
    print(f"Stream Domain: {stream_info.get('stream_domain', 'N/A')}")
    print(f"Channels Found: {len(channels)}")
    print(f"Streams Generated: {stream_info['successful']}")
    print(f"M3U File: sporcafe.m3u")
    print(f"JSON File: channels.json")
    print("=" * 60)
    
    # İlk birkaç kanalı göster
    print("\nFirst few channels in playlist:")
    print("-" * 40)
    lines = m3u_content.split('\n')
    for i, line in enumerate(lines[:20]):
        if line.startswith('#EXTINF:'):
            print(f"  {line.split(',')[-1]}")
    if len(stream_info['channels']) > 5:
        print(f"  ... and {len(stream_info['channels']) - 5} more channels")
    
    print("\n✅ Playlist ready to use!")

if __name__ == "__main__":
    main()
