import requests
import re
import sys
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://google.com"
}

def extract_base_url(html):
    patterns = [
        r'const\s+BASE_URL\s*=\s*"([^"]+)"',
        r'var\s+streamUrl\s*=\s*"([^"]+)"',
        r'source:\s*"([^"]+\.m3u8)"'
    ]

    for p in patterns:
        m = re.search(p, html)
        if m:
            url = m.group(1)
            if url.endswith(".m3u8"):
                return url.rsplit("/", 1)[0] + "/"
            return url

    return None

def main():
    try:
        # ===============================
        # SABİT KANALLAR
        # ===============================
        fixed_channels = {
            "yayinzirve": ["beIN Sports 1 A", "Inat TV"],
            "yayininat":  ["beIN Sports 1 B", "Inat TV"],
            "yayin1":     ["beIN Sports 1 C", "Inat TV"],
            "yayinb2":    ["beIN Sports 2", "Inat TV"],
            "yayinss":    ["S Sports 1", "Inat TV"],
            "yayinas":    ["A Spor", "Inat TV"],
            "yayintrt1":  ["TRT 1", "Inat TV"]
        }

        # ===============================
        # AKTİF DOMAIN
        # ===============================
        active_domain = None
        print("🔍 Aktif domain aranıyor...")

        for i in range(1200, 2000):
            url = f"https://trgoals{i}.xyz/"
            try:
                r = requests.head(url, headers=HEADERS, timeout=5)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Aktif domain: {active_domain}")
                    break
            except:
                continue

        if not active_domain:
            print("❌ Domain bulunamadı")
            return 0

        # ===============================
        # BASE_URL ÇÖZ
        # ===============================
        main_html = requests.get(active_domain, headers=HEADERS, timeout=10).text

        iframe_id = re.search(r'id=([^"&]+)', main_html)
        if not iframe_id:
            print("❌ iframe ID yok")
            return 0

        channel_html = requests.get(
            f"{active_domain}channel.html?id={iframe_id.group(1)}",
            headers=HEADERS,
            timeout=10
        ).text

        base_url = extract_base_url(channel_html)
        if not base_url:
            print("❌ BASE_URL çözülemedi (TRGOALS JS)")
            return 0

        print(f"✅ BASE_URL: {base_url}")

        # ===============================
        # CANLI MAÇLAR
        # ===============================
        response = requests.get(active_domain, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        matches_tab = soup.find(id="matches-tab")
        dynamic = []

        if matches_tab:
            for a in matches_tab.find_all("a", href=re.compile("channel.html")):
                cid = re.search(r'id=([^&]+)', a["href"]).group(1)
                name = a.find(class_="channel-name")
                time = a.find(class_="channel-status")
                if name and time:
                    dynamic.append((cid, f"{time.text.strip()} | {name.text.strip()}"))

        # ===============================
        # M3U
        # ===============================
        lines = ["#EXTM3U"]

        for cid, title in dynamic:
            lines += [
                f'#EXTINF:-1 group-title="Canlı Maçlar",{title}',
                f'#EXTVLCOPT:http-referrer={active_domain}',
                f"{base_url}{cid}.m3u8"
            ]

        for cid, info in fixed_channels.items():
            lines += [
                f'#EXTINF:-1 group-title="{info[1]}",{info[0]}',
                f'#EXTVLCOPT:http-referrer={active_domain}',
                f"{base_url}{cid}.m3u8"
            ]

        with open("karsilasmalar2.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("✅ karsilasmalar2.m3u hazır")

    except Exception as e:
        print("❌ Hata:", e)

if __name__ == "__main__":
    sys.exit(main())
