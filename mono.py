import requests
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAKLAR
DOMAIN_API_URL = "https://data-reality.com/domain.php"
MATCHES_API_URL = "https://data-reality.com/matches.php"
CHANNELS_API_URL = "https://data-reality.com/channels.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://canlimacizlejustin.online/"
}

def get_base_url_with_fallback():
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            base_url = base_url.replace("\\", "").rstrip('/')
            return base_url + "/"
    except:
        pass
    parsed = urlparse(MATCHES_API_URL)
    return f"{parsed.scheme}://{parsed.netloc}/"

def parse_matches_from_html(html_content):
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
            
            detail_div = link.find('div', class_='match-detail')
            if not detail_div: continue
                
            event_div = detail_div.find('div', class_='event')
            event_text = event_div.text.strip() if event_div else ''
            
            time, league = '', ''
            if '|' in event_text:
                parts = event_text.split('|')
                time, league = parts[0].strip(), parts[1].strip()
            else:
                league = event_text
            
            teams_div = detail_div.find('div', class_='teams')
            if teams_div:
                home = teams_div.find('div', class_='home').text.strip()
                away = teams_div.find('div', class_='away').text.strip()
                
                if channel_id:
                    matches.append({
                        'id': channel_id,
                        'home': home,
                        'away': away,
                        'home_logo': home_logo,
                        'away_logo': away_logo,
                        'league': league,
                        'time': time
                    })
        except: continue
    return matches

def parse_channels_from_html(html_content):
    channels = []
    soup = BeautifulSoup(html_content, 'html.parser')
    channel_links = soup.find_all('a', class_='single-match')
    
    for link in channel_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            detail_div = link.find('div', class_='match-detail')
            if detail_div and '7/24' in detail_div.text:
                teams_div = detail_div.find('div', class_='teams')
                home_name = teams_div.find('div', class_='home').text.strip()
                logo_url = teams_div.find('div', class_='away').find('img').get('src', '')
                
                if channel_id:
                    channels.append({'id': channel_id, 'name': home_name, 'logo': logo_url})
        except: continue
    return channels

def create_m3u_with_logos(matches, channels, base_url, referrer):
    m3u_list = ["#EXTM3U\n"]
    
    # --- CANLI MAÇLAR ---
    for m in matches:
        display_name = f"{m['home']} - {m['away']} [{m['time']}]"
        group_title = f"CANLI MAÇLAR - {m['league']}"
        main_logo = m['home_logo'] or m['away_logo']
        
        m3u_list.append(f'#EXTINF:-1 tvg-logo="{main_logo}" group-title="{group_title}",{display_name}')
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{m["id"]}/mono.m3u8')
        m3u_list.append(f'# İki logo: {m["home_logo"]} | {m["away_logo"]}\n')

    # --- 7/24 KANALLAR ---
    for c in channels:
        m3u_list.append(f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="7/24 KANALLAR",{c["name"]}')
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{c["id"]}/mono.m3u8\n')
        
    return m3u_list

def main():
    print("🚀 Justin TV Verileri Çekiliyor...")
    base_url = get_base_url_with_fallback()
    referrer = "https://canlimacizlejustin.online"
    
    try:
        # Maçlar
        resp_m = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        matches = parse_matches_from_html(resp_m.text)
        
        # Kanallar
        resp_c = requests.get(CHANNELS_API_URL, headers=HEADERS, timeout=15)
        channels = parse_channels_from_html(resp_c.text)
        
        if matches or channels:
            m3u_content = create_m3u_with_logos(matches, channels, base_url, referrer)
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_content))
            print(f"✅ mono.m3u başarıyla oluşturuldu! ({len(matches)} Maç, {len(channels)} Kanal)")
        else:
            print("❌ Veri bulunamadı.")
            
    except Exception as e:
        print(f"💥 Hata oluştu: {e}")

if __name__ == "__main__":
    main()
