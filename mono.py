import requests
import re
import json
import base64
import urllib3

urllib3.disable_warnings()

class MonoTV:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "*/*",
            "Referer": "https://google.com"
        }

        self.domains = [
            "https://monotv530.com",
            "https://monotv529.com",
            "https://monotv528.com"
        ]

    # --------------------------------------------------

    def find_active_domain(self):
        print("🔍 Aktif MonoTV domain aranıyor...")
        for d in self.domains:
            try:
                r = self.session.get(d, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200 and "Mono" in r.text:
                    print(f"✅ Aktif domain: {d}")
                    return d, r.text
            except:
                pass
        return None, None

    # --------------------------------------------------

    def extract_api(self, html, domain):
        js_files = re.findall(r'src="([^"]+\.js)"', html)

        for js in js_files:
            js_url = js if js.startswith("http") else domain + js
            try:
                r = self.session.get(js_url, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200:
                    m = re.search(r'api/[^"\']+', r.text)
                    if m:
                        api = domain + "/" + m.group(0).lstrip("/")
                        print(f"✅ API bulundu: {api}")
                        return api
            except:
                pass
        return None

    # --------------------------------------------------

    def extract_channels(self, api_url):
        print("📺 Kanal listesi alınıyor...")
        try:
            r = self.session.get(api_url, headers=self.headers, timeout=10, verify=False)
            data = r.json()
        except:
            print("❌ Kanal JSON alınamadı")
            return []

        channels = []
        for item in data:
            cid = item.get("id") or item.get("slug")
            name = item.get("name") or cid
            if cid:
                channels.append({
                    "id": str(cid),
                    "name": name
                })

        print(f"✅ {len(channels)} kanal bulundu")
        return channels

    # --------------------------------------------------

    def find_m3u8_server(self, html):
        print("🔍 m3u8 sunucusu aranıyor...")
        m = re.search(r'atob\("([^"]+)"\)', html)
        if m:
            try:
                server = base64.b64decode(m.group(1)).decode()
                print(f"✅ m3u8 server: {server}")
                return server
            except:
                pass

        fallback = "https://rei.zirvedesin201.cfd/"
        print(f"⚠️ Varsayılan sunucu kullanılıyor: {fallback}")
        return fallback

    # --------------------------------------------------

    def build_links(self, channels, server):
        output = []
        for ch in channels:
            url = f"{server}{ch['id']}/index.m3u8"
            output.append({
                "name": ch["name"],
                "url": url
            })
        return output

    # --------------------------------------------------

    def save_files(self, items):
        print("💾 M3U ve JSON yazılıyor...")

        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for i in items:
                f.write(f'#EXTINF:-1,{i["name"]}\n{i["url"]}\n')

        with open("mono.json", "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        print(f"✅ {len(items)} kanal kaydedildi")

    # --------------------------------------------------

    def run(self):
        print("\n🚀 MonoTV Scraper başlatıldı\n")

        domain, html = self.find_active_domain()
        if not domain:
            print("❌ Aktif domain bulunamadı")
            return

        api = self.extract_api(html, domain)
        if not api:
            print("❌ API bulunamadı")
            return

        channels = self.extract_channels(api)
        if not channels:
            print("❌ Kanal bulunamadı")
            return

        server = self.find_m3u8_server(html)
        items = self.build_links(channels, server)

        self.save_files(items)

        print("\n🎯 TAMAMLANDI")
        print(f"✔ Aktif domain : {domain}")
        print(f"✔ m3u8 server : {server}")
        print(f"✔ Çalışan kanal : {len(items)}")

# --------------------------------------------------

if __name__ == "__main__":
    MonoTV().run()
