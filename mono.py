import requests
import re
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoHybridScraper:
    def __init__(self):
        self.api_url = "https://justintvcanli.online/domain.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.kanallar = {
            "zirve": "beIN Sports 1 A", "trgoals": "beIN Sports 1 B", "yayin1": "beIN Sports 1 C",
            "b2": "beIN Sports 2", "b3": "beIN Sports 3", "b4": "beIN Sports 4", "b5": "beIN Sports 5",
            "bm1": "beIN Sports 1 Max", "bm2": "beIN Sports 2 Max", "ss1": "S Sports 1",
            "ss2": "S Sports 2", "smarts": "Smart Sports", "sms2": "Smart Sports 2",
            "t1": "Tivibu Sports 1", "t2": "Tivibu Sports 2", "t3": "Tivibu Sports 3",
            "t4": "Tivibu Sports 4", "as": "A Spor", "trtspor": "TRT Spor",
            "trtspor2": "TRT Spor Yıldız", "trt1": "TRT 1", "atv": "ATV",
            "tv85": "TV8.5", "nbatv": "NBA TV", "eu1": "Euro Sport 1", "eu2": "Euro Sport 2",
            "ex1": "Tâbii 1", "ex2": "Tâbii 2", "ex3": "Tâbii 3", "ex4": "Tâbii 4",
            "ex5": "Tâbii 5", "ex6": "Tâbii 6", "ex7": "Tâbii 7", "ex8": "Tâbii 8"
        }

    def fetch_assets(self):
        """Aktif domaini (Referer) tarayarak bulur ve sunucuyu API'den çeker."""
        active_referer = None
        
        print("🌐 Aktif domain (Referer) taranıyor...")
        # 530'dan 580'e kadar aktif olanı bul
        for i in range(530, 580):
            target = f"https://monotv{i}.com"
            try:
                # Proxy kullanmadan direkt deniyoruz, gerekirse proxy_base eklenebilir
                r = requests.get(target, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200:
                    active_referer = target + "/"
                    print(f"✅ Aktif Referer Bulundu: {active_referer}")
                    break
            except:
                continue

        # Yayın sunucusunu API'den al
        print("📡 Yayın sunucusu API'den çekiliyor...")
        stream_server = None
        try:
            rapi = requests.get(self.api_url, headers=self.headers, timeout=10, verify=False)
            if rapi.status_code == 200:
                data = rapi.json()
                stream_server = data.get("baseurl", "").replace("\\", "")
        except:
            pass

        return active_referer, stream_server

    def run(self):
        referer, stream = self.fetch_assets()

        # Eğer domain bulunamazsa hata verme, sadece bildir
        if not referer:
            referer = "https://justintvcanli.online/" # Yedek referer
            print("⚠️ Aktif monotv bulunamadı, yedek referer kullanılıyor.")
        
        if not stream:
            print("❌ Sunucu adresi API'den alınamadı.")
            return

        print(f"✅ Final Sunucu: {stream}")
        print(f"✅ Final Referer: {referer}")

        m3u = ["#EXTM3U"]
        for cid, name in self.kanallar.items():
            m3u.append(f'#EXTINF:-1,{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={referer}')
            m3u.append(f'{stream}{cid}/mono.m3u8')

        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        
        print(f"🏁 Başarılı: {len(self.kanallar)} kanal hazır.")

if __name__ == "__main__":
    MonoHybridScraper().run()
