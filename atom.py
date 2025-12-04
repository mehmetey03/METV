import requests
import re
import sys

BASE_CHECK = "https://url24.link/AtomSporTV"
FALLBACK = "https://www.atomsportv480.top"
OUTPUT = "atom.m3u"

UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"

headers = {
    "User-Agent": UA,
    "Accept": "*/*",
    "Referer": "https://url24.link/"
}

GREEN = "\033[92m"
RESET = "\033[0m"


def get_domain():
    """url24.link üzerinden gerçek domain bulur"""
    try:
        r = requests.get(BASE_CHECK, headers=headers, allow_redirects=False, timeout=10)
        if "location" not in r.headers:
            return FALLBACK

        loc1 = r.headers["location"]
        r2 = requests.get(loc1, headers=headers, allow_redirects=False, timeout=10)

        if "location" in r2.headers:
            final = r2.headers["location"].strip().rstrip("/")
            print(f"Aktif domain: {final}")
            return final

        return FALLBACK

    except:
        return FALLBACK


def get_all_ids(domain):
    """Ana sayfadan tüm kanal ID'lerini toplar"""
    print(f"\nKanal listesi çekiliyor: {domain}")

    try:
        html = requests.get(domain, headers={"User-Agent": UA}, timeout=10).text
    except:
        print("❌ Ana sayfa okunamadı")
        return []

    # tüm matches?id=X tiplerini yakala
    ids = re.findall(r'matches\?id=([a-zA-Z0-9\-\_]+)', html)

    ids = list(set(ids))  # benzersiz yap

    print(f"Toplam {len(ids)} ID bulundu.\n")
    return ids


def get_m3u8(domain, cid):
    """Her kanal için, matches?id=XX → fetch → JSON → m3u8 çıkarır"""

    try:
        url = f"{domain}/matches?id={cid}"
        html = requests.get(url, headers={"User-Agent": UA}, timeout=10).text

        fetch_match = re.search(r'fetch\("(.*?)"', html)
        if not fetch_match:
            return None

        fetch_url = fetch_match.group(1)

        if not fetch_url.endswith(cid):
            fetch_url = fetch_url + cid

        r = requests.get(fetch_url, headers={"User-Agent": UA, "Referer": domain}, timeout=10)
        j = r.text

        m = re.search(r'"deismackanal":"(.*?)"', j)
        if m:
            return m.group(1).replace("\\", "")

        return None

    except:
        return None


def create_m3u(channels):
    f = open(OUTPUT, "w", encoding="utf-8")
    f.write("#EXTM3U\n")

    for name, url in channels:
        f.write(f'#EXTINF:-1 ,{name}\n')
        f.write(url + "\n")

    f.close()


def main():
    print("AtomSporTV — Tüm kanallar çekiliyor...\n")

    domain = get_domain()

    ids = get_all_ids(domain)

    if not ids:
        print("❌ Hiç kanal bulunamadı!")
        create_m3u([])
        return

    working = []

    for cid in ids:
        print(f"→ {cid}")

        m3u8 = get_m3u8(domain, cid)

        if m3u8:
            print(f"   {GREEN}✔ M3U8 bulundu{RESET}")
            working.append((cid, m3u8))
        else:
            print("   ✗ M3U8 bulunamadı")

    print("\nM3U oluşturuluyor...\n")
    create_m3u(working)

    print(f"[✓] {OUTPUT} oluşturuldu ({len(working)} kanal).\n")
    print(f"Biten toplam kanal: {len(working)}")


if __name__ == "__main__":
    main()
