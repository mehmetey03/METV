import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOMAIN_API = "https://maqrizi.com/domain.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_active_info():
    base, site, html = "", "", ""
    try:
        base = requests.get(DOMAIN_API, timeout=5).json().get("baseurl", "")
    except: pass

    # Aktif Jokerbet adresini doğrula
    target_url = "https://jokerbettv177.com/"
    try:
        r = requests.get(target_url, headers={"User-Agent": UA}, timeout=5, verify=False)
        if r.status_code == 200:
            site, html = target_url, r.text
    except:
        print("⚠️ jokerbettv177.com'a ulaşılamadı, alternatifler denenebilir.")
    
    return base, site, html

def main():
    base_url, site_url, html_content = get_active_info()
    if not base_url or not html_content:
        print("❌ Veri çekilemedi.")
        return

    m3u = ["#EXTM3U"]
    processed_ids = set()

    # 1. SABİT KANALLARI ÇEK (Carousel Yapısından)
    # data-stream="id" data-name="Name" yapısını hedefler
    print("📺 Sabit kanallar işleniyor...")
    sabit_pattern = r'class="[^"]*single-channel[^"]*".*?data-stream="([^"]+)".*?data-name="([^"]+)"'
    sabit_channels = re.findall(sabit_pattern, html_content, re.DOTALL)

    for stream_id, name in sabit_channels:
        if stream_id not in processed_ids:
            m3u.append(f'#EXTINF:-1 group-title="📺 SABİT KANALLAR",{name.strip().upper()}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            processed_ids.add(stream_id)

    # 2. CANLI MAÇLARI ÇEK (Match-List Yapısından)
    print("⚽ Canlı maçlar işleniyor...")
    mac_pattern = r'class="single-match[^"]*".*?data-stream="([^"]+)".*?data-name="([^"]+)"'
    matches = re.findall(mac_pattern, html_content, re.DOTALL)

    for stream_id, name in matches:
        if stream_id not in processed_ids:
            m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{name.strip()}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            processed_ids.add(stream_id)

    # Dosyaya Yaz
    with open("jokerbet_otomatik.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    
    print("-" * 30)
    print(f"🚀 Başarılı! Toplam {len(processed_ids)} yayın listelendi.")
    print("📂 Dosya: jokerbet_otomatik.m3u8")

if __name__ == "__main__":
    main()
