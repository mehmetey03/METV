import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoBot:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

    def run(self):
        # 1. Aktif Domaini Bul (Hızlı Tarama)
        active_url = None
        html_content = ""
        for i in range(530, 560):
            url = f"https://monotv{i}.com"
            try:
                r = requests.get(url, headers=self.headers, timeout=5, verify=False)
                if r.status_code == 200:
                    active_url = url
                    html_content = r.text
                    print(f"✅ Site bulundu: {url}")
                    break
            except: continue

        if not active_url:
            print("❌ Aktif site bulunamadı.")
            return

        # 2. Yayın Sunucusunu (Base URL) Otomatik Yakala
        # Sayfa içindeki .m3u8 içeren linklerin kök dizinini bulur
        stream_match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6})/[\w\-]+/mono\.m3u8', html_content)
        base_stream = stream_match.group(1).rstrip('/') + "/" if stream_match else "https://rei.zirvedesin201.cfd/"
        print(f"🌐 Yayın Sunucusu: {base_stream}")

        # 3. Tüm Kanal ID'lerini Regex ile Topla
        # 'id=' den sonra gelen ve tırnak/boşlukla biten her şeyi alır
        all_ids = re.findall(r'id=([a-zA-Z0-9_-]+)', html_content)
        # Tekrarlananları ve sistem ID'lerini temizle
        cids = list(dict.fromkeys([i for i in all_ids if len(i) > 2 and i not in ['google', 'twitter', 'facebook', 'whatsapp', 'telegram']]))

        if not cids:
            # Alternatif: data-id veya farklı bir yapıda saklanıyor olabilir
            cids = re.findall(r'data-id=["\']([^"\']+)["\']', html_content)

        m3u = ["#EXTM3U"]
        for cid in cids:
            # İsimlendirme: ID'den temiz bir isim üret (Örn: bein1 -> BEIN 1)
            clean_name = cid.upper().replace('BEIN', 'beIN ').replace('SPOR', ' SPOR')
            
            m3u.append(f'#EXTINF:-1 group-title="OTOMATIK LISTE",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={active_url}/')
            m3u.append(f'{base_stream}{cid}/mono.m3u8')

        # 4. Dosyaya Yaz
        if len(m3u) > 1:
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u))
            print(f"🏁 BAŞARILI: {len(cids)} kanal m3u dosyasına eklendi.")
        else:
            print("❌ Maalesef hiçbir kanal ID'si yakalanamadı. Site yapısı tamamen değişmiş.")

if __name__ == "__main__":
    MonoBot().run()
