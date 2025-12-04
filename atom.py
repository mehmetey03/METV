import requests
import re

# AtomSporTV
START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://url24.link/'
}

def get_base_domain():
    """Ana domain'i bul"""
    try:
        response = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if 'location' in response.headers:
            location1 = response.headers['location']
            response2 = requests.get(location1, headers=headers, allow_redirects=False, timeout=10)
            if 'location' in response2.headers:
                base_domain = response2.headers['location'].strip().rstrip('/')
                print(f"Ana Domain: {base_domain}")
                return base_domain
        return "https://www.atomsportv480.top"
    except Exception as e:
        print(f"Domain hatası: {e}")
        return "https://www.atomsportv480.top"

def get_channel_m3u8(channel_id, base_domain):
    """PHP mantığı ile m3u8 linkini al"""
    try:
        matches_url = f"{base_domain}/matches?id={channel_id}"
        response = requests.get(matches_url, headers=headers, timeout=10)
        html = response.text

        # fetch URL'si
        fetch_match = re.search(r'fetch\(["\'](.*?)["\']', html)
        if fetch_match:
            fetch_url = fetch_match.group(1).strip()
            if not fetch_url.endswith(channel_id):
                fetch_url += channel_id

            custom_headers = headers.copy()
            custom_headers['Origin'] = base_domain
            custom_headers['Referer'] = base_domain
            response2 = requests.get(fetch_url, headers=custom_headers, timeout=10)
            data = response2.text

            # m3u8 URL
            m3u8_match = re.search(r'"deismackanal":"(.*?)"', data)
            if m3u8_match:
                return m3u8_match.group(1).replace('\\', '')
            m3u8_match = re.search(r'"(?:stream|url|source)":\s*"(.*?\.m3u8)"', data)
            if m3u8_match:
                return m3u8_match.group(1).replace('\\', '')
        return None
    except:
        return None

def extract_channels_from_json(base_domain):
    """Dinamik JSON endpoint ile tüm kanalları al"""
    print("Tüm kanallar JSON üzerinden alınıyor...")
    try:
        url = f"{base_domain}/home/channels.php"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Kanal listesi okunamadı: {response.status_code}")
            return []

        data = response.json()
        channels = []
        for item in data:
            channel_id = item.get("id") or item.get("match_id")
            if not channel_id:
                continue
            channel_name = item.get("name") or channel_id.replace("-", " ").title()
            group = "TV Kanalları"
            channels.append({
                "id": channel_id,
                "name": channel_name,
                "group": group
            })
        return channels
    except Exception as e:
        print(f"JSON kanallar alınamadı: {e}")
        return []

def test_and_create_m3u(channels, base_domain):
    """Kanalları test et ve M3U oluştur"""
    working_channels = []
    print(f"{len(channels)} kanal test ediliyor...")
    for i, ch in enumerate(channels):
        print(f"{i+1:3d}. {ch['name'][:40]:40s}...", end=" ", flush=True)
        url = get_channel_m3u8(ch['id'], base_domain)
        if url:
            print(f"{GREEN}✓{RESET}")
            ch['url'] = url
            working_channels.append(ch)
        else:
            print("✗")
    return working_channels

def create_m3u_file(channels, base_domain):
    if not channels:
        print("❌ M3U oluşturmak için kanal yok!")
        return
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            f.write(f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={base_domain}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(ch['url'] + "\n")
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {len(channels)} kanal eklendi.")

def main():
    print(f"{GREEN}AtomSporTV M3U Güncel Script{RESET}")
    base_domain = get_base_domain()
    channels = extract_channels_from_json(base_domain)
    if not channels:
        print("❌ Hiç kanal bulunamadı!")
        return
    working_channels = test_and_create_m3u(channels, base_domain)
    create_m3u_file(working_channels, base_domain)

if __name__ == "__main__":
    main()
