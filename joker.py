import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TARGET_URL = "https://jokerbettv177.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

PROXIES = [
    f"https://api.codetabs.com/v1/proxy/?quest={TARGET_URL}",
    f"https://corsproxy.io/?{TARGET_URL}",
    f"https://api.allorigins.win/raw?url={TARGET_URL}"
]

def get_html():
    for proxy_url in PROXIES:
        try:
            print(f"🔄 Deneniyor: {proxy_url[:50]}...")
            response = requests.get(proxy_url, headers={"User-Agent": UA}, timeout=15)
            if response.status_code == 200 and "data-stream" in response.text:
                return response.text
        except: continue
    return None

def main():
    html = get_html()
    if not html:
        print("❌ Siteye ulaşılamadı!")
        return

    # 1. Sunucu kök adresini dinamik yakala (Örn: https://pix.xsiic.workers.dev/)
    # Sayfa içinde .workers.dev geçen ilk linki bulup kök dizini alıyoruz
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xsiic.workers.dev/"
    
    m3u = ["#EXTM3U"]
    ids = set()

    # 2. Yayınları tara
    # data-stream="..." ve data-name="..." değerlerini çekiyoruz
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    
    for stream_id, name in matches:
        clean_name = name.strip().upper()
        
        # Eğer stream_id zaten tam bir linkse (http ile başlıyorsa)
        if stream_id.startswith('http'):
            final_link = stream_id
        else:
            # Sadece rakamdan oluşuyorsa (Örn: "38") -> /hls/38.m3u8
            if stream_id.isdigit():
                final_link = f"{base_url}hls/{stream_id}.m3u8"
            # "betlivematch-38" gibi bir şeyse rakamı ayıkla -> /hls/38.m3u8
            elif "betlivematch" in stream_id.lower():
                only_id = re.sub(r'\D', '', stream_id)
                final_link = f"{base_url}hls/{only_id}.m3u8"
            # Diğer metinler için (Örn: "bein-sports-1") -> /bein-sports-1.m3u8
            else:
                final_link = f"{base_url}{stream_id}.m3u8"

        if final_link not in ids:
            m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI YAYINLAR",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            m3u.append(final_link)
            ids.add(final_link)

    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        print(f"🚀 Başarılı! {len(ids)} kanal doğru formatta (hls/cdn) kaydedildi.")
        print(f"📡 Kullanılan Base: {base_url}")
    else:
        print("❌ Yayın bulunamadı.")

if __name__ == "__main__":
    main()
