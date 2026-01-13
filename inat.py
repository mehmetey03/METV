import requests
import re
import html
import unicodedata
from bs4 import BeautifulSoup

OUTPUT_FILE = "inat.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
            r = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 1000:
                print(f"{GREEN}✅ Aktif domain bulundu: {url}{RESET}")
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
def get_matches(domain):
    try:
        url = domain + "/live"
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.encoding = r.apparent_encoding

        soup = BeautifulSoup(r.text, "html.parser")
        maclar = []

        for a in soup.select("a[href*='id=']"):
            href = a.get("href", "")
            m = re.search(r"id=([^&]+)", href)
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

    except Exception as e:
        print("get_matches hatası:", e)
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

    print(f"{GREEN}✔ M3U oluşturuldu: {OUTPUT_FILE}{RESET}")

# -------------------------------------------------
if __name__ == "__main__":
    domain = find_active_domain()

    if not domain:
        print("❌ Aktif domain bulunamadı")
        exit(1)

    print("📡 Maçlar çekiliyor...")
    maclar = get_matches(domain)
    print(f"{GREEN}{len(maclar)} yayın bulundu{RESET}")

    if maclar:
        create_m3u(maclar, domain)
    else:
        print("⚠ Maç bulunamadı, M3U oluşturulmadı")
