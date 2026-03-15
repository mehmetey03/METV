import re
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
TARGET_URL = "https://27intersportv.us"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Sabit Kanallar Listesi
SABIT_KANALLAR = [
    ("beIN SPORTS HD1", "bein-sports-1.m3u8"),
    ("beIN SPORTS HD2", "bein-sports-2.m3u8"),
    ("beIN SPORTS HD3", "bein-sports-3.m3u8"),
    ("beIN SPORTS HD4", "bein-sports-4.m3u8"),
    ("beIN SPORTS HD5", "bein-sports-5.m3u8"),
    ("beIN SPORTS MAX 1", "bein-sports-max-1.m3u8"),
    ("beIN SPORTS MAX 2", "bein-sports-max-2.m3u8"),
    ("S SPORT", "s-sport.m3u8"),
    ("S SPORT 2", "s-sport-2.m3u8"),
    ("TIVIBUSPOR 1", "tivibu-spor.m3u8"),
    ("TIVIBUSPOR 2", "tivibu-spor-2.m3u8"),
    ("TIVIBUSPOR 3", "tivibu-spor-3.m3u8"),
    ("TIVIBUSPOR 4", "tivibu-spor-4.m3u8"),
    ("spor SMART", "spor-smart.m3u8"),
    ("spor SMART 2", "spor-smart-2.m3u8"),
    ("TRT SPOR", "trt-spor.m3u8"),
    ("TRT SPOR 2", "trt-spor-yildiz.m3u8"),
    ("TRT 1", "trt-1.m3u8"),
    ("ASPOR", "a-spor.m3u8"),
    ("TABİİ SPOR", "tabii-spor.m3u8"),
    ("TABİİ SPOR 1", "tabii-spor-1.m3u8"),
    ("TABİİ SPOR 2", "tabii-spor-2.m3u8"),
    ("TABİİ SPOR 3", "tabii-spor-3.m3u8"),
    ("TABİİ SPOR 4", "tabii-spor-4.m3u8"),
    ("TABİİ SPOR 5", "tabii-spor-5.m3u8"),
    ("TABİİ SPOR 6", "tabii-spor-6.m3u8"),
    ("ATV", "atv.m3u8"),
    ("TV 8.5", "tv8.5.m3u8")
]

def get_html():
    # GitHub engellerini aşmak için farklı proxy servisleri
    proxies = [
        f"https://api.allorigins.win/get?url={TARGET_URL}",
        f"https://api.codetabs.com/v1/proxy/?quest={TARGET_URL}",
        f"https://thingproxy.freeboard.io/fetch/{TARGET_URL}"
    ]
    
    for url in proxies:
        try:
            print(f"🔄 Bağlanıyor: {url[:50]}...")
            res = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            if res.status_code == 200:
                # Allorigins JSON formatında döner, diğerleri direkt text
                if "allorigins" in url:
                    return res.json().get('contents', '')
                return res.text
        except Exception as e:
            print(f"⚠️ Proxy hatası ({url[:25]}): {e}")
            continue
    return None

def main():
    html = get_html()
    if not html:
        print("❌ Site içeriği alınamadı. Proxy servisleri yanıt vermiyor olabilir.")
        return

    # 1. GÜNCEL SUNUCUYU TESPİT ET (Meta etiketinden)
    # <meta name="fbd" content="https://pix.xmlx.workers.dev/hls">
    base_match = re.search(r'meta name="fbd" content="([^"]+)"', html)
    if base_match:
        base_url = base_match.group(1).split('/hls')[0] + "/"
    else:
        # Alternatif: Script içindeki dns-prefetch üzerinden bul
        base_match = re.search(r'https?://[.\w-]+\.workers\.dev', html)
        base_url = base_match.group(0) + "/" if base_match else "https://pix.xmlx.workers.dev/"
    
    print(f"📡 Yayın Sunucusu: {base_url}")

    m3u = ["#EXTM3U"]

    # 2. SABİT KANALLARI EKLE
    for name, file in SABIT_KANALLAR:
        m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name}')
        m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
        m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}/')
        m3u.append(f"{base_url}{file}")

    # 3. CANLI MAÇLARI EKLE (data-streamx ve data-name üzerinden)
    # Yeni yapıda linkler data-streamx="https://.../mac.m3u8" şeklinde tam URL olabiliyor
    matches = re.findall(r'data-streamx="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    
    added_streams = []
    for stream_url, name in matches:
        clean_name = name.strip().upper()
        if clean_name in added_streams: continue # Tekrar edenleri engelle
        
        # URL'yi temizle ve gerekirse base_url ekle
        final_link = stream_url if stream_url.startswith('http') else f"{base_url}{stream_url}"
        
        m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{clean_name}')
        m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
        m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}/')
        m3u.append(final_link)
        added_streams.append(clean_name)

    # 4. KAYDET
    with open("joker.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    
    print(f"🚀 Başarılı! {len(added_streams)} canlı maç ve sabit kanallar joker.m3u8 dosyasına yazıldı.")

if __name__ == "__main__":
    main()
