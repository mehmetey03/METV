import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoDeepScan:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://google.com"
        }

    def run(self):
        # 1. Aktif Domaini Bul
        active_url = None
        html = ""
        for i in range(530, 560):
            url = f"https://monotv{i}.com"
            try:
                r = requests.get(url, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200:
                    active_url, html = url, r.text
                    print(f"✅ Aktif Site: {url}")
                    break
            except: continue

        if not active_url: return

        # 2. Yayın Sunucusunu (Dinamik Regex) Bul
        # Sitede 'zirvedesin', 'xyz', 'cfd' gibi geçen tüm yayın linklerini tara
        stream_patterns = [
            r'https?://[a-z0-9.-]+\.(?:cfd|xyz|live|pw|site|tv|sbs)/',
            r'["\'](https?://[^"\']+?/mono\.m3u8)'
        ]
        
        base_stream = "https://rei.zirvedesin201.cfd/" # Default
        for p in stream_patterns:
            m = re.search(p, html)
            if m:
                found = m.group(0 if "http" in p else 1)
                if "m3u8" in found:
                    base_stream = found.split('zirve')[0] if 'zirve' in found else found.rsplit('/', 2)[0] + "/"
                else:
                    base_stream = found
                break
        
        print(f"📡 Sunucu: {base_stream}")

        # 3. Agresif ID ve İsim Yakalayıcı (Ham Metin Taraması)
        # Link yapısı: channel.html?id=XXX veya id=XXX formatlarını bul
        # Yanındaki isimleri yakalamak için daha esnek bir yapı
        raw_matches = re.findall(r'id=([a-zA-Z0-9_-]{3,})', html)
        unique_ids = list(dict.fromkeys(raw_matches))
        
        m3u = ["#EXTM3U"]
        count = 0

        for cid in unique_ids:
            # Sistem dosyalarını ele
            if any(x in cid.lower() for x in ['google', 'twitter', 'facebook', 'whatsapp', 'script', 'main', 'jquery']):
                continue
            
            # İsimlendirme (ID'den temizle)
            name = cid.upper().replace('-', ' ').replace('_', ' ')
            
            # Gruba ayır (spor kelimesi geçiyorsa spor yap)
            group = "MAÇLAR" if any(x in cid.lower() for x in ['bein', 'spor', 'tivibu', 'smart', 'ssport']) else "7/24 KANALLAR"

            m3u.append(f'#EXTINF:-1 group-title="{group}",{name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={active_url}/')
            m3u.append(f'{base_stream}{cid}/mono.m3u8')
            count += 1

        # 4. Kaydet
        if count > 0:
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u))
            print(f"🏁 SONUÇ: {count} yayın başarıyla eklendi.")
        else:
            print("❌ Hala 0 yayın! Site içeriği şifreli olabilir.")

if __name__ == "__main__":
    MonoDeepScan().run()
