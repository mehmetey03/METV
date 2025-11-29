import requests
from bs4 import BeautifulSoup
import re

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/goal/refs/heads/main/domain.txt"
OUTPUT_FILE = "trgoalss.m3u"

trgoals_ref = "https://trgoals1472.xyz"  # Örnek referrer

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def get_active_domain():
    r = requests.get(DOMAIN_TXT_URL, timeout=10)
    r.raise_for_status()
    m = re.search(r"guncel_domain\s*=\s*(https?://[^\s]+)", r.text)
    if not m:
        raise Exception("guncel_domain bulunamadı!")
    return m.group(1).strip()


def get_matches(domain):
    """ Kanal listesi çek """
    r = requests.get(domain, headers=HEADERS, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    maclar = []

    for item in soup.select("a.channel-item"):
        name = item.select_one(".channel-name")
        status = item.select_one(".channel-status")
        href = item.get("href", "")
        m = re.search(r"id=([^&]+)", href)
        kanal_id = m.group(1).replace("yayin", "").strip() if m else ""

        maclar.append({
            "kanal_adi": (status.get_text(strip=True) + " - " + name.get_text(strip=True)).strip(),
            "source_id": kanal_id
        })
    return maclar


def extract_base_url(html):
    """ Sayfa içinden gerçek yayın base URL al """
    m = re.search(r'https?://[^\s"]+\.m3u8', html)
    if m:
        url = m.group(0)
        base = "/".join(url.split("/")[:-1]) + "/"  # Dosya adını çıkar
        return base
    return None


def fetch_streams(domain, channels):
    """ Her kanalın gerçek linkini al """
    streams = []
    for ch in channels:
        full_url = f"{domain}/index.php?id={ch['source_id']}"
        try:
            r = requests.get(full_url, headers={**HEADERS, "Referer": trgoals_ref}, timeout=6)
            if r.status_code == 200:
                base = extract_base_url(r.text)
                if base:
                    # Örnek: base + "yayin1.m3u8" gibi
                    stream = f"{base}yayin{ch['source_id']}.m3u8"
                    ch["stream"] = stream
                    streams.append(ch)
        except Exception:
            continue
    return streams


def create_m3u(channels):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for kanal in channels:
            f.write(f'#EXTINF:-1 tvg-id="{kanal["source_id"]}.tr" group-title="TrGoals",{kanal["kanal_adi"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={trgoals_ref}/\n')
            f.write(f'{kanal["stream"]}\n')
    print(f"✔ M3U dosyası oluşturuldu: {OUTPUT_FILE}")


# --- ÇALIŞTIR ---
if __name__ == "__main__":
    try:
        domain = get_active_domain()
        print("Domain:", domain)
        channels = get_matches(domain)
        print(f"{len(channels)} kanal bulundu.")
        full_list = fetch_streams(domain, channels)
        print(f"{len(full_list)} geçerli stream bulundu.")
        create_m3u(full_list)
    except Exception as e:
        print("Hata:", e)
