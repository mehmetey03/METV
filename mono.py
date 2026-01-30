import requests
import re
import urllib3

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "*/*",
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

# --------------------------------------------------

def get_active_domain():
    print("🔍 Aktif MonoTV domain aranıyor...")
    for i in range(520, 560):
        url = f"https://monotv{i}.com"
        try:
            r = requests.get(url, timeout=5, verify=False, headers=HEADERS)
            if r.status_code == 200:
                print(f"✅ Aktif domain: {url}")
                return url
        except:
            pass
    return None

# --------------------------------------------------

def detect_base_from_player(domain, test_id="zirve"):
    print("🎯 Player üzerinden CDN yakalanıyor...")

    player_url = f"{domain}/player?id={test_id}"

    try:
        r = requests.get(
            player_url,
            headers={**HEADERS, "Referer": domain},
            timeout=10,
            verify=False
        )
    except:
        return None

    # m3u8 direkt varsa
    m = re.search(r'(https?://[^"\']+?/[^"\']+?/mono\.m3u8)', r.text)
    if m:
        full = m.group(1)
        base = full.split(f"/{test_id}/")[0] + "/"
        print(f"✅ CDN bulundu: {base}")
        return base

    # alternatif: herhangi m3u8
    m = re.search(r'(https?://[^"\']+\.m3u8)', r.text)
    if m:
        url = m.group(1)
        base = url.rsplit("/", 2)[0] + "/"
        print(f"✅ CDN bulundu (GENEL): {base}")
        return base

    return None

# --------------------------------------------------

def check_stream(url, referer):
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Referer": referer
            },
            timeout=6,
            verify=False
        )
        return r.status_code == 200 and "#EXTM3U" in r.text
    except:
        return False

# --------------------------------------------------

def main():
    domain = get_active_domain()
    if not domain:
        print("❌ Domain bulunamadı")
        return

    base_url = detect_base_from_player(domain)
    if not base_url:
        print("❌ CDN bulunamadı → MonoTV stream gizli")
        return

    m3u = ["#EXTM3U"]
    ok = 0

    print("\n📡 Kanallar kontrol ediliyor...\n")

    for cid, name in CHANNELS.items():
        stream = f"{base_url}{cid}/mono.m3u8"
        print(f"🔍 {name}")

        if check_stream(stream, domain):
            ok += 1
            m3u.append(f'#EXTINF:-1,{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={domain}')
            m3u.append(stream)
            print("✅ ÇALIŞIYOR")
        else:
            print("❌ ÇALIŞMIYOR")

    with open("mono.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))

    print("\n🎯 TAMAMLANDI")
    print(f"✔ Çalışan yayın: {ok}")
    print("✔ Dosya: mono.m3u")

# --------------------------------------------------

if __name__ == "__main__":
    main()
