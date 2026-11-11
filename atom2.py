import requests
import re
import json
import base64
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
#  AtomSporTV  –  Canlı Maç + TV Kanalları M3U (V2)
# ─────────────────────────────────────────────
START_URL    = "https://url24.link/AtomSporTV"
MATCHES_URL  = "https://teletv15.top/load/matches.php"
CHANNELS_URL = "https://teletv15.top/load/channels.php"
OUTPUT_FILE  = "atom_mac.m3u"

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://url24.link/'
}

def get_base_domain():
    try:
        r1 = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in r1.headers:
            r2 = requests.get(r1.headers['location'], headers=headers, allow_redirects=False, timeout=10)
            if 'location' in r2.headers:
                domain = r2.headers['location'].strip().rstrip('/')
                # Bazı durumlarda www. eklenmemiş olabilir, garantiye alalım
                if not domain.startswith("http"):
                    domain = "https://" + domain
                return domain
    except Exception:
        pass
    return "https://www.atomsportv520.top"

def normalize_logo(src, base_domain):
    if not src: return ""
    if src.startswith("http"): return src
    if src.startswith("//"): return "https:" + src
    return base_domain + "/" + src.lstrip("/")

def parse_list(html, base_domain):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for a in soup.find_all('a', class_='single-match', href=True):
        href = a['href']
        mid = re.search(r'matches\?id=([\w\-]+)', href)
        if not mid: continue
        match_id = mid.group(1)

        imgs = a.find_all('img')
        home_logo = normalize_logo(imgs[0]['src'], base_domain) if len(imgs) >= 1 else ""
        away_logo = normalize_logo(imgs[-1]['src'], base_domain) if len(imgs) >= 2 else ""

        date_div = a.select_one('.date')
        event_div = a.select_one('.event')
        home_div = a.select_one('.teams .home')
        away_div = a.select_one('.teams .away')

        sport = date_div.get_text(strip=True) if date_div else ""
        time, league = "", ""
        if event_div:
            ev_text = event_div.get_text(strip=True)
            if '|' in ev_text:
                time, league = [x.strip() for x in ev_text.split('|', 1)]
            else:
                league = ev_text

        items.append({
            'id': match_id,
            'sport': sport,
            'home': home_div.get_text(strip=True) if home_div else "",
            'away': away_div.get_text(strip=True) if away_div else "",
            'home_logo': home_logo,
            'away_logo': away_logo,
            'logo': home_logo or away_logo,
            'time': time,
            'league': league,
        })
    return items

