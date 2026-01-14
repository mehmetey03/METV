import requests
import re
import sys
from bs4 import BeautifulSoup

def main():
    try:
        # ===============================
        # SABİT KANAL LİSTESİ
        # ===============================
        fixed_channels = {
            "yayinzirve": ["beIN Sports 1 A", "Inat TV"],
            "yayininat":  ["beIN Sports 1 B", "Inat TV"],
            "yayin1":     ["beIN Sports 1 C", "Inat TV"],
            "yayinb2":    ["beIN Sports 2", "Inat TV"],
            "yayinb3":    ["beIN Sports 3", "Inat TV"],
            "yayinb4":    ["beIN Sports 4", "Inat TV"],
            "yayinb5":    ["beIN Sports 5", "Inat TV"],
            "yayinbm1":   ["beIN Sports 1 Max", "Inat TV"],
            "yayinbm2":   ["beIN Sports 2 Max", "Inat TV"],
            "yayinss":    ["S Sports 1", "Inat TV"],
            "yayinss2":   ["S Sports 2", "Inat TV"],
            "yayint1":    ["Tivibu Sports 1", "Inat TV"],
            "yayint2":    ["Tivibu Sports 2", "Inat TV"],
            "yayint3":    ["Tivibu Sports 3", "Inat TV"],
            "yayint4":    ["Tivibu Sports 4", "Inat TV"],
            "yayinsmarts":["Smart Sports", "Inat TV"],
            "yayinsms2":  ["Smart Sports 2", "Inat TV"],
            "yayinas":    ["A Spor", "Inat TV"],
            "yayintrtspor": ["TRT Spor", "Inat TV"],
            "yayintrtspor2":["TRT Spor Yıldız", "Inat TV"],
            "yayintrt1":  ["TRT 1", "Inat TV"],
            "yayinatv":   ["ATV", "Inat TV"],
            "yayintv85":  ["TV8.5", "Inat TV"],
            "yayinnbatv": ["NBATV", "Inat TV"],
            "yayineu1":   ["Euro Sport 1", "Inat TV"],
            "yayineu2":   ["Euro Sport 2", "Inat TV"],
            "yayinex1":   ["Tâbii 1", "Inat TV"],
            "yayinex2":   ["Tâbii 2", "Inat TV"],
            "yayinex3":   ["Tâbii 3", "Inat TV"],
            "yayinex4":   ["Tâbii 4", "Inat TV"],
            "yayinex5":   ["Tâbii 5", "Inat TV"],
            "yayinex6":   ["Tâbii 6", "Inat TV"],
            "yayinex7":   ["Tâbii 7", "Inat TV"],
            "yayinex8":   ["Tâbii 8", "Inat TV"]
        }

        # ===============================
        # AKTİF DOMAIN BUL
        # ===============================
        active_domain = None
        print("🔍 Aktif domain aranıyor...")

        for i in range(1212, 2000):
            url = f"https://inattv{i}.xyz/"
            try:
                r = requests.head(url, timeout=5)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Aktif domain: {active_domain}")
                    break
            except:
                continue

        if not active_domain:
            print("⚠️ Aktif domain bulunamadı")
            return 0

        # ===============================
        # BASE_URL AL
        # ===============================
        main_html = requests.get(active_domain, timeout=10).text
        m = re.search(
            r'<iframe[^>]+id="customIframe"[^>]+src="/channel.html\?id=([^"]+)"',
            main_html
        )
        if not m:
            print("⚠️ İlk kanal ID bulunamadı")
            return 0

        first_id = m.group(1)
        channel_html = requests.get(
            f"{active_domain}channel.html?id={first_id}", timeout=10
        ).text

        b = re.search(r'const\s+BASE_URL\s*=\s*"([^"]+)"', channel_html)
        if not b:
            print("⚠️ BASE_URL bulunamadı")
            return 0

        base_url = b.group(1)
        print(f"✅ BASE_URL: {base_url}")

        # ===============================
        # CANLI MAÇLARI ÇEK (UTF-8 FIX)
        # ===============================
        print("📡 Canlı maçlar alınıyor...")
        response = requests.get(active_domain, timeout=10)
        response.encoding = "utf-8"   # 🔥 TÜRKÇE KARAKTER FIX
        soup = BeautifulSoup(response.text, "html.parser")

        matches_tab = soup.find(id="matches-tab")
        dynamic_channels = []

        if matches_tab:
            links = matches_tab.find_all(
                "a", href=re.compile(r'/channel\.html\?id=')
            )
            for link in links:
                id_match = re.search(r'id=([^&]+)', link.get("href", ""))
                if not id_match:
                    continue

                cid = id_match.group(1)
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

        # CANLI MAÇLAR
        for cid, title in dynamic_channels:
            lines.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(f'{base_url}{cid}.m3u8')

        # SABİT KANALLAR
        for cid, info in fixed_channels.items():
            lines.append(f'#EXTINF:-1 group-title="{info[1]}",{info[0]}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(f'{base_url}{cid}.m3u8')

        with open("karsilasmalar.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("✅ karsilasmalar.m3u başarıyla oluşturuldu")
        return 0

    except Exception as e:
        print(f"❌ Hata: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
