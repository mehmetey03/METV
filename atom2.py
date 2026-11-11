import requests
import re
import json
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
#  AtomSporTV  –  Canlı Maç + TV Kanalları M3U (V3)
#  Node.js API mantığı ile güncellendi
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
    """Yönlendirmeleri takip ederek gerçek ana domaini bulur."""
    fallback = "https://www.atomsportv520.top"
    current_url = START_URL
    referer = headers['Referer']
    
    try:
        for _ in range(10):
            h = headers.copy()
            h['Referer'] = referer
            
            res = requests.get(current_url, headers=h, allow_redirects=False, timeout=10)
            
            if 300 <= res.status_code < 400:
                location = res.headers.get('location')
                if location:
                    referer = current_url
                    current_url = requests.compat.urljoin(current_url, location)
                    continue
            
            # Sayfa yüklendi, JS içindeki channels.php fetch'ini ara
            match = re.search(r'fetch\s*\(\s*["\'](https?://[^/"\']+)/load/channels\.php', res.text, re.IGNORECASE)
            if match:
                domain = match.group(1)
                print(f"  {GREEN}[+] Ana Domain Bulundu: {domain}{RESET}")
                return domain
            break
            
    except Exception as e:
        print(f"  {YELLOW}[!] Domain bulma hatası: {e}{RESET}")
        
    print(f"  {YELLOW}[!] Fallback domain kullanılıyor: {fallback}{RESET}")
    return fallback

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

def get_stream_url(resource_id, base_domain):
    """
    Node.js kodundaki gibi yayinlink.php API'sine istek atar.
    Dönen JSON içindeki 'deismackanal' değerini alır.
    """
    url = f"{base_domain}/load/yayinlink.php?id={resource_id}"
    try:
        # Referer olarak anasayfayı gönderiyoruz
        h = headers.copy()
        h['Referer'] = f"{base_domain}/"
        
        resp = requests.get(url, headers=h, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            # Node.js kodunda aranan anahtar kelime
            if isinstance(data, dict) and 'deismackanal' in data:
                stream = data['deismackanal'].strip()
                if stream:
                    return stream
        return None
    except Exception:
        return None

def build_m3u(working_matches, working_channels, base_domain):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        
        # Yayınlar için gerekli header'ları M3U dosyasına ekliyoruz
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
    
    matches = get_matches(base_domain)
    channels = get_channels(base_domain)

    working_matches = []
    print(f"\n{YELLOW}Maçlar test ediliyor ({len(matches)})...{RESET}")
    for m in matches:
        # Direkt API'den stream linkini çekiyoruz
        url = get_stream_url(m['id'], base_domain)
        if url:
            m['url'] = url
            working_matches.append(m)
            print(f"  {GREEN}✓{RESET} {m['home']} vs {m['away']}")
        else:
            print(f"  {RED}✗{RESET} {m['home']} vs {m['away']}")

    working_channels = []
    print(f"\n{YELLOW}Kanallar test ediliyor ({len(channels)})...{RESET}")
    for c in channels:
        url = get_stream_url(c['id'], base_domain)
        if url:
            c['url'] = url
            working_channels.append(c)
            print(f"  {GREEN}✓{RESET} {c['name']}")
        else:
            print(f"  {RED}✗{RESET} {c['name']}")

    build_m3u(working_matches, working_channels, base_domain)

if __name__ == "__main__":
    main()
