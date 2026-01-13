import requests
import re
import html
import unicodedata
from bs4 import BeautifulSoup

OUTPUT_FILE = "inat.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json,text/html,*/*",
    "Referer": "https://google.com"
}

# -------------------------------------------------
def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    return unicodedata.normalize("NFC", text).strip()

# -------------------------------------------------
def find_active_domain():
    print("🔍 Aktif domain aranıyor...")
    for i in range(1204, 2000):
        url = f"https://inattv{i}.xyz"
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code == 200 and len(r.text) > 1000:
                print(f"✅ Aktif domain bulundu: {url}")
                return url
        except:
            pass
    return None

# -------------------------------------------------
def get_channel_m3u8(domain, channel_id):
    try:
        url = f"{domain}/channel.html?id=yayinzirve"
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.encoding = r.apparent_encoding

        m = re.search(r'baseurl\s*=\s*"(.*?)"', r.text)
        if not m:
            return ""

        return f"{m.group(1)}{channel_id}.m3u8"
    except:
        return ""

# -------------------------------------------------
def get_matches_from_api(domain):
    api_urls = [
        "/api/live",
        "/ajax/live",
        "/api/matches",
        "/data/matches.json"
    ]

    for api in api_urls:
        try:
            r = requests.get(domain + api, headers=HEADERS, timeout=8)
            if r.status_code != 200:
                continue

            data = r.json()
            if not isinstance(data, list):
                continue

            print(f"✅ API bulundu: {api}")

            maclar = []
            for item in data:
                kanal_id = item.get("id") or item.get("channel_id")
                title = item.get("title") or item.get("name")

                if not kanal_id or not title:
                    continue

                m3u8 = get_channel_m3u8(domain, kanal_id)
                if not m3u8:
                    continue

                maclar.append({
                    "tvg_id": kanal_id,
                    "kanal_adi": clean_text(title),
                    "dosya": m3u8
                })

            if maclar:
                return maclar

        except:
            continue

    return []

# -------------------------------------------------
def get_matches_from_html(domain):
    try:
        r = requests.get(domain + "/live", headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")

        maclar = []
        for a in soup.select("a[href*='id=']"):
            m = re.search(r"id=([^&]+)", a.get("href", ""))
            if not m:
                continue

            kanal_id = m.group(1)
            name = clean_text(a.get_text(" ", strip=True))

            if not name:
                continue

            m3u8 = get_channel_m3u8(domain, kanal_id)
            if not m3u8:
                continue

            maclar.append({
                "tvg_id": kanal_id,
                "kanal_adi": name,
                "dosya": m3u8
            })

        return maclar
    except:
        return []

# -------------------------------------------------
def create_m3u(maclar, domain):
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        f.write("#EXTM3U\n")
        for k in maclar:
            f.write(
                f'#EXTINF:-1 tvg-id="{k["tvg_id"]}" group-title="İnat",{k["kanal_adi"]}\n'
            )
            f.write(f"#EXTVLCOPT:http-referrer={domain}\n")
            f.write(k["dosya"] + "\n")

    print(f"✔ M3U oluşturuldu: {OUTPUT_FILE}")

# -------------------------------------------------
if __name__ == "__main__":
    domain = find_active_domain()
    if not domain:
        print("❌ Domain bulunamadı")
        exit(1)

    print("📡 Yayınlar API’den deneniyor...")
    maclar = get_matches_from_api(domain)

    if not maclar:
        print("⚠ API yok, HTML deneniyor...")
        maclar = get_matches_from_html(domain)

    print(f"📊 Bulunan yayın: {len(maclar)}")

    if maclar:
        create_m3u(maclar, domain)
    else:
        print("❌ Hiç yayın bulunamadı")
