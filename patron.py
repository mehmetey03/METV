import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://hepbetspor16.cfd/",
    "X-Requested-With": "XMLHttpRequest"
}

def get_base_url():
    """Yayın sunucusunun base URL'ini al"""
    try:
        r = requests.get("https://patronsports1.cfd/domain.php", headers=HEADERS, timeout=10, verify=False)
        return r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
    except: 
        return "https://obv.d72577a9dd0ec28.sbs/"

def main():
    api_url = "https://patronsports1.cfd/matches.php"
    main_site = "https://hepbetspor16.cfd"
    base_url = get_base_url()
    
    print(f"📡 API'ye bağlanılıyor: {api_url}")
    print(f"🚀 Yayın Sunucusu: {base_url}")
    
    try:
        # API'den maç verilerini çek
        response = requests.get(api_url, headers=HEADERS, timeout=15, verify=False)
        matches = response.json()
        
        print(f"🔍 Toplam {len(matches)} maç bulundu.")
        
        m3u_list = ["#EXTM3U"]
        channel_count = 0
        
        # Maçları kanal ID'lerine göre grupla (aynı ID birden fazla maç için kullanılabiliyor)
        channels = {}
        for match in matches:
            # URL'den kanal ID'sini çıkar (/ch.html?id=patron -> patron)
            url_path = match.get('URL', '')
            channel_id = url_path.split('id=')[-1] if 'id=' in url_path else None
            
            if channel_id and channel_id not in channels:
                # Kanal için bir temsilci maç seç (ilk görülen)
                channels[channel_id] = {
                    'name': f"{match.get('HomeTeam', '')} - {match.get('AwayTeam', '')}",
                    'league': match.get('league', ''),
                    'type': match.get('type', 'football')
                }
        
        # Kanalları M3U formatında ekle
        for channel_id, info in channels.items():
            # Grup adını lig/tür bilgisine göre oluştur
            group = f"CANLI {info['type'].upper()} - {info['league']}"
            
            m3u_list.append(f'#EXTINF:-1 group-title="{group}",{info["name"]}')
            m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_list.append(f'#EXTVLCOPT:http-referrer={main_site}/')
            m3u_list.append(f'{base_url}{channel_id}/mono.m3u8')
            channel_count += 1
            
            print(f"📺 Kanal {channel_count}: {info['name']} (ID: {channel_id})")
        
        # Çıktıyı dosyaya yaz
        output_file = "karsilasmalar4.m3u"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        print(f"\n✅ İşlem tamamlandı!")
        print(f"📊 Toplam kanal: {channel_count}")
        print(f"💾 Dosya: {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"💥 API bağlantı hatası: {e}")
    except json.JSONDecodeError as e:
        print(f"💥 JSON parse hatası: {e}")
    except Exception as e:
        print(f"💥 Beklenmeyen hata: {e}")

if __name__ == "__main__":
    main()