def get_matches(base_domain):
    try:
        resp = requests.get(MATCHES_URL, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        return parse_list(resp.text, base_domain)
    except Exception as e:
        print(f"{RED}Maç listesi hatası: {e}{RESET}")
        return []

def get_channels(base_domain):
    try:
        resp = requests.get(CHANNELS_URL, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        items = parse_list(resp.text, base_domain)
        for c in items:
            c['name'] = c['home']
            c['logo'] = c['away_logo'] or c['home_logo']
        return items
    except Exception as e:
        print(f"{RED}Kanal listesi hatası: {e}{RESET}")
        return []

def extract_stream_url(resource_id, base_domain):
    """Gelişmiş Stream Ayıklayıcı"""
    h = headers.copy()
    h['Referer'] = f"{base_domain}/"
    
    match_url = f"{base_domain}/matches?id={resource_id}"
    try:
        resp = requests.get(match_url, headers=h, timeout=15)
        html = resp.text
        
        # 1. Yöntem: Iframe içinde başka bir player sayfası var mı?
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            if iframe_url.startswith('//'): iframe_url = 'https:' + iframe_url
            elif iframe_url.startswith('/'): iframe_url = base_domain + iframe_url
            
            h['Referer'] = match_url
            iframe_resp = requests.get(iframe_url, headers=h, timeout=15)
            html = iframe_resp.text # HTML'i iframe içeriğiyle değiştir
            
            # Görseldeki gibi track istekleri var mı?
            track_match = re.search(r'(https?://[^\s"\']+tracks[^\s"\']+\.m3u8[^\s"\']*)', html)
            if track_match: return track_match.group(1)

        # 2. Yöntem: Base64 gizlenmiş veri var mı?
        # Genelde player scriptleri içinde "atob('...')" şeklinde saklanır
        b64_matches = re.findall(r'atob\([\'"]([^\'"]+)[\'"]\)', html)
        for b64 in b64_matches:
            try:
                decoded = base64.b64decode(b64).decode('utf-8')
                m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', decoded)
                if m3u8_match: return m3u8_match.group(1)
            except: pass

        # 3. Yöntem: JSON veya Script içinde direkt URL var mı?
        # Görseldeki .help veya corestream gibi yapıları arıyoruz
        patterns = [
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
            r'"stream"\s*:\s*"(.*?)"',
            r'"url"\s*:\s*"(.*?\.m3u8[^"]*)"',
            r'(https?://[^"\']+\.help/[^"\']+\.m3u8)',
            r'(https?://[^"\']+workers\.dev/[^"\']+)'
        ]
        for pat in patterns:
            mm = re.search(pat, html)
            if mm: 
                found_url = mm.group(1).replace('\\/', '/').replace('\\', '')
                return found_url
                
        # 4. Yöntem: Sayfa içindeki JavaScript dosyalarını tara (Bazen link JS içine gömülüdür)
        js_files = re.findall(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', html)
        for js_url in js_files:
            if js_url.startswith('//'): js_url = 'https:' + js_url
            elif js_url.startswith('/'): js_url = base_domain + js_url
            
            try:
                js_resp = requests.get(js_url, headers=h, timeout=5)
                js_match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', js_resp.text)
                if js_match: return js_match.group(1)
            except: pass

        return None
    except Exception as e:
        print(f"  {RED}[Hata: {resource_id} - {str(e)}]{RESET}")
        return None

def build_m3u(working_matches, working_channels, base_domain):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for m in working_matches:
            display = f"{m['home']} - {m['away']} [{m['time']}]"
            group = f"CANLI MAÇLAR - {m['league']}"
            f.write(f'#EXTINF:-1 tvg-logo="{m["logo"]}" group-title="{group}",{display}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}/\n')
            f.write(f"{m['url']}\n\n")
        for c in working_channels:
            f.write(f'#EXTINF:-1 tvg-logo="{c["logo"]}" group-title="TV Kanalları",{c["name"]}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}/\n')
            f.write(f"{c['url']}\n\n")
    print(f"\n{GREEN}[✓] {OUTPUT_FILE} başarıyla oluşturuldu.{RESET}")

def main():
    print(f"\n{GREEN}AtomSporTV M3U Oluşturucu Başlatıldı...{RESET}")
    base_domain = get_base_domain()
    print(f"Ana Domain: {base_domain}")

    matches = get_matches(base_domain)
    channels = get_channels(base_domain)

    working_matches = []
    print(f"\n{YELLOW}Maçlar test ediliyor ({len(matches)})...{RESET}")
    for m in matches:
        url = extract_stream_url(m['id'], base_domain)
        if url:
            m['url'] = url
            working_matches.append(m)
            print(f"  {GREEN}✓{RESET} {m['home']} vs {m['away']}")
        else:
            print(f"  {RED}✗{RESET} {m['home']} vs {m['away']}")

    working_channels = []
    print(f"\n{YELLOW}Kanallar test ediliyor ({len(channels)})...{RESET}")
    for c in channels:
        url = extract_stream_url(c['id'], base_domain)
        if url:
            c['url'] = url
            working_channels.append(c)
            print(f"  {GREEN}✓{RESET} {c['name']}")
        else:
            print(f"  {RED}✗{RESET} {c['name']}")

    build_m3u(working_matches, working_channels, base_domain)

if __name__ == "__main__":
    main()
