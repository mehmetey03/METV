import requests
from bs4 import BeautifulSoup
import re

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/goal/refs/heads/main/domain.txt"
OUTPUT_FILE = "trgoalss.m3u"

trgoals_ref = "https://www.trgoals.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# === 1. domain.txt içinden aktif domain bul ===
def get_active_domain():
    r = requests.get(DOMAIN_TXT_URL, timeout=10)
    r.raise_for_status()
    m = re.search(r"guncel_domain\s*=\s*(https?://[^\s]+)", r.text)
    if not m:
        raise Exception("guncel_domain bulunamadı!")
    return m.group(1).strip()

# === 2. Maç listesi çek ===
def get_matches(domain):
    r = requests.get(domain, headers=HEADERS, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    matches = []
    for item in soup.select("a.channel-item"):
        name = item.select_one(".channel-name")
        status = item.select_one(".channel-status")
        href = item.get("href", "")

        m = re.search(r"id=([^&]+)", href)
        raw_id = m.group(1) if m else ""
        kanal_id = raw_id.replace("yayin", "").strip()

        matches.append({
            "kanal_adi": (status.get_text(strip=True) + " - " + name.get_text(strip=True)).strip(),
            "source_id": kanal_id
        })
    return matches

# === 3. Sayfa içinden gerçek base URL çıkar ===
def extract_base_url(html):
    """
    Örnek: 'https:\/\/savatv16.com\/705\/mono.m3u8' → https://savatv16.com/
    """
    m = re.search(r'https:\\/\\/(.*?)(?:\\/[\d]+\\/mono\.m3u8)', html)
    if not m:
        return None
    return f"https://{m.group(1)}/"

# === 4. Her kanalın gerçek stream linkini bul ===
def fetch_sporcafe_streams(domain, referer, channels):
    result = []
    for ch in channels:
        full_url = f"{domain}/index.php?id={ch['source_id']}"
        try:
            r = requests.get(full_url, headers={**HEADERS, "Referer": referer}, timeout=6)
            if r.status_code == 200:
                base = extract_base_url(r.text)
                if base:
                    stream = f"{base}{ch['source_id']}/playlist.m3u8"
                    ch["stream"] = stream
                    result.append(ch)
        except Exception:
            continue
    return result

# === 5. M3U dosyasını oluştur ===
def create_m3u(channels):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for kanal in channels:
            f.write(f'#EXTINF:-1 tvg-id="{kanal["source_id"]}" group-title="TrGoals",{kanal["kanal_adi"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={trgoals_ref}\n')
            f.write(f'{kanal["stream"]}\n')
    print(f"✔ trgoalss.m3u oluşturuldu ({len(channels)} kanal)")

# === 6. Ana akış ===
if __name__ == "__main__":
    try:
        print("🔍 Güncel domain alınıyor...")
        domain = get_active_domain()
        print("🌍 Domain:", domain)

        print("📡 Kanal listesi çekiliyor...")
        channels = get_matches(domain)
        print(f"{len(channels)} kanal bulundu.")

        print("🎯 Gerçek yayın linkleri alınıyor...")
        full_list = fetch_sporcafe_streams(domain, trgoals_ref, channels)
        print(f"{len(full_list)} geçerli yayın bulundu.")

        print("💾 M3U dosyası yazılıyor...")
        create_m3u(full_list)

    except Exception as e:
        print("❌ Hata:", e)
