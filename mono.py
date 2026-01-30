import requests
import re
import json
import base64
import urllib3

urllib3.disable_warnings()

class MonoTV:
    def __init__(self):
        self.s = requests.Session()
        self.h = {
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
                r = self.s.get(d, headers=self.h, timeout=7, verify=False)
                if r.status_code == 200 and "Mono" in r.text:
                    print(f"✅ Aktif domain: {d}")
                    return d, r.text
            except:
                pass
        return None, None

    # --------------------------------------------------

    def extract_api(self, html, domain):
        print("🔍 API endpoint aranıyor...")

        candidates = set()

        # 1️⃣ HTML içindeki fetch / axios
        patterns = [
            r'fetch\(["\'](\/api\/[^"\']+)["\']',
            r'axios\.get\(["\'](\/api\/[^"\']+)["\']',
            r'["\'](\/api\/[^"\']+)["\']'
        ]

        for p in patterns:
            for m in re.findall(p, html):
                candidates.add(m)

        # 2️⃣ JS dosyalarını da tara
        js_files = re.findall(r'src="([^"]+\.js)"', html)

        for js in js_files:
            js_url = js if js.startswith("http") else domain + js
            try:
                r = self.s.get(js_url, headers=self.h, timeout=5, verify=False)
                if r.status_code == 200:
                    for p in patterns:
                        for m in re.findall(p, r.text):
                            candidates.add(m)
            except:
                pass

        if not candidates:
            return None

        api = domain + sorted(candidates)[0]
        print(f"✅ API bulundu: {api}")
        return api

    # --------------------------------------------------

    def extract_channels(self, api):
        print("📺 Kanal listesi alınıyor...")
        try:
            r = self.s.get(api, headers=self.h, timeout=10, verify=False)
            data = r.json()
        except:
            print("❌ API JSON alınamadı")
            return []

        channels = []
        for i in data:
            cid = i.get("id") or i.get("slug")
            name = i.get("name") or cid
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
        print(f"⚠️ Varsayılan sunucu: {fallback}")
        return fallback

    # --------------------------------------------------

    def run(self):
        print("\n🚀 MonoTV Scraper başlatıldı\n")

        domain, html = self.find_active_domain()
        if not domain:
            print("❌ Domain bulunamadı")
            return

        api = self.extract_api(html, domain)
        if not api:
            print("❌ API bulunamadı")
            return

        channels = self.extract_channels(api)
        if not channels:
            print("❌ Kanal yok")
            return

        server = self.find_m3u8_server(html)

        print("💾 Dosyalar yazılıyor...")
        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for c in channels:
                url = f"{server}{c['id']}/index.m3u8"
                f.write(f"#EXTINF:-1,{c['name']}\n{url}\n")

        with open("mono.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)

        print("\n🎯 TAMAMLANDI")
        print(f"✔ Domain : {domain}")
        print(f"✔ Kanal  : {len(channels)}")

# --------------------------------------------------

if __name__ == "__main__":
    MonoTV().run()
