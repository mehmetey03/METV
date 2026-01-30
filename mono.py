import requests
import itertools
import urllib3

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*"
}

CHANNELS = {
    "zirve": "beIN Sports 1 A",
    "trgoals": "beIN Sports 1 B",
    "yayin1": "beIN Sports 1 C",
    "b2": "beIN Sports 2",
    "b3": "beIN Sports 3",
    "b4": "beIN Sports 4",
    "b5": "beIN Sports 5",
    "ss1": "S Sports 1",
    "ss2": "S Sports 2",
    "t1": "Tivibu Sports 1",
    "t2": "Tivibu Sports 2",
    "trt1": "TRT 1",
    "atv": "ATV"
}

# -------------------------------------------------

def get_active_domain():
    print("🔍 Aktif MonoTV domain aranıyor...")
    for i in range(520, 560):
        url = f"https://monotv{i}.com"
        try:
            r = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            if r.status_code == 200:
                print(f"✅ Aktif domain: {url}")
                return url
        except:
            pass
    return None

# -------------------------------------------------

def discover_cdn(test_id="zirve"):
    print("🌐 CDN pattern brute başlatıldı...")

    subs = ["tv", "cdn", "live", "edge", "stream"]
    names = ["zirve", "mono", "monospo", "spor", "live"]
    tlds = ["com", "net", "xyz", "cfd", "tv"]

    for s, n, t in itertools.product(subs, names, tlds):
        base = f"https://{s}.{n}.{t}/"
        test_url = f"{base}{test_id}/mono.m3u8"

        try:
            r = requests.get(
                test_url,
                headers=HEADERS,
                timeout=5,
                verify=False
            )
            if r.status_code == 200 and "#EXTM3U" in r.text:
                print(f"✅ CDN BULUNDU: {base}")
                return base
        except:
            pass

    return None

# -------------------------------------------------

def main():
    domain = get_active_domain()
    if not domain:
        print("❌ Domain bulunamadı")
        return

    base_url = discover_cdn()
    if not base_url:
        print("❌ CDN bulunamadı (JS runtime gerekiyor)")
        return

    m3u = ["#EXTM3U"]
    ok = 0

    print("\n📡 Kanallar yazılıyor...\n")

    for cid, name in CHANNELS.items():
        url = f"{base_url}{cid}/mono.m3u8"
        m3u.append(f'#EXTINF:-1,{name}')
        m3u.append(f'#EXTVLCOPT:http-referrer={domain}')
        m3u.append(url)
        ok += 1

    with open("mono.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))

    print("\n🎯 TAMAMLANDI")
    print(f"✔ Kanal sayısı: {ok}")
    print("✔ Dosya: mono.m3u")

# -------------------------------------------------

if __name__ == "__main__":
    main()
