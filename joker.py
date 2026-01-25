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

    # 2. Aktif Siteyi Tarama
    print("🔍 Aktif site aranıyor...")
    for i in range(170, 200):
        url = f"https://jokerbettv{i}.com/"
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=5, verify=False)
            if r.status_code == 200 and "betlivematch" in r.text:
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
    processed_streams = set()

    # 1. Önce data-stream'i kontrol et (betlivematch formatında)
    print("🔄 Canlı maçlar aranıyor...")
    
    # Regex pattern'i: data-stream="betlivematch-XXXXXXXXX" ve data-name="..."
    pattern = r'data-stream="(betlivematch[^"]+)"[^>]*?data-name="([^"]+)"'
    found = re.findall(pattern, html_content)
    
    for stream_id, name in found:
        if stream_id not in processed_streams:
            clean_name = name.strip().upper()
            group = "⚽ CANLI MAÇLAR"
            
            m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            processed_streams.add(stream_id)
            print(f"✓ Canlı Maç: {clean_name}")

    # 2. Sabit kanalları kontrol et (data-streamx ve data-stream için)
    print("🔄 Sabit kanallar aranıyor...")
    
    # Sabit kanallar için pattern (data-streamx veya data-stream)
    fixed_pattern = r'data-(?:streamx|stream)="([^"]+)"[^>]*?data-name="([^"]+)"'
    fixed_found = re.findall(fixed_pattern, html_content)
    
    for stream_data, name in fixed_found:
        clean_name = name.strip().upper()
        
        # Eğer canlı maç değilse ve henüz eklenmediyse
        if not stream_data.startswith('betlivematch') and stream_data not in processed_streams:
            group = "📺 SABİT KANALLAR"
            
            m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            
            # Stream verisini kontrol et
            if stream_data.startswith('http'):
                m3u.append(stream_data)
            elif base_url:
                m3u.append(f"{base_url}{stream_data}.m3u8")
            else:
                m3u.append(f"{stream_data}.m3u8")
                
            processed_streams.add(stream_data)
            print(f"✓ Sabit Kanal: {clean_name}")

    # 3. Gelecek maçları da ekleyelim (data-stream="xxxx-yyyy" formatında)
    print("🔄 Gelecek maçlar aranıyor...")
    
    # Gelecek maçlar için pattern (örn: data-stream="minnesota-tw-gs-warriors")
    future_pattern = r'data-stream="([a-zA-Z0-9\-]+)"[^>]*?data-name="([^"]+)"'
    future_found = re.findall(future_pattern, html_content)
    
    for stream_id, name in future_found:
        # Canlı maç değilse ve henüz eklenmediyse
        if not stream_id.startswith('betlivematch') and stream_id not in processed_streams:
            clean_name = name.strip().upper()
            group = "⏳ GELECEK MAÇLAR"
            
            m3u.append(f'#EXTINF:-1 group-title="{group}",{clean_name}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={UA}')
            m3u.append(f'#EXTVLCOPT:http-referrer={site_url}')
            m3u.append(f"{base_url}{stream_id}.m3u8")
            processed_streams.add(stream_id)
            print(f"✓ Gelecek Maç: {clean_name}")

    if len(m3u) > 1:
        with open("joker.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u))
        total_channels = (len(m3u) - 1) // 4  # Her kanal için 4 satır
        print(f"🚀 BAŞARILI: {total_channels} yayın joker.m3u8 dosyasına kaydedildi.")
        print(f"📊 Dağılım: {total_channels} kanal (canlı maçlar + sabit kanallar + gelecek maçlar)")
    else:
        print("❌ HATA: Sitede yayın bulunamadı.")
        print("ℹ️ DEBUG: HTML'de 'betlivematch' araması:")
        print("Found 'betlivematch':", "betlivematch" in html_content)
        print("Found 'data-stream':", "data-stream" in html_content)

if __name__ == "__main__":
    main()
