import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
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

    # 1. Ana Sunucu Adresini Yakala
    base_match = re.search(r'(https?://[.\w-]+\.workers\.dev/)', html)
    base_url = base_match.group(1) if base_match else "https://pix.xsiic.workers.dev/"
    
    m3u = ["#EXTM3U"]
    ids = set()

    # 2. Yayınları tara (data-stream ve data-name ikilisini alır)
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    
    for stream_id, name in matches:
        clean_name = name.strip().upper()
        
        # Gereksiz "betlivematch-" ön ekini temizle ama geri kalan metne dokunma
        stream_path = stream_id.replace('betlivematch-', '')
        
        # Link oluşturma: 
        # Eğer stream_path zaten tam bir linkse olduğu gibi al
        # Değilse, base_url + stream_path + .m3u8 yap
        if stream_path.startswith('http'):
            final_link = stream_path
        else:
            # /hls/ veya ek takıları kaldırıp doğrudan kök dizine ekliyoruz
            final_link = f"{base_url}{stream_path}.m3u8"

        if final_link not in ids:
            m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI YAYINLAR",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            m3u.append(final_link)
            ids.add(final_link)

    # 3. Dosyaya Yaz
    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        print(f"✅ BAŞARILI! {len(ids)} kanal kaydedildi.")
        print(f"🔗 Örnek Link: {m3u[4] if len(m3u)>4 else 'Yok'}")
    else:
        print("❌ Yayın bulunamadı.")

if __name__ == "__main__":
    main()
