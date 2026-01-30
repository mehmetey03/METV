import requests
import re
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://monotv530.com/"
    }

    # 1. Aktif Domain Bul
    active_domain = None
    for i in range(530, 550):
        url = f"https://monotv{i}.com"
        try:
            r = session.get(url, timeout=5, verify=False)
            if r.status_code == 200:
                active_domain = url
                break
        except: continue

    if not active_domain:
        print("❌ Domain bulunamadı.")
        return

    print(f"✅ Domain: {active_domain}")
    base_url = "https://rei.zirvedesin201.cfd/"

    try:
        r = session.get(active_domain, headers=headers, verify=False)
        html = r.text

        # 2. Regex ile Kanal Bloklarını Yakala
        # Bu pattern: <a...href="channel?id=xxx" ... > ... <div class="home">İsim</div> ... </a> yapısını yakalar
        pattern = r'href="channel\?id=([^"]+)".*?<div class="home">([^<]+)</div>'
        matches = re.findall(pattern, html, re.DOTALL)

        m3u_content = ["#EXTM3U"]
        seen = set()

        for cid, name in matches:
            cid = cid.strip()
            name = name.strip().upper()
            
            if cid in seen: continue
            
            # M3U Formatı
            m3u_content.append(f'#EXTINF:-1 group-title="MonoTV",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            seen.add(cid)

        # 3. Sonuçları Kaydet
        if len(seen) > 0:
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_content))
            print(f"🏁 Başarılı! {len(seen)} kanal yakalandı.")
        else:
            # Yedek plan: Eğer hala boşsa ham ID taraması yap
            print("⚠️ Özel yapı bulunamadı, ham tarama deneniyor...")
            ham_ids = re.findall(r'id=([a-zA-Z0-9_-]{2,15})', html)
            ham_ids = list(dict.fromkeys(ham_ids))
            
            for hid in ham_ids:
                if hid in ['css', 'js', 'video', 'google']: continue
                m3u_content.append(f'#EXTINF:-1,{hid.upper()}')
                m3u_content.append(f'{base_url}{hid}/mono.m3u8')
            
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_content))
            print(f"🏁 Ham modda {len(ham_ids)} kanal yazıldı.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
