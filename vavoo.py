import requests
import re

URL = "https://vavoo.to/channels"
PROXY_BASE = "https://vettelchannelowner-vettel-channel.hf.space/proxy/m3u?url=https://vavoo.to/play/{}/index.m3u8"
LOGO_URL = "https://raw.githubusercontent.com/kerimmkirac/CanliTvListe/refs/heads/main/vavoo.png"
OUTPUT_FILE = "vavoo.m3u"

TURKISH_CHAR_MAP = str.maketrans({
    'ç': 'c', 'Ç': 'C',
    'ğ': 'g', 'Ğ': 'G',
    'ı': 'i', 'İ': 'I',
    'ö': 'o', 'Ö': 'O',
    'ş': 's', 'Ş': 'S',
    'ü': 'u', 'Ü': 'U'
})

NAME_CORRECTIONS = {
    "S NEMA": "SİNEMA",
    "T RK": "TÜRK",
    "M Z K": "MÜZİK",
    "A LE": "AİLE",
    "AKS YON": "AKSİYON",
    "KOMED": "KOMEDİ",
    "YERL": "YERLİ",
    "KURD": "KURDİ",
    "OCUK": "ÇOÇUK",
    "CAY": "ÇAY",
    "D Ğ N": "DOĞAN",
    "VINC": "VINCI",
    "KOMEDİI": "KOMEDİ",
}

def normalize_tvg_id(name):
    name_ascii = name.translate(TURKISH_CHAR_MAP)
    return re.sub(r'\W+', '_', name_ascii.strip()).upper()

def fix_channel_name(name):
    for wrong, correct in NAME_CORRECTIONS.items():
        name = re.sub(wrong, correct, name, flags=re.IGNORECASE)
    return name.strip()

def fetch_turkey_channels():
    response = requests.get(URL)
    if response.status_code != 200:
        print("Hata: Kanal listesi alınamadı.")
        return []

    channels = response.json()
    turkey_channels = [ch for ch in channels if ch.get("country") == "Turkey"]

    for ch in turkey_channels:
        ch["name"] = fix_channel_name(ch.get("name", ""))

    def sort_key(ch):
        name = ch.get("name", "")
        name_ascii = name.translate(TURKISH_CHAR_MAP).lower()

        if "bein sports" in name_ascii:
            priority = 0
        elif "spor" in name_ascii:
            priority = 1
        else:
            priority = 2

        return (priority, name_ascii)

    return sorted(turkey_channels, key=sort_key)

def generate_m3u(channels):
    
    spor_channels = [ch for ch in channels if "spor" in ch.get("name", "").lower()]
    genel_channels = [ch for ch in channels if "spor" not in ch.get("name", "").lower()]

    spor_count = len(spor_channels)
    genel_count = len(genel_channels)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in channels:
            name = ch.get("name", "Unknown").strip()
            tvg_id = normalize_tvg_id(name)
            proxy_url = PROXY_BASE.format(ch.get("id"))

            
            if "spor" in name.lower():
                group_title = f"Spor ({spor_count})"
            else:
                group_title = f"Genel Kanallar ({genel_count})"

            f.write(
                f'#EXTINF:-1 tvg-name="{name}" tvg-language="Türkçe" '
                f'tvg-country="Türkiye" tvg-id="{tvg_id}" tvg-logo="{LOGO_URL}" '
                f'group-title="{group_title}",{name}\n{proxy_url}\n'
            )

    print(f"{len(channels)} Tane kanal bulundu → '{OUTPUT_FILE}' dosyasına yazıldı.")

if __name__ == "__main__":
    turkey_channels = fetch_turkey_channels()
    generate_m3u(turkey_channels)
