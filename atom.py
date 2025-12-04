import requests
import re

START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36'
}

# -------------------------
# 1) GERÇEK DOMAINİ BULMA
# -------------------------
def follow_redirects(url):
    try:
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        if "location" in r.headers:
            loc = r.headers["location"]
            r2 = requests.get(loc, headers=headers, allow_redirects=False, timeout=10)
            if "location" in r2.headers:
                return r2.headers["location"].rstrip("/")
        return "https://atomsportv480.top"
    except:
        return "https://atomsportv480.top"

# -------------------------
# 2) TÜM KANAL ID’LERİNİ BULMA
# -------------------------
def get_all_ids(base):
    print(f"Kanal listesi alınıyor: {base}")

    r = requests.get(base, headers=headers, timeout=10)
    html = r.text

    ids = re.findall(r"matches\?id=([^\"\'\s&]+)", html)

    ids = list(set(ids))  # benzersiz yap

    print(f"Toplam {len(ids)} kanal bulundu.")
    return ids

# -------------------------
# 3) HER KANALIN GERÇEK M3U8 LİNKİNİ ÇEKME
# -------------------------
def get_real_link(base, cid):
    try:
        match_url = f"{base}/matches?id={cid}"
        r = requests.get(match_url, headers=headers, timeout=10)
        html = r.text

        fetch = re.search(r'fetch\("(.*?)"', html)
        if not fetch:
            return None

        fetch_url = fetch.group(1)
        if not fetch_url.endswith(cid):
            fetch_url += cid

        custom = headers.copy()
        custom["Origin"] = base
        custom["Referer"] = match_url

        r2 = requests.get(fetch_url, headers=custom, timeout=10)

        m = re.search(r'"deismackanal":"(.*?)"', r2.text)
        if not m:
            return None

        url = m.group(1).replace("\\", "")
        return url

    except:
        return None

# -------------------------
# 4) M3U OLUŞTURMA
# -------------------------
def create_m3u(channels):
    print("M3U oluşturuluyor...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in channels:
            cid = ch["id"]
            name = ch["name"]
            url = ch["url"]

            f.write(f'#EXTINF:-1 tvg-id="{cid}",{name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={ch["referer"]}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(url + "\n")

    print(f"[✓] {OUTPUT_FILE} oluşturuldu ({len(channels)} kanal).")

# -------------------------
# 5) ÇALIŞTIRMA
# -------------------------
def main():
    print("AtomSporTV — Tüm kanallar çekiliyor...\n")

    domain = follow_redirects(START_URL)
    print("Aktif domain:", domain)

    ids = get_all_ids(domain)

    final = []

    for cid in ids:
        print("→", cid)
        url = get_real_link(domain, cid)
        if url:
            final.append({
                "id": cid,
                "name": cid.replace("-", " ").title(),
                "url": url,
                "referer": domain
            })
            print("   ✔ M3U8 bulundu")
        else:
            print("   ✗ M3U8 yok (atlanıyor)")

    create_m3u(final)

    print("\nBiten toplam kanal:", len(final))

if __name__ == "__main__":
    main()
