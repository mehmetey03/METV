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
# 1) Aktif domain bul
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
# 2) Tüm kanalları resmi API'den çek
# -------------------------------------------------------
def get_channel_list(base):
    url = base + "/home/channels.php"

    print("\nKanal listesi çekiliyor:", url)

    try:
        r = requests.get(url, headers=headers, timeout=10)
        js = json.loads(r.text)

        print(f"Toplam {len(js)} kanal bulundu.")
        return js

    except Exception as e:
        print("Kanal listesi okunamadı:", e)
        return []


# -------------------------------------------------------
# 3) yayınlink.php → ID → gerçek m3u8
# -------------------------------------------------------
def get_m3u8_from_yayinlink(channel_id):
    try:
        url = f"https://analyticsjs.sbs/load/yayinlink.php?id={channel_id}"
        r = requests.get(url, headers=headers, timeout=10)

        try:
            js = json.loads(r.text)
            if "link" in js:
                return js["link"]
        except:
            pass

        m = re.search(r'(https?://[^\s"]+\.m3u8[^\s"]*)', r.text)
        if m:
            return m.group(1)

    except:
        pass

    return None


# -------------------------------------------------------
# 4) fetch(...) → deismackanal → m3u8
# -------------------------------------------------------
def get_m3u8_by_fetch(channel_slug, base):
    try:
        page = f"{base}/{channel_slug}"
        r = requests.get(page, headers=headers, timeout=10)
        html = r.text

        fetch_match = re.search(r'fetch\(["\'](.*?)["\']', html)
        if not fetch_match:
            return None

        api = fetch_match.group(1)
        if api.startswith("/"):
            api = base + api

        r2 = requests.get(api, headers=headers, timeout=10)

        m1 = re.search(r'"deismackanal":"(.*?)"', r2.text)
        if m1:
            return m1.group(1).replace("\\", "")

        m2 = re.search(r'"(?:stream|url)":\s*"(.*?\.m3u8)"', r2.text)
        if m2:
            return m2.group(1).replace("\\", "")

    except:
        return None

    return None


# -------------------------------------------------------
# 5) kanal çözme
# -------------------------------------------------------
def resolve_channel(ch, base):
    cid = ch["id"]
    slug = ch["name"]

    # 1) fetch → maç + premium kanallar
    m3u8 = get_m3u8_by_fetch(slug, base)
    if m3u8:
        return m3u8

    # 2) ID → yayınlink → xmediaget
    m3u8 = get_m3u8_from_yayinlink(cid)
    if m3u8:
        return m3u8

    return None


# -------------------------------------------------------
# 6) M3U yaz
# -------------------------------------------------------
def create_m3u(base, channels):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in channels:
            cid = ch["id"]
            name = ch["name"]

            print(f"→ {name} ({cid}) çözülüyor...", end=" ")

            m3u8 = resolve_channel(ch, base)

            if not m3u8:
                print("✗")
                continue

            print("✓")

            f.write(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{name}" group-title="AtomSpor",{name}\n')
            f.write(f"#EXTVLCOPT:http-referrer={base}\n")
            f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
            f.write(m3u8 + "\n")

    print("\n[✓] M3U oluştı: atom.m3u")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    print("AtomSporTV — Tüm kanallar çekiliyor...\n")

    base = get_base_domain()
    print("Aktif domain:", base)

    channels = get_channel_list(base)

    create_m3u(base, channels)

    print("\nToplam kanal:", len(channels))


if __name__ == "__main__":
    main()
