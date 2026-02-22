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
    """
    Maçları HTML'den parse et - İKİ LOGO DA ÇEKİLİYOR
    HTML yapısı:
    <a class="single-match show" href="channel?id=b2">
        <img src="home_logo_url">  # Ev sahibi logosu
        <div class="match-detail">...</div>
        <img src="away_logo_url">  # Deplasman logosu
    </a>
    """
    matches = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    match_links = soup.find_all('a', class_='single-match')
    
    for link in match_links:
        try:
            # Kanal ID
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            # Tüm resimleri bul (genelde 2 tane)
            imgs = link.find_all('img')
            
            # İlk resim ev sahibi logosu, ikinci resim deplasman logosu
            home_logo = imgs[0].get('src') if len(imgs) > 0 else ''
            away_logo = imgs[1].get('src') if len(imgs) > 1 else ''
            
            # Detayları bul
            detail_div = link.find('div', class_='match-detail')
            if not detail_div:
                continue
                
            # Maç tipi (Futbol, Basketbol vb.)
            date_div = detail_div.find('div', class_='date')
            match_type = date_div.text.strip() if date_div else 'football'
            
            # Saat ve lig
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
            
            # Takım isimleri
            teams_div = detail_div.find('div', class_='teams')
            if teams_div:
                home_team = teams_div.find('div', class_='home')
                away_team = teams_div.find('div', class_='away')
                
                home = home_team.text.strip() if home_team else ''
                away = away_team.text.strip() if away_team else ''
                
                if channel_id and home and away:
                    # Kanal adı
                    channel_name = f"{home} - {away}"
                    if time:
                        channel_name += f" [{time}]"
                    
                    # Logo için (VLC'de gösterilecek - ev sahibi logosu)
                    main_logo = home_logo or away_logo or ""
                    
                    matches.append({
                        'id': channel_id,
                        'name': channel_name,
                        'home': home,
                        'away': away,
                        'home_logo': home_logo,  # Ev sahibi logosu
                        'away_logo': away_logo,  # Deplasman logosu
                        'main_logo': main_logo,  # Ana logo (VLC için)
                        'league': league,
                        'type': match_type.lower(),
                        'time': time,
                        'source': 'match'
                    })
        except Exception as e:
            print(f"⚠️ Parse hatası (maç): {e}")
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

def save_detailed_json(matches, channels, filename="justin_detayli.json"):
    """Tüm detayları JSON olarak kaydet (her iki logo dahil)"""
    data = {
        'matches': matches,
        'channels': channels,
        'total_matches': len(matches),
        'total_channels': len(channels),
        'total_broadcasts': len(matches) + len(channels)
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Detaylı JSON kaydedildi: {filename}")

def create_m3u_with_logos(matches, channels, base_url, referrer):
    """M3U playlist oluştur - tvg-logo olarak main_logo kullan"""
    m3u_list = ["#EXTM3U"]
    
    # Maçları ekle
    print("\n📝 Maçlar M3U'ya ekleniyor...")
    for match in matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        
        # EXTINF satırı (main_logo kullan)
        extinf = f'#EXTINF:-1 tvg-logo="{match["main_logo"]}" group-title="{group}",{match["name"]}'
        
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{match["id"]}/mono.m3u8')
        
        # Her iki logoyu da yorum satırı olarak ekle (debug için)
        if match['home_logo'] and match['away_logo']:
            m3u_list.append(f'# LOGOLAR: 🏠 {match["home_logo"]} | ✈️ {match["away_logo"]}')
    
    # Sabit kanalları ekle
    print("📺 Sabit kanallar M3U'ya ekleniyor...")
    for channel in channels:
        extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{channel["id"]}/mono.m3u8')
    
    return m3u_list

def main():
    print("🔍 Kaynaklardan bilgiler alınıyor...")
    print("=" * 70)
    
    base_url = get_base_url_with_fallback()
    referrer = get_referrer_with_fallback()
    
    print(f"📡 Referrer: {referrer}")
    print(f"🚀 Base URL: {base_url}")
    print("=" * 70)
    
    all_matches = []
    all_channels = []
    
    # 1. Maçları çek (ÇİFT LOGOLU)
    try:
        print("\n📡 Maçlar yükleniyor...")
        r = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        all_matches = parse_matches_from_html(r.text)
        print(f"✅ {len(all_matches)} maç bulundu.")
        
        # İstatistik
        double_logo = sum(1 for m in all_matches if m['home_logo'] and m['away_logo'])
        single_logo = sum(1 for m in all_matches if (m['home_logo'] or m['away_logo']) and not (m['home_logo'] and m['away_logo']))
        no_logo = len(all_matches) - double_logo - single_logo
        
        print(f"   📊 Logo durumu:")
        print(f"      ✓ Çift logo: {double_logo} maç")
        print(f"      ✓ Tek logo: {single_logo} maç")
        print(f"      ⚠️ Logosuz: {no_logo} maç")
        
        # Örnek maçlar
        print(f"\n   📺 Örnek maçlar:")
        for match in all_matches[:3]:
            logo_status = "🏠✈️" if match['home_logo'] and match['away_logo'] else "🏠" if match['home_logo'] else "✈️" if match['away_logo'] else "❌"
            print(f"      {logo_status} {match['name']}")
            
    except Exception as e:
        print(f"⚠️ Maç hatası: {e}")
    
    # 2. Sabit kanalları çek
    try:
        print("\n📺 Sabit kanallar yükleniyor...")
        r = requests.get(CHANNELS_API_URL, headers=HEADERS, timeout=15)
        all_channels = parse_channels_from_html(r.text)
        print(f"✅ {len(all_channels)} sabit kanal bulundu.")
        
        # Örnek kanallar
        print(f"\n   📺 Örnek kanallar:")
        for channel in all_channels[:3]:
            print(f"      {'🖼️' if channel['logo'] else '❌'} {channel['name']}")
            
    except Exception as e:
        print(f"⚠️ Kanal hatası: {e}")
    
    # 3. M3U oluştur
    if all_matches or all_channels:
        m3u_list = create_m3u_with_logos(all_matches, all_channels, base_url, referrer)
        
        # M3U dosyasını kaydet
        output_file = "justin_playlist.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        # Detaylı JSON kaydet
        save_detailed_json(all_matches, all_channels, "justin_detayli.json")
        
        print("\n" + "=" * 70)
        print(f"✅ İŞLEM TAMAMLANDI!")
        print(f"📊 Maç sayısı: {len(all_matches)}")
        print(f"📊 Kanal sayısı: {len(all_channels)}")
        print(f"📊 Toplam yayın: {len(all_matches) + len(all_channels)}")
        print(f"📊 M3U satır sayısı: {len(m3u_list)}")
        print(f"💾 M3U dosya: {output_file}")
        print("=" * 70)
    else:
        print("\n❌ Hiç veri bulunamadı!")

if __name__ == "__main__":
    main()
