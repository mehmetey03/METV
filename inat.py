import requests
from bs4 import BeautifulSoup
import re
import html
import unicodedata

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/inatdom/refs/heads/main/domain.txt"
OUTPUT_FILE = "inat.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

# -------------------- Yardımcı Fonksiyon --------------------
def clean_text(text):
    """Metni düzgün Türkçe karakterlerle düzeltir"""
    if not text:
        return ""
    text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    return text

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

def get_channel_m3u8(domain, channel_id):
    """PHP mantığını kullanarak m3u8 linkini al"""
    try:
        base_page_url = f"{domain}/channel.html?id=yayinzirve"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        r = requests.get(base_page_url, headers=headers, timeout=10)
        r.encoding = r.apparent_encoding  # <- encoding düzeltildi
        html_text = r.text

        m = re.search(r'baseurl\s*=\s*"(.*?)"', html_text)
        if not m:
            return ""
        baseurl = m.group(1).strip()
        return f"{baseurl}{channel_id}.m3u8"

    except Exception as e:
        print("get_channel_m3u8 hatası:", e)
        return ""

def get_matches(domain):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        r = requests.get(domain, headers=headers, timeout=10)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        maclar = []

        for item in soup.select("a.channel-item"):
            name_el = item.select_one(".channel-name")
            status_el = item.select_one(".channel-status")
            live = True if item.select_one(".live-badge") else False
            href = item.get("href", "")

            m = re.search(r"id=([^&]+)", href)
            kanal_id = m.group(1).strip() if m else ""
            if not kanal_id:
                continue

            m3u8_link = get_channel_m3u8(domain, kanal_id)
            if not m3u8_link:
                continue

            maclar.append({
                "saat": clean_text(status_el.get_text(strip=True)) if status_el else "",
                "takimlar": clean_text(name_el.get_text(strip=True)) if name_el else "",
                "canli": live,
                "dosya": m3u8_link,
                "kanal_adi": (clean_text(status_el.get_text(strip=True)) + " - " + clean_text(name_el.get_text(strip=True))).strip(),
                "tvg_id": kanal_id
            })

        return maclar

    except Exception as e:
        print("get_matches hatası:", e)
        return []

def create_m3u(maclar, domain):
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:  # <- UTF-8 BOM eklendi
        f.write("#EXTM3U\n")
        for kanal in maclar:
            f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" group-title="İnat",{kanal["kanal_adi"]}\n')
            f.write(f'#EXTVLCOPT:http-referrer={domain}\n')
            f.write(kanal["dosya"] + "\n")
    print(f"✔ M3U dosyası oluşturuldu: {OUTPUT_FILE}")

# -------------------- ÇALIŞTIR --------------------
try:
    print("Güncel domain alınıyor...")
    domain = get_active_domain()
    print(f"{GREEN}[✓] Kullanılan domain: {domain}{RESET}")

    print("Maçlar çekiliyor...")
    maclar = get_matches(domain)
    print(f"{len(maclar)} geçerli maç bulundu.")

    if maclar:
        print("M3U oluşturuluyor...")
        create_m3u(maclar, domain)
    else:
        print("Maç bulunamadı, M3U oluşturulmadı.")

except Exception as e:
    print("Hata:", e)
