import requests
import re
import urllib3

urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Kanal ID → İsim eşlemesi
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
    "t1": "Tivibu Sports 1",
    "t2": "Tivibu Sports 2",
    "t3": "Tivibu Sports 3",
    "t4": "Tivibu Sports 4",
    "as": "A Spor",
    "trtspor": "TRT Spor",
    "trtspor2": "TRT Spor Yıldız",
    "trt1": "TRT 1",
    "atv": "ATV",
    "tv85": "TV8.5"
}

# --------------------------------------------------

def find_active_domain():
    print("🔍 Aktif MonoTV domain aranıyor...")
    for i in range(520, 570):
        url = f"https://monotv{i}.com"
        try:
            r = requests.get(url, headers=HEADERS, timeout=5, verify=False)
            if r.status_code == 200:
                print(f"✅ Aktif domain bulundu: {url}")
                return url
        except:
            pass
    print("❌ Domain bulunamadı")
    return None

# --------------------------------------------------

def get_base_url(domain):
    """
    domain üzerindeki domain.php veya 
    içeriğe gömülü baseurl'i çözmeye çalışır.
    """

    print("🌐 Base URL aranıyor...")

    # önce domain.php
    try:
        api_url = f"{domain}/domain.php"
        r = requests.get(api_url, headers=HEADERS, timeout=8, verify=False)
        data = r.json()
        base = data.get("baseurl")
        if base:
            print(f"✅ baseurl bulundu (domain.php): {base}")
            return base.rstrip("/") + "/"
    except:
        pass

    # sonra HTML + JS içinden regex
    try:
        r = requests.get(domain, headers=HEADERS, timeout=8, verify=False)
        html = r.text
        m = re.search(
            r'(https?://[a-z0-9.-]+\.[a-z]{2,6})/[a-z0-9/\-]+/mono\.m3u8',
            html,
            re.IGNORECASE
        )
        if m:
            base = m.group(1).rstrip("/") + "/"
            print(f"✅ baseurl bulundu (HTML): {base}")
            return base
    except:
        pass

    print("⚠️ baseurl bulunamadı")
    return None

# --------------------------------------------------

def test_stream(url, referer):
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Referer": referer
            },
            timeout=7,
            stream=True,
            verify=False
        )
        if r.status_code == 200:
            # ilk küçük kısmı kontrol et
            sample = next(r.iter_content(2048), b"").decode(errors="ignore")
            return "#EXTM3U" in sample
    except:
        pass
    return False

# --------------------------------------------------

def main():
    domain = find_active_domain()
    if not domain:
        return

    base_url = get_base_url(domain)
    if not base_url:
        print("❌ baseurl bulunamadığı için işlem iptal edildi.")
        return

    print("\n📺 Kanal testleri başlıyor...\n")

    m3u_lines = ["#EXTM3U"]
    count = 0

    for cid, name in CHANNELS.items():
        stream_url = f"{base_url}{cid}/mono.m3u8"
        print(f"🔍 {name} ({cid})")

        if test_stream(stream_url, domain):
            count += 1
            m3u_lines.append(f'#EXTINF:-1 group-title="Spor",{name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={domain}/')
            m3u_lines.append(stream_url)
            print("✅ Çalışıyor")
        else:
            print("❌ Çalışmıyor")

    with open("mono.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print("\n🎯 TAMAMLANDI")
    print(f"✔ Toplam çalışan kanal: {count}")
    print("✔ Dosya kaydedildi → mono.m3u")

# --------------------------------------------------

if __name__ == "__main__":
    main()
