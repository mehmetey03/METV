import requests
import re
import json

START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"

headers = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Referer": "https://url24.link/",
}

def get_base_domain():
    try:
        r = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        loc1 = r.headers.get("location")
        if not loc1:
            return "https://www.atomsportv480.top"

        r2 = requests.get(loc1, headers=headers, allow_redirects=False, timeout=10)
        loc2 = r2.headers.get("location")

        if loc2:
            return loc2.rstrip("/")

    except:
        pass

    return "https://www.atomsportv480.top"


def extract_channel_ids(domain):
    print("\nKanal listesi alınıyor:", domain)

    r = requests.get(domain, headers=headers, timeout=10)
    html = r.text

    ids = re.findall(r"matches\?id=([0-9]+)", html)
    ids = list(set(ids))

    print(f"Toplam {len(ids)} kanal bulundu.")
    return ids


def get_real_m3u8(channel_id):
    api_url = f"https://analyticsjs.sbs/load/yayinlink.php?id={channel_id}"

    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        data = json.loads(r.text)

        if "url" in data:
            return data["url"]

        # Bazı varyantlarda başka isim olabilir
        if "stream" in data:
            return data["stream"]

    except:
        return None

    return None


def create_m3u(base_domain, channels):
    print("\nM3U oluşturuluyor...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in channels:
            cid = ch["id"]
            url = ch["url"]

            f.write(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{cid}" group-title="Diğer",{cid}\n')
            f.write(f"#EXTVLCOPT:http-referrer={base_domain}\n")
            f.write(f"#EXTVLCOPT:http-user-agent={UA}\n")
            f.write(url + "\n")

    print(f"\n[✓] {OUTPUT_FILE} oluşturuldu ({len(channels)} kanal).")


def main():
    print("AtomSporTV — Tüm kanallar çekiliyor...")

    base = get_base_domain()
    print("Aktif domain:", base)

    ids = extract_channel_ids(base)
    working = []

    for cid in ids:
        print(f"→ {cid}")
        m3u8 = get_real_m3u8(cid)

        if m3u8:
            print("   ✔ M3U8 bulundu")
            working.append({
                "id": cid,
                "url": m3u8
            })
        else:
            print("   ✗ Bulunamadı")

    create_m3u(base, working)

    print("\nBiten toplam kanal:", len(working))


if __name__ == "__main__":
    main()
