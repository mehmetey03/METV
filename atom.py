import requests
import re
import json

START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'tr-TR,tr;q=0.8',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36'
}

def follow_redirects(url):
    try:
        r = requests.get(url, headers=headers, allow_redirects=False, timeout=10)
        if "location" not in r.headers:
            return "https://atomsportv480.top"

        loc1 = r.headers["location"]
        r2 = requests.get(loc1, headers=headers, allow_redirects=False, timeout=10)

        if "location" in r2.headers:
            domain = r2.headers["location"].rstrip("/")
            return domain

        return "https://atomsportv480.top"
    except:
        return "https://atomsportv480.top"

def extract_fetch_urls(html):
    """ fetch("URL") ile çağrılan tüm API linklerini bul """
    urls = re.findall(r'fetch\(["\'](.*?)["\']', html)
    clean_urls = []

    for u in urls:
        u = u.strip()
        if u.startswith("//"):   # //api şeklinde olabilir
            u = "https:" + u
        clean_urls.append(u)

    return list(set(clean_urls))

def get_all_matches(base):
    print(f"\nBase: {base}")
    main_page = requests.get(base, headers=headers, timeout=10).text

    fetch_urls = extract_fetch_urls(main_page)

    print(f"Bulunan fetch API sayısı: {len(fetch_urls)}")

    all_channels = []

    for api in fetch_urls:
        try:
            if not api.startswith("http"):
                api = base + api

            # ID ekleniyorsa ID'yi sondan ekleme
            if "?id=" not in api:
                continue

            print(f"→ API: {api}")

            resp = requests.get(api, headers=headers, timeout=10).text

            # JSON olan API’ler
            try:
                data = json.loads(resp)
            except:
                continue

            if "deismackanal" in resp:
                # Tek kanal dönen API
                url = data.get("deismackanal", "").replace("\\", "")
                cid = api.split("=")[-1]

                all_channels.append({
                    "id": cid,
                    "name": cid.replace("-", " ").title(),
                    "group": "Spor",
                    "url": url,
                    "referer": base
                })

            # Liste dönen API
            if "data" in data:
                for item in data["data"]:
                    cid = item.get("id")
                    url = item.get("url", "").replace("\\", "")
                    name = item.get("name", cid)
                    group = item.get("kategori", "Spor")

                    if cid and url:
                        all_channels.append({
                            "id": cid,
                            "name": name,
                            "group": group,
                            "url": url,
                            "referer": base
                        })

        except Exception as e:
            print(f"API hata: {e}")

    # tekrarları kaldır
    uniq = {}
    for ch in all_channels:
        uniq[ch["id"]] = ch

    return list(uniq.values())

def create_m3u(channels):
    print(f"\nM3U oluşturuluyor... ({len(channels)} kanal)")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in channels:
            f.write(
                f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}\n'
            )
            f.write(f'#EXTVLCOPT:http-referrer={ch["referer"]}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}\n')
            f.write(ch["url"] + "\n")

    print(f"[✓] {OUTPUT_FILE} oluşturuldu.")

def main():
    print("AtomSporTV — Tüm kanallar çekiliyor...\n")

    base = follow_redirects(START_URL)
    print("Aktif domain:", base)

    channels = get_all_matches(base)

    print("\nToplam bulunan kanal:", len(channels))

    create_m3u(channels)

if __name__ == "__main__":
    main()
