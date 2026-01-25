import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
TARGET_URL = "https://jokerbettv177.com/"
DOMAIN_API = "https://maqrizi.com/domain.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Senin verdiğin proxy listesi
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
                print("✅ Veri başarıyla çekildi!")
                return response.text
        except Exception as e:
            print(f"⚠️ Bu proxy başarısız oldu: {e}")
            continue
    return None

def main():
    # 1. Base URL Al
    base_url = ""
    try:
        base_url = requests.get(DOMAIN_API, timeout=10).json().get("baseurl", "")
    except: pass

    # 2. Proxy üzerinden HTML al
    html = get_html()
    
    if not html:
        print("❌ Hiçbir proxy ile siteye ulaşılamadı!")
        return

    m3u = ["#EXTM3U"]
    ids = set()

    # Worker (StreamX) Linkleri
    worker_matches = re.findall(r'data-streamx="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    for link, name in worker_matches:
        if link not in ids:
            m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name.strip().upper()}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            m3u.append(link)
            ids.add(link)

    # Normal Maç Linkleri
    normal_matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    for stream_id, name in normal_matches:
        if stream_id not in ids:
            clean_name = name.strip().upper()
            group = "⚽ CANLI MAÇLAR" if "-" in clean_name else "📺 SABİT KANALLAR"
            m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            ids.add(stream_id)

    # 3. Yazdır
    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        print(f"🚀 Başarılı! {len(ids)} yayın kaydedildi.")
    else:
        print("❌ Yayın bulunamadı.")

if __name__ == "__main__":
    main()
