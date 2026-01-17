import requests
import re
import sys
from bs4 import BeautifulSoup


def extract_base_url(channel_html, cid):
    """
    channel.html içinden cid.m3u8 geçen TAM URL'yi yakalar
    ve base_url üretir
    """
    # cid.m3u8 geçen URL'yi bul
    pattern = rf'(https?://[^"\']+/{cid}\.m3u8)'
    m = re.search(pattern, channel_html)
    if not m:
        return None

    full_url = m.group(1)
    return full_url.replace(f"{cid}.m3u8", "")


def main():
    try:
        # ===============================
        # SABİT KANAL LİSTESİ
        # ===============================
        fixed_channels = {
            "yayinzirve": ["beIN Sports 1 A", "Inat TV"],
            "yayininat": ["beIN Sports 1 B", "Inat TV"],
            "yayin1": ["beIN Sports 1 C", "Inat TV"],
            "yayinb2": ["beIN Sports 2", "Inat TV"],
            "yayinb3": ["beIN Sports 3", "Inat TV"],
            "yayinb4": ["beIN Sports 4", "Inat TV"],
            "yayinb5": ["beIN Sports 5", "Inat TV"],
            "yayinbm1": ["beIN Sports 1 Max", "Inat TV"],
            "yayinbm2": ["beIN Sports 2 Max", "Inat TV"],
            "yayinss": ["S Sports 1", "Inat TV"],
            "yayinss2": ["S Sports 2", "Inat TV"],
            "yayint1": ["Tivibu Sports 1", "Inat TV"],
            "yayint2": ["Tivibu Sports 2", "Inat TV"],
            "yayint3": ["Tivibu Sports 3", "Inat TV"],
            "yayint4": ["Tivibu Sports 4", "Inat TV"],
            "yayinas": ["A Spor", "Inat TV"],
            "yayintrtspor": ["TRT Spor", "Inat TV"],
            "yayintrtspor2": ["TRT Spor Yıldız", "Inat TV"],
            "yayintrt1": ["TRT 1", "Inat TV"],
            "yayinatv": ["ATV", "Inat TV"],
            "yayintv85": ["TV8.5", "Inat TV"],
            "yayinnbatv": ["NBATV", "Inat TV"],
            "yayineu1": ["Euro Sport 1", "Inat TV"],
            "yayineu2": ["Euro Sport 2", "Inat TV"],
        }

        # ===============================
        # AKTİF DOMAIN BUL
        # ===============================
        print("🔍 Aktif domain aranıyor...")
        active_domain = None

        for i in range(1400, 2000):
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
        # İLK KANAL ID
        # ===============================
        main_html = requests.get(active_domain, timeout=10).text
        m = re.search(r'/channel\.html\?id=([^"&]+)', main_html)
        if not m:
            print("❌ İlk kanal ID bulunamadı")
            return 0

        first_id = m.group(1)

        # ===============================
        # BASE_URL ÇÖZ
        # ===============================
        channel_html = requests.get(
            f"{active_domain}channel.html?id={first_id}",
            timeout=10
        ).text

        base_url = extract_base_url(channel_html, first_id)
        if not base_url:
            print("❌ BASE_URL çözülemedi (m3u8 bulunamadı)")
            return 0

        print(f"✅ BASE_URL çözüldü: {base_url}")

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

        for cid, title in dynamic_channels:
            lines.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(f'{base_url}{cid}.m3u8')

        for cid, info in fixed_channels.items():
            lines.append(f'#EXTINF:-1 group-title="{info[1]}",{info[0]}')
            lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            lines.append(f'{base_url}{cid}.m3u8')

        with open("karsilasmalar_final.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print("✅ karsilasmalar_final.m3u oluşturuldu")
        return 0

    except Exception as e:
        print(f"❌ Hata: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
