import requests
from bs4 import BeautifulSoup
import re

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/goal/refs/heads/main/domain.txt"
OUTPUT_FILE = "trgoalss.m3u"

# --- RENKLER (optional) ---
GREEN = "\033[92m"
RESET = "\033[0m"

# --- TRGOALS M3U Ayarları ---
trgoals_ref = "https://www.trgoals.com"
trgoals_base = "https://www.trgoals.com/yayin/"  # default fallback


def get_active_domain():
    """ GitHub domain.txt → guncel_domain çek """
    r = requests.get(DOMAIN_TXT_URL, timeout=10)
    if r.status_code != 200:
        raise Exception("domain.txt okunamadı!")

    txt = r.text
    m = re.search(r"guncel_domain\s*=\s*(https?://[^\s]+)", txt)
    if not m:
        raise Exception("guncel_domain bulunamadı!")

    return m.group(1).strip()


def find_baseurl(channel_url):
    """ Örnek channel sayfasından base URL çıkar """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    r = requests.get(channel_url, headers=headers, timeout=10)
    if r.status_code != 200:
        return ""

    html = r.text
    # Base URL genellikle JS içinde veya m3u8 path’inde geçer
    m = re.search(r'(https?://[^\s\'"]+\.m3u8)', html)
    if m:
        base_url = "/".join(m.group(1).split("/")[:-1]) + "/"  # sadece klasör kısmını al
        return base_url
    return ""


def get_matches(domain):
    """ Güncel domain → maçları al """
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

        # PHP'deki id=xxxxx çekme
        m = re.search(r"id=([^&]+)", href)
        raw_id = m.group(1) if m else ""

        # 'yayin' temizle
        kanal_id = raw_id.replace("yayin", "").strip()

        maclar.append({
            "saat": status.get_text(strip=True) if status else "",
            "takimlar": name.get_text(strip=True) if name else "",
            "canli": live,
            "dosya": kanal_id,
            "kanal_adi": (status.get_text(strip=True) + " - " + name.get_text(strip=True)).strip(),
            "tvg_id": kanal_id
        })

    return maclar


def create_m3u(maclar):
    """ trgoalss.m3u oluşturma """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for kanal in maclar:
            f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" group-title="TrGoals",{kanal["kanal_adi"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={trgoals_ref}\n')
            f.write(trgoals_base + kanal["dosya"] + ".m3u8\n")

    print(f"✔ M3U dosyası oluşturuldu: {OUTPUT_FILE}")


# --- ÇALIŞTIR ---
try:
    print("Güncel domain alınıyor...")
    domain = get_active_domain()
    print("Kullanılan domain:", domain)

    # Base URL dinamik olarak al
    if trgoals_ref:
        print(f"{GREEN}[✓] TrGoals domain: {trgoals_ref}{RESET}")
        base_found = find_baseurl(trgoals_ref + "/channel.html?id=yayinzirve")
        if base_found:
            trgoals_base = base_found
            print(f"{GREEN}[✓] TrGoals base URL bulundu: {trgoals_base}{RESET}")
        else:
            print("[!] Base URL bulunamadı, default kullanılıyor:", trgoals_base)

    print("Maçlar çekiliyor...")
    maclar = get_matches(domain)
    print(f"{len(maclar)} maç bulundu.")

    print("M3U oluşturuluyor...")
    create_m3u(maclar)

except Exception as e:
    print("Hata:", e)
