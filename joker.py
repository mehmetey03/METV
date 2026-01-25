import requests
import re
import urllib3

# SSL sertifika hatalarını görmezden gel
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DOMAIN_API = "https://maqrizi.com/domain.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_data():
    base, site, html = "", "", ""
    # Yayın sunucusunu al
    try:
        base = requests.get(DOMAIN_API, timeout=5).json().get("baseurl", "")
    except: pass

    # Güncel siteyi bul (177 ve sonrasını tarar)
    for i in range(177, 190):
        url = f"https://jokerbettv{i}.com/"
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=3, verify=False)
            if r.status_code == 200:
                site, html = url, r.text
                break
        except: continue
    return base, site, html

def main():
    base_url, site_url, html_content = get_data()
    if not base_url or not html_content:
        print("Veri çekilemedi!")
        return

    m3u = ["#EXTM3U"]
    processed_ids = set()

    # Regex: Hem kanalları hem maçları data-stream üzerinden yakalar
    # Jokerbet'in hem carousel hem de liste yapısına uyumludur
    found = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html_content, re.DOTALL)

    for stream_id, name in found:
        if stream_id not in processed_ids:
            clean_name = name.strip()
            # Basit gruplandırma: içinde tire varsa maçtır
            group = "⚽ CANLI MAÇLAR" if "-" in clean_name else "📺 SABİT KANALLAR"
            
            m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name.upper()}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            processed_ids.add(stream_id)

    # DOSYA ADI: joker.m3u8 (YAML ile uyumlu)
    with open("joker.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    print(f"Bitti! {len(processed_ids)} yayın joker.m3u8 dosyasına yazıldı.")

if __name__ == "__main__":
    main()
