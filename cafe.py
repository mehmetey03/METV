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
    """Aktif domain'i bul"""
    print("🔍 Aktif domain aranıyor...")
    for i in range(15, 4, -1):
        url = f"https://www.sporcafe{i}.xyz/"
        print(f"  Deneniyor: {url}")
        html = fetch_url(url)
        if html and len(html) > 1000:
            print(f"  ✓ Bulundu: {url}")
            return {'url': url, 'html': html}
    return None

def get_stream_links(domain_info, channels):
    """Stream linklerini al"""
    print("🔗 Stream linkleri alınıyor...")
    
    # Stream domain'ini bul
    stream_match = re.search(r'https?:\/\/(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', domain_info['html'])
    if not stream_match:
        return None
    
    stream_domain = f"https://{stream_match.group(1)}"
    print(f"  Stream domain: {stream_domain}")
    
    results = {}
    successful = 0
    
    for i, channel in enumerate(channels, 1):
        channel_id = channel['id']
        print(f"  [{i:2d}/{len(channels)}] {channel['name']}")
        
        channel_url = f"{stream_domain}/index.php?id={channel_id}"
        html = fetch_url(channel_url)
        
        if html:
            ads_match = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', html)
            if ads_match:
                base_url = ads_match.group(1)
                if not base_url.endswith('/'):
                    base_url += '/'
                
                stream_url = f"{base_url}{channel_id}/playlist.m3u8"
                results[channel_id] = {
                    'url': stream_url,
                    'name': channel['name'],
                    'tvg_id': channel['tvg_id'],
                    'logo': channel['logo'],
                    'group': channel['group']
                }
                successful += 1
                print(f"      ✓ Başarılı")
    
    print(f"\n  📊 Sonuç: {successful}/{len(channels)} kanal bulundu")
    return {
        'referer': domain_info['url'],
        'stream_domain': stream_domain,
        'channels': results,
        'successful': successful
    }

def generate_m3u(stream_info):
    """M3U playlist oluştur"""
    print("\n📝 M3U playlist oluşturuluyor...")
    
    output = ["#EXTM3U"]
    
    # Kanalları isme göre sırala
    sorted_channels = sorted(
        stream_info['channels'].items(),
        key=lambda x: x[1]['name']
    )
    
    for channel_id, channel_data in sorted_channels:
        # EXTINF satırı
        extinf = f'#EXTINF:-1 tvg-id="{channel_data["tvg_id"]}" tvg-name="{channel_data["name"]}" tvg-logo="{channel_data["logo"]}" group-title="{channel_data["group"]}",{channel_data["name"]}'
        output.append(extinf)
        
        # Referer
        output.append(f'#EXTVLCOPT:http-referrer={stream_info["referer"]}')
        
        # Stream URL
        output.append(channel_data['url'])
        
        # Boş satır
        output.append("")
    
    return "\n".join(output)

