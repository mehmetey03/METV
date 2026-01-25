import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
TARGET_URL = "https://jokerbettv177.com/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def get_html():
    # En stabil proxy yöntemini kullanıyoruz
    proxy_url = f"https://api.allorigins.win/raw?url={TARGET_URL}"
    try:
        response = requests.get(proxy_url, headers={"User-Agent": UA}, timeout=15)
        return response.text if response.status_code == 200 else None
    except:
        return None

def main():
    html = get_html()
    if not html:
        print("❌ Siteye bağlanılamadı.")
        return

    # 1. Sitedeki TÜM .m3u8 linklerini ve sunucuları bir kerede bul
    # Bu yöntem pix.xsiic... değişse bile yenisini otomatik yakalar.
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
        
        # 3. Gerçek linkler havuzunda bu kanalın ID'sini ara
        # Eğer s-sports-1 geçiyorsa ama havuzda s-sport.m3u8 varsa, DOĞRU OLANI seçer.
        for link in all_links:
            # S Sport 1 için 's-sport' araması gibi...
            short_id = pure_id.replace('-1', '').replace('-2', '').replace('s-sports', 's-sport')
            if short_id in link.lower():
                found_link = link
                break
        
        # Eğer havuzda bulamazsa, en azından yakaladığımız ilk sunucu adresiyle birleştir
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
        print(f"✅ Bitti! {len(added_links)} yayın güncel sunucuyla kaydedildi.")
    else:
        print("❌ Yayın bulunamadı.")

if __name__ == "__main__":
    main()
