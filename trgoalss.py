import requests
from bs4 import BeautifulSoup
import re

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/goal/refs/heads/main/domain.txt"
OUTPUT_FILE = "trgoalss.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

trgoals_ref = "https://trgoals1472.xyz"  # artık gerçek domain buradan alınabilir


def get_active_domain():
    r = requests.get(DOMAIN_TXT_URL, timeout=10)
    if r.status_code != 200:
        raise Exception("domain.txt okunamadı!")
    txt = r.text
    m = re.search(r"guncel_domain\s*=\s*(https?://[^\s]+)", txt)
    if not m:
        raise Exception("guncel_domain bulunamadı!")
    return m.group(1).strip()


def get_channel_m3u8(channel_url):
    """ Kanal sayfasından gerçek m3u8 linkini çek """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    r = requests.get(channel_url, headers=headers, timeout=10)
    if r.status_code != 200:
        return ""
    html = r.text
    # m3u8 linkini JS veya iframe içinden bul
    m = re.search(r'https?://[^\s\'"]+\.m3u8', html)
    if m:
        return m.group(0)
    return ""


def get_matches(domain):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    r = requests.get(domain, headers=headers, timeout=10)
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    maclar = []

    for item in soup.select("a.channel-item"):
        name = item.select_one(".channel-name")
        status = item.select_one(".channel-status")
        live = True if item.select_one(".live-badge") else False
        href = item.get("href", "")

        # PHP id çek
        m = re.search(r"id=([^&]+)", href)
        kanal_id = m.group(1).replace("yayin", "").strip() if m else ""

        # Gerçek kanal sayfası linki
        kanal_page = trgoals_ref + "/" + href.lstrip("/")

        # Gerçek m3u8 linki
        m3u8_link = get_channel_m3u8(kanal_page)

        maclar.append({
            "saat": status.get_text(strip=True) if status else "",
            "takimlar": name.get_text(strip=True) if name else "",
            "canli": live,
            "dosya": m3u8_link,  # artık dosya değil direkt m3u8 linki
            "kanal_adi": (status.get_text(strip=True) + " - " + name.get_text(strip=True)).strip(),
            "tvg_id": kanal_id
        })

    return maclar


def create_m3u(maclar):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for kanal in maclar:
            f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" group-title="TrGoals",{kanal["kanal_adi"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={trgoals_ref}\n')
            f.write(kanal["dosya"] + "\n")  # artık direkt gerçek m3u8 linki

    print(f"✔ M3U dosyası oluşturuldu: {OUTPUT_FILE}")


# --- ÇALIŞTIR ---
try:
    print("Güncel domain alınıyor...")
    domain = get_active_domain()
    print("Kullanılan domain:", domain)

    print(f"{GREEN}[✓] TrGoals domain: {trgoals_ref}{RESET}")
    print("Maçlar çekiliyor...")
    maclar = get_matches(domain)
    print(f"{len(maclar)} maç bulundu.")

    print("M3U oluşturuluyor...")
    create_m3u(maclar)

except Exception as e:
    print("Hata:", e)
