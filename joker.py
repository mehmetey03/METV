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

def find_dynamic_base(html):
    """
    Sayfa içerisinden aktif sunucu adresini (TRUE_BASE) bulmaya çalışır.
    """
    # 1. Yöntem: Script içindeki değişkenleri ara (Yaygın kullanılan patternler)
    found = re.search(r'["\'](https?://[.\w-]+\.workers\.dev/cdn/)["\']', html)
    if found:
        return found.group(1)
    
    # 2. Yöntem: data-server veya benzeri bir yerden çek
    found_alt = re.search(r'https?://[.\w-]+\.workers\.dev/[^"\']+', html)
    if found_alt:
        # Eğer /cdn/ yoksa sonuna ekle
        base = found_alt.group(0)
        return base if base.endswith('/') else base + '/'

    # Bulamazsa senin verdiğin varsayılanı döndür
    return "https://pix.xsiic.workers.dev/cdn/"

def main():
    html = get_html()
    if not html:
        print("❌ Siteye ulaşılamadı!")
        return

    # SUNUCU ADRESİNİ DİNAMİK OLARAK ÇEK
    dynamic_base = find_dynamic_base(html)
    print(f"📡 Tespit Edilen Sunucu: {dynamic_base}")

    m3u = ["#EXTM3U"]
    ids = set()

    # 1. CANLI MAÇLAR
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    
    for stream_id, name in matches:
        clean_name = name.strip().upper()
        # ID içindeki sadece rakamları ayıkla
        only_id = re.sub(r'\D', '', stream_id)
        
        if only_id and only_id not in ids:
            m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            # Dinamik olarak bulunan base ile birleştir
            m3u.append(f"{dynamic_base}{only_id}.m3u8")
            ids.add(only_id)

    # 2. SABİT KANALLAR
    worker_matches = re.findall(r'data-streamx="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    for link, name in worker_matches:
        clean_name = name.strip().upper()
        if clean_name not in ids:
            m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            m3u.append(link)
            ids.add(clean_name)

    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        print(f"🚀 BAŞARILI! {len(ids)} yayın dinamik sunucuyla kaydedildi.")
    else:
        print("❌ Yayın bulunamadı.")

if __name__ == "__main__":
    main()
