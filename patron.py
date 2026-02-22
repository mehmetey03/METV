import requests
import urllib3
import json
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# SADECE VE SADECE VERİLEN KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"
MATCHES_API_URL = "https://patronsports1.cfd/matches.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_base_url_from_api():
    """Sadece domain API'sini kullanarak base URL'i al. Başarısız olursa None döndür."""
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            # Gelen baseurl'yi düzenle (sondaki slash'ı kontrol et)
            base_url = base_url.replace("\\", "").rstrip('/')
            return base_url + "/"
        else:
            print("⚠️ Domain API'si 'baseurl' döndürmedi.")
            return None
    except Exception as e:
        print(f"⚠️ Domain API'sine erişilemedi: {e}")
        return None

def get_referrer_and_logo_base_from_redirect():
    """
    Redirect kaynağından iki şeyi çıkar:
    1. Kullanılacak referrer adresi (yayının açıldığı ana site)
    2. Logoların base URL'i (resimlerin bulunduğu ana dizin)
    """
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15)
        content = r.text
        
        # 1. Referrer adresini bul (.cfd uzantılı link)
        referrer_matches = re.findall(r'href="(https?://[^"]+\.cfd)[/"]', content)
        referrer = referrer_matches[0].rstrip('/') if referrer_matches else None
        
        if not referrer:
            # Alternatif: Sayfa içinde geçen .cfd adreslerini bul
            domain_matches = re.findall(r'(https?://[a-zA-Z0-9.-]+\.cfd)', content)
            referrer = domain_matches[0].rstrip('/') if domain_matches else None
        
        # 2. Logo base URL'ini bul (genellikle img/ veya /logos/ içeren linkler)
        logo_base = None
        # Örnek: src="https://patronsports1.cfd/img/logos/..." gibi kalıpları ara
        logo_matches = re.findall(r'(https?://[^"]+)/img/logos/', content)
        if logo_matches:
            logo_base = logo_matches[0].rstrip('/')
        else:
            # Alternatif: Resim linklerinin ortak base'ini bul
            img_srcs = re.findall(r'src="(https?://[^"]+/(?:img|images|logos)/[^"]+)"', content)
            if img_srcs:
                # İlk resmin base URL'ini al
                from urllib.parse import urlparse
                parsed = urlparse(img_srcs[0])
                logo_base = f"{parsed.scheme}://{parsed.netloc}"
        
        return referrer, logo_base
        
    except Exception as e:
        print(f"⚠️ Redirect kaynağı işlenirken hata: {e}")
        return None, None

def main():
    print("🔍 Kaynaklardan bilgiler alınıyor (sabit URL kullanılmadan)...")
    
    # 1. Base URL'i sadece domain API'sinden al
    base_url = get_base_url_from_api()
    if not base_url:
        print("❌ Base URL alınamadığı için işlem durduruluyor.")
        print("   Domain API'si çalışmıyor olabilir veya 'baseurl' bilgisi eksik.")
        return
    
    # 2. Redirect kaynağından referrer ve logo base'ini al
    referrer, logo_base = get_referrer_and_logo_base_from_redirect()
    if not referrer:
        print("❌ Redirect kaynağından referrer adresi alınamadığı için işlem durduruluyor.")
        print("   'inattv.html' dosyasına erişilemiyor veya içinde .cfd linki yok.")
        return
    
    print(f"📡 Kullanılacak Referrer: {referrer}")
    print(f"🖼️ Logo Base URL (bulunursa): {logo_base}")
    print(f"🚀 Yayın Sunucusu (Domain API'den): {base_url}")
    
    # 3. Maç verilerini API'den çek
    try:
        response = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        matches = response.json()
        print(f"🔍 Maç API'sinden {len(matches)} kayıt alındı.")
        
        m3u_list = ["#EXTM3U"]
        channels = {}  # Benzersiz kanallar için
        
        for match in matches:
            # URL'den kanal ID'sini çıkar
            url_path = match.get('URL', '')
            channel_id = url_path.split('id=')[-1] if 'id=' in url_path else None
            
            if channel_id and channel_id not in channels:
                home = match.get('HomeTeam', '').strip()
                away = match.get('AwayTeam', '').strip()
                league = match.get('league', 'Spor').strip()
                match_type = match.get('type', 'football').strip()
                match_time = match.get('Time', '').strip()
                
                # Logo URL'ini oluştur (eğer logo_base varsa ve takım ismi biliniyorsa)
                logo_url = ""
                if logo_base and home:
                    # Basit bir logo URL'i tahmini (siteye göre değişir, bu örnek)
                    # Gerçek logolar matches API'sinde 'HomeLogo' ve 'AwayLogo' olabilir.
                    # Önce API'den gelen logo'yu dene:
                    api_logo = match.get('HomeLogo') or match.get('AwayLogo')
                    if api_logo and api_logo.startswith('http'):
                        logo_url = api_logo
                    else:
                        # API'de yoksa, base_url ve takım adıyla dene (Bu kısım siteye özeldir, dikkat!)
                        # Örnek: logo_base + /logos/ + takim_adi + .png
                        # Takım adını düzenle (küçük harf, boşlukları tire yap)
                        team_slug = re.sub(r'[^a-z0-9]', '', home.lower())
                        if team_slug:
                            logo_url = f"{logo_base}/img/logos/{team_slug}.png"
                
                # Kanal adı
                channel_name = f"{home} - {away}"
                if match_time:
                    channel_name += f" [{match_time}]"
                
                # Grup başlığı
                group_title = f"CANLI {match_type.upper()} - {league}"
                
                # EXTINF satırı (logo varsa ekle)
                if logo_url:
                    extinf = f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="{group_title}",{channel_name}'
                else:
                    extinf = f'#EXTINF:-1 group-title="{group_title}",{channel_name}'
                
                m3u_list.append(extinf)
                m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
                m3u_list.append(f'{base_url}{channel_id}/mono.m3u8')
                
                channels[channel_id] = channel_name
                print(f"  ➕ {channel_name} (ID: {channel_id})")
        
        # Çıktı dosyasını kaydet
        output_file = "karsilasmalar4.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print(f"\n✅ İşlem tamamlandı! {len(channels)} kanal '{output_file}' dosyasına kaydedildi.")
        
        # İsteğe bağlı: JSON yedek
        json_file = "patron_channels.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=2, ensure_ascii=False)
        print(f"📋 Kanal listesi JSON yedek: {json_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"💥 Maç API'sine bağlantı hatası: {e}")
    except json.JSONDecodeError as e:
        print(f"💥 Maç API'sinden gelen veri JSON formatında değil: {e}")
    except Exception as e:
        print(f"💥 Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
