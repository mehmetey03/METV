import re
import html
import unicodedata
import cloudscraper
from bs4 import BeautifulSoup

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/inatdom/refs/heads/main/domain.txt"
OUTPUT_FILE = "inat.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "desktop": True
    }
)

# -------------------- Yardımcı --------------------
def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)
    return unicodedata.normalize("NFC", text).strip()

# -------------------- Domain Al --------------------
def get_active_domain():
    r = scraper.get(DOMAIN_TXT_URL, timeout=10)
    if r.status_code != 200:
        raise Exception("domain.txt okunamadı")

    m = re.search(r"guncel_domain\s*=\s*(https?://[^\s]+)", r.text)
    if not m:
        raise Exception("guncel_domain bulunamadı")

    return m.group(1).rstrip("/")

# -------------------- m3u8 Al --------------------
def get_channel_m3u8(domain, channel_id):
    try:
        url = f"{domain}/channel.html?id=yayinzirve"
        r = scraper.get(url, timeout=10)
        r.encoding = r.apparent_encoding

        m = re.search(r'baseurl\s*=\s*"(.*?)"', r.text)
        if not m:
            return ""

        return f"{m.group(1)}{channel_id}.m3u8"
    except:
        return ""

# -------------------- Maçları Çek --------------------
def get_matches(domain):
    try:
        url = domain + "/live"
        r = scraper.get(url, timeout=10)
        r.encoding = r.apparent_encoding

        soup = BeautifulSoup(r.text, "html.parser")
        maclar = []

        # GENEL ve DAYANIKLI SELECTOR
        for item in soup.select("a[href*='id=']"):
            href = item.get("href", "")
            m = re.search(r"id=([^&]+)", href)
            if not m:
                continue

            kanal_id = m.group(1)

            name = clean_text(item.get_text(" ", strip=True))
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

# -------------------- M3U Oluştur --------------------
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

# -------------------- ÇALIŞTIR --------------------
if __name__ == "__main__":
    try:
        print("Güncel domain alınıyor...")
        domain = get_active_domain()
        print(f"{GREEN}[✓] Domain: {domain}{RESET}")

        print("Maçlar çekiliyor...")
        maclar = get_matches(domain)
        print(f"{GREEN}{len(maclar)} maç bulundu{RESET}")

        if maclar:
            create_m3u(maclar, domain)
        else:
            print("⚠ Maç bulunamadı")

    except Exception as e:
        print("HATA:", e)
