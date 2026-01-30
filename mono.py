import requests
import re
import urllib3

urllib3.disable_warnings()

CHANNELS = {
    "zirve": "beIN Sports 1 A",
    "trgoals": "beIN Sports 1 B",
    "yayin1": "beIN Sports 1 C",
    "b2": "beIN Sports 2",
    "b3": "beIN Sports 3",
    "b4": "beIN Sports 4",
    "b5": "beIN Sports 5",
    "bm1": "beIN Sports 1 Max",
    "bm2": "beIN Sports 2 Max",
    "ss1": "S Sports 1",
    "ss2": "S Sports 2",
    "smarts": "Smart Sports",
    "sms2": "Smart Sports 2",
    "t1": "Tivibu Sports 1",
    "t2": "Tivibu Sports 2",
    "t3": "Tivibu Sports 3",
    "t4": "Tivibu Sports 4",
    "as": "A Spor",
    "trtspor": "TRT Spor",
    "trtspor2": "TRT Spor Yıldız",
    "trt1": "TRT 1",
    "atv": "ATV",
    "tv85": "TV8.5",
    "nbatv": "NBA TV",
    "eu1": "Euro Sport 1",
    "eu2": "Euro Sport 2",
    "ex1": "Tâbii 1",
    "ex2": "Tâbii 2",
    "ex3": "Tâbii 3",
    "ex4": "Tâbii 4",
    "ex5": "Tâbii 5",
    "ex6": "Tâbii 6",
    "ex7": "Tâbii 7",
    "ex8": "Tâbii 8"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# --------------------------------------------------

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

# --------------------------------------------------

def extract_js_urls(html, domain):
    js_files = re.findall(r'<script[^>]+src=["\'](.*?)["\']', html, re.I)
    full = []
    for js in js_files:
        if js.startswith("//"):
            full.append("https:" + js)
        elif js.startswith("/"):
            full.append(domain.rstrip("/") + js)
        elif js.startswith("http"):
            full.append(js)
    return full

# --------------------------------------------------

def detect_base_url(domain):
    print("🌐 CDN otomatik aranıyor (HTML + JS)...")

    try:
        r = requests.get(domain, headers=HEADERS, timeout=10, verify=False)
        html = r.text
    except:
        return None

    # 1️⃣ HTML içinde ara
    match = re.search(
        r'(https?://[a-z0-9.-]+\.[a-z]{2,6})/[^"\']+/mono\.m3u8',
        html,
        re.I
    )
    if match:
        base = match.group(1).rstrip("/") + "/"
        print(f"✅ CDN bulundu (HTML): {base}")
        return base

    # 2️⃣ JS dosyaları içinde ara
    for js_url in extract_js_urls(html, domain):
        try:
            js = requests.get(js_url, headers=HEADERS, timeout=6, verify=False).text
            match = re.search(
                r'(https?://[a-z0-9.-]+\.[a-z]{2,6})/[^"\']+/mono\.m3u8',
                js,
                re.I
            )
            if match:
                base = match.group(1).rstrip("/") + "/"
                print(f"✅ CDN bulundu (JS): {base}")
                return base
        except:
            continue

    print("❌ CDN bulunamadı (sitede yok)")
    return None

# --------------------------------------------------

def stream_alive(url, referer):
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Referer": referer
            },
            timeout=6,
            stream=True,
            verify=False
        )
        if r.status_code == 200:
            data = next(r.iter_content(2048), b"").decode(errors="ignore")
            return "#EXTM3U" in data
    except:
        pass
    return False

# --------------------------------------------------

def main():
    domain = get_active_domain()
    if not domain:
        print("❌ Domain bulunamadı")
        return

    base_url = detect_base_url(domain)
    if not base_url:
        print("❌ CDN bulunamadı → script durduruldu")
        return

    m3u = ["#EXTM3U"]
    working = 0

    print("\n📡 Kanallar test ediliyor...\n")

    for cid, name in CHANNELS.items():
        url = f"{base_url}{cid}/mono.m3u8"
        print(f"🔍 {name}")

        if stream_alive(url, base_url):
            working += 1
            m3u.append(f'#EXTINF:-1 group-title="Spor",{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={base_url}')
            m3u.append(url)
            print("✅ ÇALIŞIYOR")
        else:
            print("❌ ÇALIŞMIYOR")

    with open("mono.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))

    print("\n🎯 TAMAMLANDI")
    print(f"✔ Çalışan kanal: {working}")
    print("✔ mono.m3u oluşturuldu")

# --------------------------------------------------

if __name__ == "__main__":
    main()
