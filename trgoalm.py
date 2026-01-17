import requests
import re
import sys
import json
from bs4 import BeautifulSoup


TRGOALS_JSON = "https://raw.githubusercontent.com/mehmetey03/METV/5af7251ac4b20adf59a0c3c8b3431b416a18ab94/trgoals_data.json"


def main():
    try:
        # ===============================
        # SABİT KANAL LİSTESİ
        # ===============================
        fixed_channels = {
            "yayinzirve": "beIN Sports 1 A",
            "yayininat":  "beIN Sports 1 B",
            "yayin1":     "beIN Sports 1 C",
            "yayinb2":    "beIN Sports 2",
            "yayinb3":    "beIN Sports 3",
            "yayinb4":    "beIN Sports 4",
            "yayinb5":    "beIN Sports 5",
            "yayinbm1":   "beIN Sports 1 Max",
            "yayinbm2":   "beIN Sports 2 Max",
            "yayinss":    "S Sports 1",
            "yayinss2":   "S Sports 2",
            "yayint1":    "Tivibu Sports 1",
            "yayint2":    "Tivibu Sports 2",
            "yayint3":    "Tivibu Sports 3",
            "yayint4":    "Tivibu Sports 4",
            "yayinas":    "A Spor",
            "yayintrtspor": "TRT Spor",
            "yayintrtspor2": "TRT Spor Yıldız",
            "yayintrt1":  "TRT 1",
            "yayinatv":   "ATV",
            "yayintv85":  "TV8.5",
            "yayinnbatv": "NBATV",
            "yayineu1":   "Euro Sport 1",
            "yayineu2":   "Euro Sport 2"
        }

        # ===============================
        # AKTİF DOMAIN BUL
        # ===============================
        print("🔍 Aktif domain aranıyor...")
        active_domain = None

        for i in range(1497, 2000):
            url = f"https://trgoals{i}.xyz/"
            try:
                r = requests.head(url, timeout=5)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Aktif domain: {active_domain}")
                    break
            except:
                continue

        if not active_domain:
            print("❌ Aktif domain bulunamadı")
            return 0

        # ===============================
        # JSON'DAN GERÇEK LINKLERİ AL
        # ===============================
        print("📦 trgoals_data.json alınıyor...")
        j = requests.get(TRGOALS_JSON, timeout=10).json()
        items = j["list"]["item"]

        json_links = {}
        base_url = None

        for it in items:
            url = it.get("url")
            if not url:
                continue

            cid = url.split("/")[-1].replace(".m3u8", "")
            json_links[cid] = url

            if not base_url:
                base_url = url.replace(f"{cid}.m3u8", "")

        if not base_url:
            print("❌ JSON içinden base_url çıkarılamadı")
            return 0

        print(f"✅ BASE_URL (JSON): {base_url}")

        # ===============================
        # CANLI MAÇLARI ÇEK
        # ===============================
        print("📡 Canlı maçlar alınıyor...")
        r = requests.get(active_domain, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        dynamic_channels = []
        matches_tab = soup.find(id="matches-tab")

        if matches_tab:
            for link in matches_tab.find_all("a", href=True):
                if "channel.html?id=" not in link["href"]:
                    continue

                cid = re.search(r'id=([^&]+)', link["href"]).group(1)
                name_el = link.find(class_="channel-name")
                time_el = link.find(class_="channel-status")

                if name_el and time_el:
                    title = f"{time_el.get_text(strip=True)} | {name_el.get_text(strip=True)}"
                    dynamic_channels.append((cid, title))

        print(f"✅ {len(dynamic_channels)} canlı maç bulundu")

        # ===============================
        # M3U OLUŞTUR
        # ===============================
        print("📝 M3U oluşturuluyor...")
        lines = ["#EXTM3U"]

        # CANLI MAÇLAR (base_url + cid)
        for cid, title in dynamic_channels:
            lines.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(f'{base_url}{cid}.m3u8')

        # SABİT KANALLAR (JSON'DAN GERÇEK URL)
        for cid, name in fixed_channels.items():
            if cid not in json_links:
                continue

            lines.append(f'#EXTINF:-1 group-title="Inat TV",{name}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(json_links[cid])

        with open("karsilasmalar_final.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("✅ karsilasmalar_final.m3u başarıyla oluşturuldu")
        return 0

    except Exception as e:
        print(f"❌ Hata: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
