import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# Yasaklı kelimeler (Yayın sunucusu olamazlar)
BANNED_DOMAINS = ["gstatic", "jsdelivr", "google", "doubleclick", "analytics", "facebook", "twitter", "yandex"]

def main():
    try:
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
            "yayinsmarts": ["Smart Sports", "Inat TV"],
            "yayinsms2": ["Smart Sports 2", "Inat TV"],
            "yayinas": ["A Spor", "Inat TV"],
            "yayintrtspor": ["TRT Spor", "Inat TV"],
            "yayintrtspor2": ["TRT Spor Yıldız", "Inat TV"],
            "yayintrt1": ["TRT 1", "Inat TV"],
            "yayinatv": ["ATV", "Inat TV"],
            "yayintv85": ["TV8.5", "Inat TV"],
            "yayinnbatv": ["NBATV", "Inat TV"],
            "yayineu1": ["Euro Sport 1", "Inat TV"],
            "yayineu2": ["Euro Sport 2", "Inat TV"],
            "yayinex1": ["Tâbii 1", "Inat TV"],
            "yayinex2": ["Tâbii 2", "Inat TV"],
            "yayinex3": ["Tâbii 3", "Inat TV"],
            "yayinex4": ["Tâbii 4", "Inat TV"],
            "yayinex5": ["Tâbii 5", "Inat TV"],
            "yayinex6": ["Tâbii 6", "Inat TV"],
            "yayinex7": ["Tâbii 7", "Inat TV"],
            "yayinex8": ["Tâbii 8", "Inat TV"]
        }

        print("🔍 Aktif domain aranıyor...")
        active_domain = None
        for i in range(1230, 1300):
            url = f"https://inattv{i}.xyz"
            try:
                r = requests.get(url, headers=HEADERS, timeout=2, verify=False)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Aktif domain: {active_domain}")
                    break
            except: continue

        if not active_domain:
            sys.exit("❌ Aktif domain bulunamadı.")

        def is_valid_stream_domain(url):
            return not any(banned in url for banned in BANNED_DOMAINS)

        def resolve_base_url(channel_id):
            target = f"{active_domain}/channel.html?id={channel_id}"
            try:
                r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
                
                # m3u8 linklerini ayıkla
                urls = re.findall(r'["\'](https?://[^\s"\']+?/)[\w\-]+\.m3u8', r.text)
                for link in urls:
                    if is_valid_stream_domain(link):
                        return link

                # Alternatif arama (Regex genişletildi)
                alt_urls = re.findall(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|me|net|com|pw|site|club)/)', r.text)
                for link in alt_urls:
                    if is_valid_stream_domain(link):
                        return link
            except: pass
            return None

        # Gerçek sunucuyu yakala
        base_url = resolve_base_url("yayininat")
        if not base_url:
            sys.exit("❌ Gerçek yayın sunucusu bulunamadı.")

        print(f"✅ Yayın sunucusu: {base_url}")

        # Canlı maçları listele
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        dynamic_channels = []
        matches_tab = soup.find(id="matches-tab")
        if matches_tab:
            for a in matches_tab.find_all("a", href=re.compile(r'id=')):
                cid_match = re.search(r'id=([^&]+)', a["href"])
                name = a.find(class_="channel-name")
                status = a.find(class_="channel-status")
                if cid_match and name:
                    title = f"{status.get_text(strip=True) if status else '00:00'} | {name.get_text(strip=True)}"
                    dynamic_channels.append((cid_match.group(1), title))

        # M3U Yazdır
        with open("karsilasmalar.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for cid, title in dynamic_channels:
                f.write(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={active_domain}/\n')
                f.write(f'{base_url}{cid}.m3u8\n')

            for cid, info in fixed_channels.items():
                f.write(f'#EXTINF:-1 group-title="Inat TV",{info[0]}\n')
                f.write(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={active_domain}/\n')
                f.write(f'{base_url}{cid}.m3u8\n')

        print(f"🏁 BAŞARILI → {base_url} üzerinden liste hazır.")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
