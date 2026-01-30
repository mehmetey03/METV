import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoHybridBot:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }
        # Senin istediğin sabit kanal listesi
        self.kanal_sozlugu = {
            "zirve": "beIN Sports 1 A",
            "trgoals": "beIN Sports 1 B",
            "yayin1": "beIN Sports 1 C",
            "b2": "beIN Sports 2",
            "b3": "beIN Sports 3",
            "b4": "beIN Sports 4",
            "b5": "beIN Sports 5",
            "bm1": "beIN Sports 1 Max",
            "bm2": "beIN Sports 2 Max",
            "ss1": "S Sports 1",
            "ss2": "S Sports 2",
            "smarts": "Smart Sports",
            "sms2": "Smart Sports 2",
            "t1": "Tivibu Sports 1",
            "t2": "Tivibu Sports 2",
            "t3": "Tivibu Sports 3",
            "t4": "Tivibu Sports 4",
            "as": "A Spor",
            "trtspor": "TRT Spor",
            "trtspor2": "TRT Spor Yıldız",
            "trt1": "TRT 1",
            "atv": "ATV",
            "tv85": "TV8.5",
            "nbatv": "NBA TV",
            "eu1": "Euro Sport 1",
            "eu2": "Euro Sport 2",
            "ex1": "Tâbii 1",
            "ex2": "Tâbii 2",
            "ex3": "Tâbii 3",
            "ex4": "Tâbii 4",
            "ex5": "Tâbii 5",
            "ex6": "Tâbii 6",
            "ex7": "Tâbii 7",
            "ex8": "Tâbii 8"
        }

    def find_dynamic_assets(self):
        """Aktif domain ve yayın sunucusunu otomatik bulur."""
        print("🔍 Güncel giriş adresi ve yayın sunucusu aranıyor...")
        for i in range(530, 565):
            url = f"https://monotv{i}.com"
            try:
                r = requests.get(url, headers=self.headers, timeout=4, verify=False)
                if r.status_code == 200:
                    # 1. Referer bulundu
                    active_referer = url + "/"
                    
                    # 2. Yayın sunucusunu (base_stream) HTML içinden çek
                    # Örn: https://rei.zirvedesin201.cfd/zirve/mono.m3u8 yapısından kökü al
                    match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6})/[^"\']+?/mono\.m3u8', r.text)
                    if match:
                        base_stream = match.group(1).rstrip('/') + "/"
                        return active_referer, base_stream
            except:
                continue
        return None, None

    def run(self):
        referer, base_stream = self.find_dynamic_assets()

        if not referer or not base_stream:
            # Eğer otomatik bulunamazsa varsayılanları kullan (Güvenlik önlemi)
            referer = "https://monotv530.com/"
            base_stream = "https://rei.zirvedesin201.cfd/"
            print("⚠️ Otomatik tespit başarısız, varsayılanlar kullanılıyor.")
        else:
            print(f"✅ Bulunan Domain: {referer}")
            print(f"✅ Bulunan Sunucu: {base_stream}")

        m3u_lines = ["#EXTM3U"]
        for cid, name in self.kanal_sozlugu.items():
            group = "SPOR" if "Sport" in name or "beIN" in name else "ULUSAL"
            
            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={referer}')
            m3u_lines.append(f'{base_stream}{cid}/mono.m3u8')

        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        
        print(f"🏁 Bitti: {len(self.kanal_sozlugu)} kanal listeye eklendi.")

if __name__ == "__main__":
    MonoHybridBot().run()
