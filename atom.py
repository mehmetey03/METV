import requests
import re
import json

START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36",
    "Referer": "https://url24.link/",
    "Accept": "*/*"
}


# -------------------------------------------------------
# 1) Aktif AtomSpor domain bulma
# -------------------------------------------------------
def get_base_domain():
    try:
        r1 = requests.get(START_URL, headers=headers, allow_redirects=False, timeout=10)
        loc1 = r1.headers.get("location")

        if not loc1:
            return "https://www.atomsportv480.top"

        r2 = requests.get(loc1, headers=headers, allow_redirects=False, timeout=10)
        loc2 = r2.headers.get("location")

        if loc2:
            return loc2.rstrip("/")

        return "https://www.atomsportv480.top"

    except:
        return "https://www.atomsportv480.top"


# -------------------------------------------------------
# 2) Tüm kanal ID’lerini toplama
# -------------------------------------------------------
def get_all_channel_ids(base):
    print("\nKanal ID'leri alınıyor...")

    r = requests.get(base, headers=headers)
    html = r.text

    ids = re.findall(r"yayinlink\.php\?id=(\d+)", html)
    ids2 = re.findall(r"data-id=[\"'](\d+)[\"']", html)
    ids3 = re.findall(r"(\d+)\.m3u8", html)

    all_ids = list(set(ids + ids2 + ids3))

    print(f"Toplam {len(all_ids)} ID bulundu.")
    return all_ids


# -------------------------------------------------------
# 3) ID → yayınlink.php → gerçek .m3u8 alma
# -------------------------------------------------------
def get_m3u8_from_yayinlink(channel_id):
    try:
        url = f"https://analyticsjs.sbs/load/yayinlink.php?id={channel_id}"
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text

        # JSON → { "link": "https://......m3u8" }
        try:
            js = json.loads(text)
            if "link" in js:
                return js["link"]
        except:
            pass

        # fallback regex
        m = re.search(r'(https?://[^\s"]+\.m3u8[^\s"]*)', text)
        if m:
            return m.group(1)

    except:
        pass

    return None


# -------------------------------------------------------
# 4) fetch(...) → deismackanal → m3u8 alma
# -------------------------------------------------------
def get_m3u8_by_fetch(channel_id, base):
    try:
        matches_url = f"{base}/matches?id={channel_id}"
        response = requests.get(matches_url, headers=headers, timeout=10)
        html = response.text

        fetch_match = re.search(r'fetch\(["\'](.*?)["\']', html)
        if not fetch_match:
            return None

        fetch_url = fetch_match.group(1)
        if not fetch_url.endswith(channel_id):
            fetch_url += channel_id

        custom_headers = headers.copy()
        custom_headers['Origin'] = base
        custom_headers['Referer'] = base

        r2 = requests.get(fetch_url, headers=custom_headers, timeout=10)
        text = r2.text

        # yeni API
        m1 = re.search(r'"deismackanal":"(.*?)"', text)
        if m1:
            return m1.group(1).replace("\\", "")

        # eski API
        m2 = re.search(r'"(?:stream|url|source)":\s*"(.*?\.m3u8)"', text)
        if m2:
            return m2.group(1).replace("\\", "")

    except:
        return None

    return None


# -------------------------------------------------------
# 5) Bir kanalı çözme (en güçlü yöntem)
# -------------------------------------------------------
def get_channel_m3u8(channel_id, base):
    # 1. fetch yöntemi
    m3u8 = get_m3u8_by_fetch(channel_id, base)

    # 2. yayınlink yöntemi
    if not m3u8:
        m3u8 = get_m3u8_from_yayinlink(channel_id)

    return m3u8


# -------------------------------------------------------
# 6) M3U yazma
# -------------------------------------------------------
def create_m3u(base, channels):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for cid in channels:
            print(f"→ {cid} işleniyor...", end=" ")

            m3u8_real = get_channel_m3u8(cid, base)

            if not m3u8_real:
                print("✗")
                continue

            print("✓")

            f.write(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{cid}" group-title="Diğer",{cid}\n')
            f.write(f"#EXTVLCOPT:http-referrer={base}\n")
            f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
            f.write(m3u8_real + "\n")

    print("\nM3U Hazır →", OUTPUT_FILE)


# -------------------------------------------------------
# 7) MAIN
# -------------------------------------------------------
def main():
    print("AtomSporTV — Tüm kanallar çekiliyor...\n")

    base = get_base_domain()
    print("Aktif domain:", base)

    ids = get_all_channel_ids(base)
    create_m3u(base, ids)

    print("\nToplam kanal:", len(ids))


if __name__ == "__main__":
    main()
