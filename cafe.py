import re
import requests
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DOMAIN = "https://www.sporcafe-4a2fb1f79d.xyz/"

def fetch_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": BASE_DOMAIN
    }
    try:
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        return r.text
    except:
        return None


def get_stream_links(channels):
    print("🔗 Stream linkleri alınıyor...")

    main_html = fetch_url(BASE_DOMAIN)
    if not main_html:
        print("✗ Ana sayfa alınamadı")
        return None

    # Stream domain tespiti
    stream_match = re.search(
        r'https?:\/\/(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)',
        main_html
    )

    if not stream_match:
        print("✗ Stream domain bulunamadı")
        return None

    stream_domain = f"https://{stream_match.group(1)}"
    print(f"✓ Stream domain: {stream_domain}")

    results = {}
    success = 0

    for i, ch in enumerate(channels, 1):
        print(f"[{i:02}/{len(channels)}] {ch['name']}")

        page = fetch_url(f"{stream_domain}/index.php?id={ch['id']}")
        if not page:
            continue

        ads = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', page)
        if not ads:
            continue

        base = ads.group(1).rstrip("/") + "/"
        stream_url = f"{base}{ch['id']}/playlist.m3u8"

        results[ch["id"]] = {
            "url": stream_url,
            "name": ch["name"],
            "tvg_id": ch["tvg_id"],
            "logo": ch["logo"],
            "group": ch["group"]
        }

        success += 1
        print("   ✓ OK")

    return {
        "referer": BASE_DOMAIN,
        "stream_domain": stream_domain,
        "channels": results,
        "successful": success
    }


def generate_m3u(info):
    out = ["#EXTM3U"]

    for _, ch in sorted(info["channels"].items(), key=lambda x: x[1]["name"]):
        out.append(
            f'#EXTINF:-1 tvg-id="{ch["tvg_id"]}" tvg-name="{ch["name"]}" '
            f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}'
        )
        out.append(f'#EXTVLCOPT:http-referrer={info["referer"]}')
        out.append(ch["url"])
        out.append("")

    return "\n".join(out)


def main():
    print("=" * 60)
    print("SPORCAFE M3U PLAYLIST OLUŞTURUCU")
    print("=" * 60)

    channels = [
        {"id": "sbeinsports-1", "name": "BeIN Sports 1", "tvg_id": "bein1", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/5rhmw31628798883.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-2", "name": "BeIN Sports 2", "tvg_id": "bein2", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/7uv6x71628799003.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-3", "name": "BeIN Sports 3", "tvg_id": "bein3", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/u3117i1628798857.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-4", "name": "BeIN Sports 4", "tvg_id": "bein4", "logo": "https://i.postimg.cc/0yjyF10x/bein4.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsports-5", "name": "BeIN Sports 5", "tvg_id": "bein5", "logo": "https://i.postimg.cc/BvjF7hx5/bein5.png", "group": "BEIN SPORTS"},
        {"id": "sbeinsportshaber", "name": "BeIN Sports Haber", "tvg_id": "beinhd", "logo": "https://i.postimg.cc/x14Fs2kw/beinhd.png", "group": "BEIN SPORTS"},
        {"id": "sdazn1", "name": "DAZN 1", "tvg_id": "dazn1", "logo": "https://i.postimg.cc/QMgmHh7x/dazn1.png", "group": "DAZN"},
        {"id": "sdazn2", "name": "DAZN 2", "tvg_id": "dazn2", "logo": "https://i.postimg.cc/XY5YQvSd/dazn2.png", "group": "DAZN"},
        {"id": "saspor", "name": "A Spor", "tvg_id": "aspor", "logo": "https://i.postimg.cc/gJMK4kTN/aspor.png", "group": "YEREL SPOR"},
        {"id": "sssport", "name": "S Sport", "tvg_id": "ssport", "logo": "https://i.postimg.cc/TYcZT4zR/ssport.png", "group": "S SPORT"},
        {"id": "sssport2", "name": "S Sport 2", "tvg_id": "ssport2", "logo": "https://i.postimg.cc/WbftnShM/ssport2.png", "group": "S SPORT"},
        {"id": "sssplus1", "name": "S Sport Plus", "tvg_id": "ssportplus", "logo": "https://i.postimg.cc/rmK04Jxr/ssportplus.png", "group": "S SPORT"},
        {"id": "strtspor", "name": "TRT Spor", "tvg_id": "trtspor", "logo": "https://i.postimg.cc/jjTfdSTL/trtspor.png", "group": "TRT"},
        {"id": "strtspor2", "name": "TRT Spor 2", "tvg_id": "trtspor2", "logo": "https://i.postimg.cc/wvsvstyn/trtspor2.png", "group": "TRT"},
        {"id": "stv8", "name": "TV8", "tvg_id": "tv8", "logo": "https://i.postimg.cc/CLpftN9Y/tv8.png", "group": "DİĞER"},
        {"id": "sexxen-1", "name": "Exxen Spor 1", "tvg_id": "exxen1", "logo": "https://i.postimg.cc/B6t4z1d3/exxen.png", "group": "EXXEN"},
        {"id": "sexxen-2", "name": "Exxen Spor 2", "tvg_id": "exxen2", "logo": "https://i.postimg.cc/B6t4z1d3/exxen.png", "group": "EXXEN"},
        {"id": "ssmartspor", "name": "Smart Spor", "tvg_id": "smartspor", "logo": "https://i.postimg.cc/7YNxxHgM/smartspor.png", "group": "DİĞER"},
        {"id": "ssmartspor2", "name": "Smart Spor 2", "tvg_id": "smartspor2", "logo": "https://i.postimg.cc/7YNxxHgM/smartspor.png", "group": "DİĞER"},
        {"id": "stivibuspor-1", "name": "Tivibu Spor 1", "tvg_id": "tivibu1", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stivibuspor-2", "name": "Tivibu Spor 2", "tvg_id": "tivibu2", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stivibuspor-3", "name": "Tivibu Spor 3", "tvg_id": "tivibu3", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stivibuspor-4", "name": "Tivibu Spor 4", "tvg_id": "tivibu4", "logo": "https://i.postimg.cc/G2xMf9Gn/tivibu.png", "group": "TİVİBU"},
        {"id": "stabiispor-1", "name": "Tabii Spor 1", "tvg_id": "tabii1", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-2", "name": "Tabii Spor 2", "tvg_id": "tabii2", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-3", "name": "Tabii Spor 3", "tvg_id": "tabii3", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-4", "name": "Tabii Spor 4", "tvg_id": "tabii4", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "stabiispor-5", "name": "Tabii Spor 5", "tvg_id": "tabii5", "logo": "https://i.postimg.cc/9MpztRQF/tabii.png", "group": "TABII"},
        {"id": "strt1", "name": "TRT 1", "tvg_id": "trt1", "logo": "https://i.postimg.cc/XYJkFyqV/trt1.png", "group": "TRT"},
    ]

    print(f"📺 {len(channels)} kanal işlenecek")

    info = get_stream_links(channels)
    if not info or not info["channels"]:
        print("✗ Stream bulunamadı")
        return

    m3u = generate_m3u(info)

    with open("sporcafe.m3u", "w", encoding="utf-8") as f:
        f.write(m3u)

    print("\n✅ TAMAMLANDI")
    print(f"📡 Referer: {BASE_DOMAIN}")
    print(f"📺 Kanal: {info['successful']}")
    print("💾 Dosya: sporcafe.m3u")


if __name__ == "__main__":
    main()
