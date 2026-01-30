import requests
import re
import json
import urllib3
import base64
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AdvancedMonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "tr-TR,tr;q=0.9",
            "Connection": "keep-alive"
        }

    # -------------------------------------------------

    def get_active_domain(self):
        print("🔍 Aktif MonoTV domain aranıyor...")
        domains = [
            "https://monotv.com",
            "https://www.monotv.com",
            "https://monotv.net",
            "https://monotv.org"
        ]
        for i in range(530, 620):
            domains.append(f"https://monotv{i}.com")

        for domain in domains:
            try:
                r = self.session.get(domain, headers=self.headers, timeout=6, verify=False)
                if r.status_code == 200 and "player-channel-area" in r.text:
                    print(f"✅ Aktif domain: {domain}")
                    return domain.rstrip("/")
            except:
                pass

        print("❌ Aktif domain bulunamadı")
        return None

    # -------------------------------------------------

    def extract_channels(self, html):
        soup = BeautifulSoup(html, "html.parser")
        channels = []

        for a in soup.find_all("a", href=True):
            if "channel?id=" in a["href"]:
                cid = a["href"].split("channel?id=")[-1].split("&")[0]
                name = a.text.strip() or cid.upper()
                if len(cid) > 1:
                    channels.append({
                        "id": cid,
                        "name": name,
                        "type": "channel"
                    })

        # uniq
        uniq = {}
        for c in channels:
            uniq[c["id"]] = c
        return list(uniq.values())

    # -------------------------------------------------

    def find_m3u8_server(self, html):
        print("🔍 m3u8 sunucusu aranıyor...")

        # Base64 çöz
        for b64 in re.findall(r'atob\(["\']([^"\']+)["\']\)', html):
            try:
                decoded = base64.b64decode(b64).decode()
                if ".m3u8" in decoded:
                    server = decoded.rsplit("/", 1)[0] + "/"
                    print(f"🔓 Base64 sunucu bulundu: {server}")
                    return server
            except:
                pass

        # Düz regex
        match = re.search(r'(https?://[^"\']+?/[^"\']+?\.m3u8)', html)
        if match:
            server = match.group(1).rsplit("/", 1)[0] + "/"
            print(f"🔓 Regex sunucu bulundu: {server}")
            return server

        # fallback
        fallback = "https://rei.zirvedesin201.cfd/"
        print(f"⚠️ Varsayılan sunucu kullanılıyor: {fallback}")
        return fallback

    # -------------------------------------------------

    def test_m3u8(self, url, referer):
        try:
            r = self.session.get(
                url,
                headers={**self.headers, "Referer": referer},
                timeout=6,
                verify=False,
                stream=True
            )
            if r.status_code in (200, 206):
                ct = r.headers.get("Content-Type", "")
                if "mpegurl" in ct or ".m3u8" in url:
                    return True
        except:
            pass
        return False

    # -------------------------------------------------

    def resolve_m3u8(self, base, channels, referer):
        valid = []
        for c in channels:
            cid = c["id"]
            paths = [
                f"live/{cid}/index.m3u8",
                f"live/{cid}/mono.m3u8",
                f"{cid}/index.m3u8",
                f"{cid}/mono.m3u8",
                f"hls/{cid}/index.m3u8"
            ]
            for p in paths:
                url = base + p
                if self.test_m3u8(url, referer):
                    c["m3u8"] = url
                    valid.append(c)
                    print(f"✅ {c['name']} → OK")
                    break
        return valid

    # -------------------------------------------------

    def save_outputs(self, channels, domain):
        print("💾 M3U ve JSON yazılıyor...")

        m3u = ["#EXTM3U"]
        for c in channels:
            m3u.append(f'#EXTINF:-1 group-title="MonoTV",{c["name"]}')
            m3u.append(f'#EXTVLCOPT:http-referrer={domain}/')
            m3u.append(c["m3u8"])

        with open("mono_channels.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))

        with open("mono_channels.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=2, ensure_ascii=False)

        print(f"✅ {len(channels)} kanal kaydedildi")

    # -------------------------------------------------

    def scrape(self):
        print("🚀 MonoTV Scraper başlatıldı")

        domain = self.get_active_domain()
        if not domain:
            return

        r = self.session.get(domain, headers=self.headers, verify=False)
        html = r.text

        channels = self.extract_channels(html)
        print(f"📺 Bulunan kanal ID: {len(channels)}")

        base = self.find_m3u8_server(html)
        valid = self.resolve_m3u8(base, channels, domain)

        self.save_outputs(valid, domain)

        print("\n🎯 TAMAMLANDI")
        print(f"✔ Aktif domain : {domain}")
        print(f"✔ m3u8 server : {base}")
        print(f"✔ Çalışan kanal : {len(valid)}")

# -----------------------------------------------------

if __name__ == "__main__":
    try:
        AdvancedMonoScraper().scrape()
    except KeyboardInterrupt:
        print("\n⏹️ Durduruldu")
