import requests
import urllib3
import json
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"
MATCHES_API_URL = "https://patronsports1.cfd/matches.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_referrer_from_redirect():
    """Redirect kaynağından doğru referrer adresini bul."""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15)
        # İçerikteki yönlendirme linklerini bul (genellikle href içinde)
        content = r.text
        # Örnek: <a href="https://hepsibetsiteXX.cfd/"> gibi linkleri ara
        referrers = re.findall(r'href="(https?://[^"]+\.cfd)[/"]', content)
        if referrers:
            # Bulunan ilk .cfd uzantılı siteyi referrer olarak kullan
            return referrers[0].rstrip('/')
        
        # Alternatif: Sayfa içinde geçen .cfd adreslerini bul
        domains = re.findall(r'(https?://[a-zA-Z0-9.-]+\.cfd)', content)
        if domains:
            return domains[0].rstrip('/')
            
    except Exception as e:
        print(f"⚠️ Redirect kaynağı okunamadı: {e}")
    
    # Hiçbir şey bulunamazsa varsayılan (belki domain API'sinden alınabilir)
    return "https://patronsports1.cfd"

def get_base_url():
    """Yayın sunucusunun adresini al."""
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except:
        # Hata durumunda belki redirect'ten dene
        return "https://obv.d72577a9dd0ec28.sbs/"  # Son çare

def main():
    print("🔍 Bilgiler alınıyor...")
    
    # 1. Doğru referrer adresini redirect kaynağından bul
    referrer_site = get_referrer_from_redirect()
    print(f"📡 Kullanılacak Referrer: {referrer_site}")
    
    # 2. Base URL'i al
    base_url = get_base_url()
    print(f"🚀 Yayın Sunucusu: {base_url}")
    
    # 3. Maç verilerini API'den çek
    try:
        response = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        matches = response.json()
        print(f"🔍 Toplam {len(matches)} maç kaydı bulundu.")
        
        m3u_list = ["#EXTM3U"]
        channels = {}  # Benzersiz kanalları tutmak için
        
        for match in matches:
            url_path = match.get('URL', '')
            channel_id = url_path.split('id=')[-1] if 'id=' in url_path else None
            
            if channel_id and channel_id not in channels:
                home = match.get('HomeTeam', '')
                away = match.get('AwayTeam', '')
                league = match.get('league', 'Spor')
                match_type = match.get('type', 'unknown')
                match_time = match.get('Time', '')
                
                # LOGO URL'lerini al (API'den geliyor)
                home_logo = match.get('HomeLogo', '')
                away_logo = match.get('AwayLogo', '')
                # İsteğe bağlı: Birleşik bir logo veya sadece ev sahibi logosu kullan
                logo_url = home_logo if home_logo else away_logo
                
                # Kanal adı (saat bilgisiyle)
                channel_name = f"{home} - {away} [{match_time}]"
                
                # Grup adı
                group_title = f"CANLI {match_type.upper()} - {league}"
                
                # EXTINF satırı: logo ve grup bilgisiyle
                if logo_url:
                    extinf = f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="{group_title}",{channel_name}'
                else:
                    extinf = f'#EXTINF:-1 group-title="{group_title}",{channel_name}'
                
                m3u_list.append(extinf)
                m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                # Burada BULDUĞUMUZ referrer_site kullanılıyor
                m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer_site}/')
                m3u_list.append(f'{base_url}{channel_id}/mono.m3u8')
                
                channels[channel_id] = channel_name
                print(f"📺 {channel_name} (ID: {channel_id})")
        
        # M3U dosyasını kaydet
        output_file = "karsilasmalar4.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print(f"\n✅ İşlem tamamlandı! {len(channels)} kanal {output_file} dosyasına kaydedildi.")
        
    except Exception as e:
        print(f"💥 Hata: {e}")

if __name__ == "__main__":
    main()
