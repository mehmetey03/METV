import requests
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://canlimacizlejustin.online/domain.php"
MATCHES_API_URL = "https://canlimacizlejustin.online/matches.php"
CHANNELS_API_URL = "https://canlimacizlejustin.online/channels.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://canlimacizlejustin.online/"
}

def get_base_url_with_fallback():
    """Base URL'i al"""
    # Domain API'si
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            base_url = base_url.replace("\\", "").rstrip('/')
            print(f"✅ Domain API'den base URL alındı: {base_url}")
            return base_url + "/"
    except Exception as e:
        print(f"⚠️ Domain API hatası: {e}")
    
    # Varsayılan
    parsed = urlparse(MATCHES_API_URL)
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    print(f"⚠️ Varsayılan base URL: {base_url}")
    return base_url

def get_referrer_with_fallback():
    """Referrer adresini al"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(MATCHES_API_URL)
        referrer = f"{parsed.scheme}://{parsed.netloc}"
        print(f"📡 Referrer: {referrer}")
        return referrer
    except:
        return "https://canlimacizlejustin.online"

def parse_matches_from_html(html_content):
    """Maçları HTML'den parse et"""
    matches = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    match_links = soup.find_all('a', class_='single-match')
    
    for link in match_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            imgs = link.find_all('img')
            home_logo = imgs[0].get('src') if len(imgs) > 0 else ''
            away_logo = imgs[1].get('src') if len(imgs) > 1 else ''
            
            # Logo URL'lerini tamamla
            if home_logo and not home_logo.startswith('http'):
                home_logo = f"https://canlimacizlejustin.online/{home_logo.lstrip('/')}"
            if away_logo and not away_logo.startswith('http'):
                away_logo = f"https://canlimacizlejustin.online/{away_logo.lstrip('/')}"
            
            detail_div = link.find('div', class_='match-detail')
            if detail_div:
                event_div = detail_div.find('div', class_='event')
                event_text = event_div.text.strip() if event_div else ''
                
                time = ''
                league = ''
                if '|' in event_text:
                    parts = event_text.split('|')
                    time = parts[0].strip()
                    league = parts[1].strip()
                else:
                    league = event_text
                
                teams_div = detail_div.find('div', class_='teams')
                if teams_div:
                    home_team = teams_div.find('div', class_='home')
                    away_team = teams_div.find('div', class_='away')
                    
                    home = home_team.text.strip() if home_team else ''
                    away = away_team.text.strip() if away_team else ''
                    
                    date_div = detail_div.find('div', class_='date')
                    match_type = date_div.text.strip() if date_div else 'football'
                    
                    if channel_id and home and away:
                        matches.append({
                            'id': channel_id,
                            'home': home,
                            'away': away,
                            'home_logo': home_logo,
                            'away_logo': away_logo,
                            'league': league,
                            'type': match_type.lower(),
                            'time': time,
                            'name': f"{home} - {away}" + (f" [{time}]" if time else ""),
                            'source': 'match'
                        })
        except Exception as e:
            continue
    
    return matches

def parse_channels_from_html(html_content):
    """Sabit kanalları HTML'den parse et"""
    channels = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    channel_links = soup.find_all('a', class_='single-match')
    
    for link in channel_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            detail_div = link.find('div', class_='match-detail')
            if detail_div:
                event_div = detail_div.find('div', class_='event')
                if event_div and '7/24' in event_div.text:
                    teams_div = detail_div.find('div', class_='teams')
                    if teams_div:
                        home_div = teams_div.find('div', class_='home')
                        channel_name = home_div.text.strip() if home_div else ''
                        
                        # Logo'yu bul (away div'inde img var)
                        away_div = teams_div.find('div', class_='away')
                        logo_img = away_div.find('img') if away_div else None
                        logo_url = logo_img.get('src') if logo_img else ''
                        
                        if logo_url and not logo_url.startswith('http'):
                            logo_url = f"https://canlimacizlejustin.online/{logo_url.lstrip('/')}"
                        
                        if channel_id and channel_name:
                            channels.append({
                                'id': channel_id,
                                'name': channel_name,
                                'logo': logo_url,
                                'type': 'static',
                                'source': 'channel'
                            })
        except Exception as e:
            continue
    
    return channels

def main():
    print("🔍 Kaynaklardan bilgiler alınıyor...")
    print("=" * 60)
    
    base_url = get_base_url_with_fallback()
    referrer = get_referrer_with_fallback()
    
    print(f"📡 Referrer: {referrer}")
    print(f"🚀 Base URL: {base_url}")
    print("=" * 60)
    
    m3u_list = ["#EXTM3U"]
    all_matches = []
    all_channels = []
    
    # 1. Maçları çek
    try:
        print("\n📡 Maçlar yükleniyor...")
        r = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        all_matches = parse_matches_from_html(r.text)
        print(f"✅ {len(all_matches)} maç bulundu.")
        
        for match in all_matches[:5]:  # İlk 5'i göster
            logo_info = []
            if match['home_logo']: logo_info.append("🏠")
            if match['away_logo']: logo_info.append("✈️")
            print(f"  ✓ {match['name']} {''.join(logo_info)}")
        if len(all_matches) > 5:
            print(f"  ... ve {len(all_matches)-5} maç daha")
            
    except Exception as e:
        print(f"⚠️ Maç hatası: {e}")
    
    # 2. Sabit kanalları çek
    try:
        print("\n📺 Sabit kanallar yükleniyor...")
        r = requests.get(CHANNELS_API_URL, headers=HEADERS, timeout=15)
        all_channels = parse_channels_from_html(r.text)
        print(f"✅ {len(all_channels)} sabit kanal bulundu.")
        
        for channel in all_channels[:5]:
            print(f"  ✓ {channel['name']} {'🖼️' if channel['logo'] else ''}")
        if len(all_channels) > 5:
            print(f"  ... ve {len(all_channels)-5} kanal daha")
            
    except Exception as e:
        print(f"⚠️ Kanal hatası: {e}")
    
    # 3. M3U oluştur
    print("\n📝 M3U oluşturuluyor...")
    
    # Maçları ekle
    for match in all_matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        logo = match['home_logo'] or match['away_logo'] or ""
        
        m3u_list.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{match["name"]}')
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{match["id"]}/mono.m3u8')
    
    # Sabit kanalları ekle
    for channel in all_channels:
        m3u_list.append(f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}')
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{channel["id"]}/mono.m3u8')
    
    # 4. Kaydet
    output_file = "mono.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_list))
    
    # JSON yedek
    json_output = "justin_veriler.json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump({
            'matches': all_matches,
            'channels': all_channels
        }, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"✅ İŞLEM TAMAMLANDI!")
    print(f"📊 Maç sayısı: {len(all_matches)}")
    print(f"📊 Kanal sayısı: {len(all_channels)}")
    print(f"📊 Toplam yayın: {len(all_matches) + len(all_channels)}")
    print(f"💾 M3U dosya: {output_file}")
    print(f"📋 JSON dosya: {json_output}")
    print("=" * 60)

if __name__ == "__main__":
    main()
