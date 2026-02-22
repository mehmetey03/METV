import requests
import urllib3
import json
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SADECE VERİLEN KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"
MATCHES_API_URL = "https://patronsports1.cfd/matches.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

def get_base_url():
    """Domain API'sinden base URL'i al"""
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        base_url = r.json().get("baseurl", "").replace("\\", "").rstrip('/')
        # Eğer base_url boşsa, redirect'ten almaya çalış
        if not base_url:
            return extract_base_from_redirect()
        return base_url + "/"  # Sonuna slash ekle
    except:
        return extract_base_from_redirect()

def extract_base_from_redirect():
    """Redirect kaynağından base URL'i çıkar (manuel yöntem)"""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
        # İçerikteki URL'leri bulmaya çalış
        content = r.text
        # Örnek: obv.xxx.sbs gibi domainleri bul
        domains = re.findall(r'https?://([^/]+\.sbs)', content)
        if domains:
            return f"https://{domains[0]}/"
        return None
    except:
        return None

def get_main_site_from_redirect():
    """Redirect kaynağından ana site URL'ini al"""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
        content = r.text
        # HTML içindeki yönlendirme linklerini bul
        # Genellikle <a href="https://site.com"> şeklinde olur
        sites = re.findall(r'href="(https?://[^"]+)"', content)
        # İçinde .cfd geçenleri filtrele
        for site in sites:
            if '.cfd' in site:
                return site.rstrip('/')
        return None
    except:
        return None

def main():
    print("🔍 Kaynaklardan bilgiler alınıyor...")
    
    # Base URL'i al
    base_url = get_base_url()
    if not base_url:
        print("❌ Base URL alınamadı!")
        return
    
    # Ana siteyi redirect'ten al
    main_site = get_main_site_from_redirect()
    if not main_site:
        print("⚠️ Ana site bulunamadı, varsayılan referer kullanılacak")
        main_site = "https://patronsports1.cfd"  # Son çare
    
    print(f"📡 Ana Site: {main_site}")
    print(f"🚀 Yayın Sunucusu: {base_url}")
    
    try:
        # Maç listesini API'den çek
        print(f"\n📡 Maç API'sine bağlanılıyor: {MATCHES_API_URL}")
        response = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15, verify=False)
        matches = response.json()
        
        print(f"🔍 Toplam {len(matches)} maç bulundu.")
        
        m3u_list = ["#EXTM3U"]
        channels = {}  # Benzersiz kanalları tut
        
        for match in matches:
            # URL'den kanal ID'sini çıkar
            url_path = match.get('URL', '')
            channel_id = url_path.split('id=')[-1] if 'id=' in url_path else None
            
            if channel_id and channel_id not in channels:
                # Yeni kanal ekle
                home = match.get('HomeTeam', '')
                away = match.get('AwayTeam', '')
                league = match.get('league', '')
                match_type = match.get('type', 'football')
                match_time = match.get('Time', '')
                
                # Kanal adını oluştur (saat bilgisiyle)
                channel_name = f"{home} - {away} [{match_time}]"
                
                channels[channel_id] = {
                    'name': channel_name,
                    'league': league,
                    'type': match_type
                }
                
                # M3U satırlarını ekle
                group = f"CANLI {match_type.upper()} - {league}"
                m3u_list.append(f'#EXTINF:-1 group-title="{group}",{channel_name}')
                m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_list.append(f'#EXTVLCOPT:http-referrer={main_site}/')
                m3u_list.append(f'{base_url}{channel_id}/mono.m3u8')
                
                print(f"📺 Kanal {len(channels)}: {channel_name} (ID: {channel_id})")
        
        # Çıktıyı dosyaya yaz
        output_file = "patron_playlist.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print(f"\n✅ İşlem tamamlandı!")
        print(f"📊 Toplam kanal: {len(channels)}")
        print(f"💾 Dosya: {output_file}")
        
        # İsteğe bağlı: JSON formatında da kaydet
        json_file = "patron_channels.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=2, ensure_ascii=False)
        print(f"📋 Kanal listesi JSON olarak da kaydedildi: {json_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"💥 API bağlantı hatası: {e}")
    except json.JSONDecodeError as e:
        print(f"💥 JSON parse hatası: {e}")
        print(f"📄 Alınan içerik: {response.text[:200]}...")
    except Exception as e:
        print(f"💥 Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
