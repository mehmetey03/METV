import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
TARGET_URL = "https://jokerbettv177.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_html():
    # Farklı proxy servisleri üzerinden deneme yapıyoruz
    proxies = [
        f"https://api.allorigins.win/raw?url={TARGET_URL}",
        f"https://corsproxy.io/?{TARGET_URL}",
        f"https://api.codetabs.com/v1/proxy/?quest={TARGET_URL}"
    ]
    
    for url in proxies:
        try:
            print(f"🔄 Bağlantı deneniyor: {url[:45]}...")
            response = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            if response.status_code == 200 and "data-stream" in response.text:
                print("✅ Bağlantı başarılı!")
                return response.text
        except Exception as e:
            continue
    return None

def main():
    html = get_html()
    if not html:
        print("❌ HATA: Siteye ulaşılamadı. Proxy servisleri şu an kapalı olabilir veya site adresini kontrol etmelisin.")
        return

    # 1. SUNUCUYU VE TÜM LİNKLERİ SİTEDEN ÇEK (Örn: pix.xsiic... değişse bile yakalar)
    # Sayfa içindeki gizli tüm m3u8 yollarını bulur
    all_links = re.findall(r'https?://[.\w-]+\.workers\.dev/[^"\']+\.m3u8', html)
    
    # 2. Kanal isimlerini ve stream ID'lerini bul
    matches = re.findall(r'data-stream="([^"]+)".*?data-name="([^"]+)"', html, re.DOTALL)
    
    m3u = ["#EXTM3U"]
    added_links = set()

    for stream_id, name in matches:
        clean_name = name.strip().upper()
        # betlivematch-s-sports-1 -> s-sports-1
        pure_id = stream_id.replace('betlivematch-', '')
        
        found_link = None
        
        # 3. DOĞRUYU BUL: 's-sports-1' gibi hatalı ID'yi, 's-sport.m3u8' gibi gerçek linkle eşleştir
        # 's-sports' içindeki takıları temizleyip havuzda arıyoruz
        match_key = pure_id.replace('s-sports', 's-sport').replace('-1', '').replace('-2', '')
        
        for link in all_links:
            if match_key in link.lower():
                found_link = link
                break
        
        # Havuzda bulunamazsa, ilk bulduğumuz sunucu köküyle zorla oluştur
        if not found_link and all_links:
            base_server = all_links[0].split('.dev/')[0] + ".dev/"
            found_link = f"{base_server}{pure_id}.m3u8"

        if found_link and found_link not in added_links:
            m3u.append(f'#EXTINF:-1 group-title="⚽ CANLI YAYINLAR",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={TARGET_URL}')
            m3u.append(found_link)
            added_links.add(found_link)

    # 4. Kaydet
    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        print(f"🚀 BAŞARILI! {len(added_links)} adet güncel kanal kaydedildi.")
    else:
        print("❌ HATA: Sayfa yüklendi ama içinde yayın linki bulunamadı.")

if __name__ == "__main__":
    main()
