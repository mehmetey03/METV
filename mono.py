import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoApiScraper:
    def __init__(self):
        # Proxy yardımıyla API'ye erişiyoruz (kodda domain sabit değil)
        self.proxy = "https://api.codetabs.com/v1/proxy/?quest="
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

    def get_dynamic_base(self):
        """API üzerinden güncel yayın sunucusunu çeker."""
        print("📡 Yayın sunucusu API'den alınıyor...")
        try:
            # Proxy kullanarak API'den JSON verisini çek
            response = requests.get(f"{self.proxy}{self.api_url}", headers=self.headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                # JSON içindeki baseurl'i al (Sondaki ters bölüleri temizle)
                base_url = data.get("baseurl", "").replace("\\", "")
                if base_url:
                    print(f"✅ Sunucu Tespit Edildi: {base_url}")
                    return base_url
        except Exception as e:
            print(f"❌ API Hatası: {e}")
        return None

    def run(self):
        # 1. Sunucu adresini API'den al
        stream_base = self.get_dynamic_base()
        
        if not stream_base:
            print("❌ Sunucu adresi alınamadı, işlem durduruldu.")
            return

        # 2. Referer domainini API adresinden türet (Dinamik)
        # https://justintvcanli.online/ formatına getiriyoruz
        referer = "/".join(self.api_url.split("/")[:3]) + "/"

        m3u = ["#EXTM3U"]
        for cid, name in self.kanallar.items():
            m3u.append(f'#EXTINF:-1,{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={referer}')
            # Örn: https://rei.zirvedesin201.cfd/zirve/mono.m3u8
            m3u.append(f'{stream_base}{cid}/mono.m3u8')

        # 3. Dosyaya yaz
        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        
        print(f"🏁 Başarılı! {len(self.kanallar)} kanal güncellendi.")

if __name__ == "__main__":
    MonoApiScraper().run()
