import requests
import re
import urllib3

urllib3.disable_warnings()

class MonoScraper:
    def __init__(self):
        self.s = requests.Session()
        self.h = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://monotv530.com"
        }

        self.base_server = "https://rei.zirvedesin201.cfd/"

    # --------------------------------------------------

    def get_active_domain(self):
        print("🔍 Aktif giriş adresi taranıyor...")
        for i in range(520, 560):
            url = f"https://monotv{i}.com"
            try:
                r = self.s.get(url, headers=self.h, timeout=5, verify=False)
                if r.status_code == 200:
                    print(f"✅ Giriş adresi bulundu: {url}")
                    return url.rstrip("/")
            except:
                pass
        return None

    # --------------------------------------------------

    def extract_html_ids(self, html):
        ids = re.findall(r'id=([a-zA-Z0-9_-]+)', html)
        return list(set(ids))

    # --------------------------------------------------

    def generate_candidate_ids(self):
        ids = []

        # Sayısal kanallar
        for i in range(0, 150):
            ids.append(str(i))

        # Bilinen sabitler
        ids += [
            "bein1","bein2","bein3","bein4",
            "ssport","ssport2",
            "trt1","kanald","atv","fox","tv8",
            "tivibuspor","tivibuspor2"
        ]

        return list(set(ids))

    # --------------------------------------------------

    def is_alive(self, url):
        try:
            r = self.s.head(url, headers=self.h, timeout=4, verify=False)
            return r.status_code == 200
        except:
            return False

    # --------------------------------------------------

    def scrape(self):
        domain = self.get_active_domain()
        if not domain:
            print("❌ Domain bulunamadı")
            return

        print("📡 Kanal ID’leri toplanıyor...")
        r = self.s.get(domain, headers=self.h, timeout=10, verify=False)

        html_ids = self.extract_html_ids(r.text)
        brute_ids = self.generate_candidate_ids()

        all_ids = list(set(html_ids + brute_ids))
        print(f"🔢 Denenecek toplam ID: {len(all_ids)}")

        m3u = ["#EXTM3U"]
        working = 0

        for cid in all_ids:
            if len(cid) < 1:
                continue

            url = f"{self.base_server}{cid}/mono.m3u8"
            print(f"🔍 Test: {cid}")

            if self.is_alive(url):
                working += 1
                name = cid.upper()
                group = "MonoTV"

                if any(x in cid.lower() for x in ["bein", "sport", "ssport", "tivibu"]):
                    group = "Spor"

                m3u.append(f'#EXTINF:-1 group-title="{group}",{name}')
                m3u.append(f'#EXTVLCOPT:http-referrer={domain}/')
                m3u.append(url)

                print(f"✅ ÇALIŞIYOR: {cid}")

        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))

        print("\n🎯 TAMAMLANDI")
        print(f"✔ Çalışan yayın: {working}")
        print("✔ Dosya: mono.m3u")

# --------------------------------------------------

if __name__ == "__main__":
    MonoScraper().scrape()
