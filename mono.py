import requests
import urllib3
import json

# SSL sertifika uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoDirectScraper:
    def __init__(self):
        # Doğrudan API adresi
        self.api_url = "https://justintvcanli.online/domain.php"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
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

    def get_base_url(self):
        """API'ye doğrudan bağlanarak yayın sunucusunu çeker."""
        print(f"📡 API'ye bağlanılıyor: {self.api_url}")
        try:
            r = requests.get(self.api_url, headers=self.headers, timeout=10, verify=False)
            if r.status_code == 200:
                # JSON verisini parse et
                data = r.json()
                # Ters bölü işaretlerini (\/) düzelt
                base = data.get("baseurl", "").replace("\\", "")
                if base:
                    print(f"✅ Yayın Sunucusu Bulundu: {base}")
                    return base
            else:
                print(f"❌ API Hatası: Durum Kodu {r.status_code}")
        except Exception as e:
            print(f"❌ Bağlantı Hatası: {e}")
        return None

    def run(self):
        # 1. Yayın sunucusunu al
        stream_base = self.get_base_url()
        
        if not stream_base:
            print("❌ İşlem iptal edildi: Sunucu adresi alınamadı.")
            return

        # 2. Referer bilgisini API domaininden türet
        referer = "https://justintvcanli.online/"

        m3u = ["#EXTM3U"]
        for cid, name in self.kanallar.items():
            # M3U Formatını oluştur
            m3u.append(f'#EXTINF:-1 group-title="MonoTV",{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={referer}')
            # Link: Sunucu + kanal id + /mono.m3u8
            m3u.append(f'{stream_base}{cid}/mono.m3u8')

        # 3. Dosyaya yaz
        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        
        print(f"🏁 BAŞARILI: {len(self.kanallar)} kanal mono.m3u dosyasına kaydedildi.")

if __name__ == "__main__":
    MonoDirectScraper().run()
