import requests
import re
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MonoGodMode:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
                    print(f"✅ Site: {url}")
                    break
            except: continue

        if not active_url: return

        # 2. Yayın Sunucusunu Yakala
        stream_match = re.search(r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6})/[\w\-]+/mono\.m3u8', html)
        base_stream = stream_match.group(1).rstrip('/') + "/" if stream_match else "https://rei.zirvedesin201.cfd/"
        
        m3u = ["#EXTM3U"]
        added_ids = set()

        # 3. YÖNTEM A: JSON Verisi Ara (En Garantisi)
        # Sitedeki maçlar genellikle bir değişken içinde listelenir
        json_data = re.findall(r'(\[\{"id":.*\}\])', html)
        if json_data:
            try:
                items = json.loads(json_data[0])
                for item in items:
                    cid = item.get('id')
                    name = item.get('name', cid)
                    if cid and cid not in added_ids:
                        m3u.append(f'#EXTINF:-1 group-title="CANLI YAYINLAR",{name}\n#EXTVLCOPT:http-referrer={active_url}/\n{base_stream}{cid}/mono.m3u8')
                        added_ids.add(cid)
            except: pass

        # 4. YÖNTEM B: Gelişmiş Regex (Maç İsimlerini Çekmek İçin)
        # HTML içindeki id= ve yanındaki isimleri temizle
        # channel.html?id=... >...< yapısını hedefler
        matches = re.findall(r'id=([a-zA-Z0-9_-]+)[^>]*>([^<]+)', html)
        for cid, name in matches:
            name = name.strip()
            if len(cid) > 2 and cid not in added_ids and len(name) > 2:
                if any(x in cid for x in ['google', 'twitter', 'facebook']): continue
                m3u.append(f'#EXTINF:-1 group-title="KANALLAR",{name}\n#EXTVLCOPT:http-referrer={active_url}/\n{base_stream}{cid}/mono.m3u8')
                added_ids.add(cid)

        # 5. YÖNTEM C: Agresif ID Yakalayıcı (Eksik Kalmasın Diye)
        all_cids = re.findall(r'channel\.html\?id=([a-zA-Z0-9_-]+)', html)
        for cid in all_cids:
            if cid not in added_ids and len(cid) > 2:
                m3u.append(f'#EXTINF:-1 group-title="DIGER",{cid.upper()}\n#EXTVLCOPT:http-referrer={active_url}/\n{base_stream}{cid}/mono.m3u8')
                added_ids.add(cid)

        # 6. Dosyaya Yaz
        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        
        print(f"🏁 SONUÇ: {len(added_ids)} yayın m3u dosyasına eklendi.")

if __name__ == "__main__":
    MonoGodMode().run()
