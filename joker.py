import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Bu API bazen yavaş cevap verebilir, timeout'u artırdık
DOMAIN_API = "https://maqrizi.com/domain.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_data():
    base, site, html = "", "", ""
    
    # 1. Base URL Çekme
    try:
        response = requests.get(DOMAIN_API, timeout=10)
        base = response.json().get("baseurl", "")
        print(f"📡 API'den gelen sunucu: {base}")
    except Exception as e:
        print(f"⚠️ API Hatası: {e}")

    # 2. Aktif Siteyi Tarama (Aralığı 170-199 yaptık)
    print("🔍 Aktif site aranıyor...")
    for i in range(170, 200):
        url = f"https://jokerbettv{i}.com/"
        try:
            # Sitenin gerçekten ayakta olduğunu kontrol et
            r = requests.get(url, headers={"User-Agent": UA}, timeout=5, verify=False)
            if r.status_code == 200 and "data-stream" in r.text:
                site, html = url, r.text
                print(f"✅ Aktif Site Bulundu: {url}")
                break
        except:
            continue
    
    return base, site, html

def main():
    base_url, site_url, html_content = get_data()
    
    # Eğer site bulunamazsa boş dosya oluşturma hatasını engellemek için kontrol
    if not html_content:
        print("❌ HATA: Hiçbir aktif Jokerbet sitesine ulaşılamadı!")
        return

    m3u = ["#EXTM3U"]
    processed_ids = set()

    # Regex ile veri çekme
    found = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html_content, re.DOTALL)

    for stream_id, name in found:
        if stream_id not in processed_ids:
            clean_name = name.strip().upper()
            group = "⚽ CANLI MAÇLAR" if "-" in clean_name else "📺 SABİT KANALLAR"
            
            m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            processed_ids.add(stream_id)

    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        print(f"🚀 BAŞARILI: {len(processed_ids)} yayın joker.m3u8 dosyasına kaydedildi.")
    else:
        print("❌ HATA: Sitede yayın bulunamadı.")

if __name__ == "__main__":
    main()
