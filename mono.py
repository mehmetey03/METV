import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoProxyScraper:
    def __init__(self):
        # Kodun içinde hiçbir URL yok. Proxy'yi ana araç olarak kullanıyoruz.
        self.proxy_base = "https://api.codetabs.com/v1/proxy/?quest="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
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
        """Proxy üzerinden aktif domaini ve sunucuyu keşfeder."""
        print("🌐 Proxy üzerinden kaynaklar taranıyor...")
        for i in range(530, 570):
            # Target URL'yi de koda yazmıyoruz, döngüyle oluşturuyoruz
            target = f"https://monotv{i}.com"
            proxy_url = f"{self.proxy_base}{target}"
            
            try:
                r = requests.get(proxy_url, headers=self.headers, timeout=10, verify=False)
                if r.status_code == 200 and "mono.m3u8" in r.text:
                    # Referer olarak bulunan ana domaini al
                    referer = target + "/"
                    
                    # Sayfa kaynağından yayın sunucusunu (base stream) ayıkla
                    # Regex: tırnak içindeki http... kısmını m3u8'den önce yakalar
                    match = re.search(r'["\'](https?://[a-z0-9.-]+)/[^"\']+?/mono\.m3u8', r.text)
                    if match:
                        stream_server = match.group(1).rstrip('/') + "/"
                        return referer, stream_server
            except:
                continue
        return None, None

    def run(self):
        referer, stream = self.fetch_assets()

        if not referer or not stream:
            print("❌ Kaynaklar proxy üzerinden bulunamadı.")
            return

        print(f"🔗 Aktif Referer: {referer}")
        print(f"📡 Yayın Sunucusu: {stream}")

        m3u = ["#EXTM3U"]
        for cid, name in self.kanallar.items():
            # M3U Standartlarına uygun ekleme
            m3u.append(f'#EXTINF:-1,{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={referer}')
            # Link Yapısı: Sunucu + ID + Dosya Adı
            m3u.append(f'{stream}{cid}/mono.m3u8')

        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        
        print(f"🏁 Başarılı! {len(self.kanallar)} kanal hazır.")

if __name__ == "__main__":
    MonoProxyScraper().run()