def main():
    print("=" * 60)
    print("SPORCAFE M3U PLAYLIST OLUŞTURUCU")
    print("=" * 60)
    
    # Kanal listesi
    channels = [
        {"id": "sbeinsports-1", "name": "BeIN Sports 1", "tvg_id": "bein1", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/5rhmw31628798883.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-2", "name": "BeIN Sports 2", "tvg_id": "bein2", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/7uv6x71628799003.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-3", "name": "BeIN Sports 3", "tvg_id": "bein3", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/u3117i1628798857.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-4", "name": "BeIN Sports 4", "tvg_id": "bein4", "logo": "https://i.postimg.cc/0yjyF10x/bein4.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-5", "name": "BeIN Sports 5", "tvg_id": "bein5", "logo": "https://i.postimg.cc/BvjF7hx5/bein5.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsportshaber", "name": "BeIN Sports Haber", "tvg_id": "beinhd", "logo": "https://i.postimg.cc/x14Fs2kw/beinhd.png", "group": "BEIN SPORTS"},
        {"id": "sdazn1", "name": "DAZN 1", "tvg_id": "dazn1", "logo": "https://i.postimg.cc/QMgmHh7x/dazn1.png", "group": "DAZN"},
        {"id": "sdazn2", "name": "DAZN 2", "tvg_id": "dazn2", "logo": "https://i.postimg.cc/XY5YQvSd/dazn2.png", "group": "DAZN"},
        {"id": "saspor", "name": "A Spor", "tvg_id": "aspor", "logo": "https://i.postimg.cc/gJMK4kTN/aspor.png", "group": "YEREL SPOR"},
        {"id": "sssport", "name": "S Sport", "tvg_id": "ssport", "logo": "https://i.postimg.cc/TYcZT4zR/ssport.png", "group": "S SPORT"},
        {"id": "sssport2", "name": "S Sport 2", "tvg_id": "ssport2", "logo": "https://i.postimg.cc/WbftnShM/ssport2.png", "group": "S SPORT"},
        {"id": "sssplus1", "name": "S Sport Plus", "tvg_id": "ssportplus", "logo": "https://i.postimg.cc/rmK04Jxr/ssportplus.png", "group": "S SPORT"},
        {"id": "strtspor", "name": "TRT Spor", "tvg_id": "trtspor", "logo": "https://i.postimg.cc/jjTfdSTL/trtspor.png", "group": "TRT"},
        {"id": "strtspor2", "name": "TRT Spor 2", "tvg_id": "trtspor2", "logo": "https://i.postimg.cc/wvsvstyn/trtspor2.png", "group": "TRT"},
        {"id": "stv8", "name": "TV8", "tvg_id": "tv8", "logo": "https://i.postimg.cc/CLpftN9Y/tv8.png", "group": "DİĞER"},
        {"id": "sexxen-1", "name": "Exxen Spor 1", "tvg_id": "exxen1", "logo": "https://i.postimg.cc/B6t4z1d3/exxen.png", "group": "EXXEN"},
        {"id": "sexxen-2", "name": "Exxen Spor 2", "tvg_id": "exxen2", "logo": "https://i.postimg.cc/B6t4z1d3/exxen.png", "group": "EXXEN"},
        {"id": "ssmartspor", "name": "Smart Spor", "tvg_id": "smartspor", "logo": "https://i.postimg.cc/7YNxxHgM/smartspor.png", "group": "DİĞER"},
        {"id": "ssmartspor2", "name": "Smart Spor 2", "tvg_id": "smartspor2", "logo": "https://i.postimg.cc/7YNxxHgM/smartspor.png", "group": "DİĞER"},
        {"id": "stivibuspor-1", "name": "Tivibu Spor 1", "tvg_id": "tivibu1", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stivibuspor-2", "name": "Tivibu Spor 2", "tvg_id": "tivibu2", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stivibuspor-3", "name": "Tivibu Spor 3", "tvg_id": "tivibu3", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stivibuspor-4", "name": "Tivibu Spor 4", "tvg_id": "tivibu4", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stabiispor-1", "name": "Tabii Spor 1", "tvg_id": "tabii1", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-2", "name": "Tabii Spor 2", "tvg_id": "tabii2", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-3", "name": "Tabii Spor 3", "tvg_id": "tabii3", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-4", "name": "Tabii Spor 4", "tvg_id": "tabii4", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-5", "name": "Tabii Spor 5", "tvg_id": "tabii5", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "strt1", "name": "TRT 1", "tvg_id": "trt1", "logo": "https://i.postimg.cc/XYJkFyqV/trt1.png", "group": "TRT"},
    ]
    
    print(f"📺 Toplam {len(channels)} kanal işlenecek")
    
    # Aktif domain'i bul
    domain_info = get_active_domain()
    if not domain_info:
        print("\n✗ HATA: Aktif domain bulunamadı!")
        return
    
    # Stream linklerini al
    stream_info = get_stream_links(domain_info, channels)
    if not stream_info or not stream_info['channels']:
        print("\n✗ HATA: Stream linkleri alınamadı!")
        return
    
    # M3U playlist oluştur
    m3u_content = generate_m3u(stream_info)
    
    # Dosyaya yaz
    with open('sporcafe.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_content)
    
    print("\n" + "=" * 60)
    print("✅ İŞLEM TAMAMLANDI!")
    print("=" * 60)
    print(f"📡 Domain: {domain_info['url']}")
    print(f"📺 Kanal Sayısı: {stream_info['successful']}")
    print(f"💾 Dosya: sporcafe.m3u")
    print("=" * 60)
    
    # İlk 3 kanalı göster
    print("\n📋 Örnek M3U formatı:")
    print("-" * 40)
    lines = m3u_content.split('\n')[:12]  # İlk 3 kanalı göster
    for line in lines:
        print(line)

if __name__ == "__main__":
    main()
