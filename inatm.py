import requests
import re
import sys
from bs4 import BeautifulSoup

def main():
    try:
        # Domain aralığı
        active_domain = None
        print("🔍 Aktif domain aranıyor...")
        
        for i in range(1212, 2000):
            url = f"https://inattv{i}.xyz/"
            try:
                r = requests.head(url, timeout=5)
                if r.status_code == 200:
                    active_domain = url
                    print(f"✅ Aktif domain bulundu: {active_domain}")
                    break
            except Exception as e:
                continue
        
        if not active_domain:
            print("⚠️  Aktif domain bulunamadı. Boş M3U dosyası oluşturuluyor...")
            return 0
        
        # Base URL çek
        print("🔗 Base URL alınıyor...")
        try:
            # Ana sayfadan ilk kanal ID'sini bul
            main_html = requests.get(active_domain, timeout=10).text
            m = re.search(r'<iframe[^>]+id="customIframe"[^>]+src="/channel.html\?id=([^"]+)"', main_html)
            
            if not m:
                print("⚠️  İlk kanal ID bulunamadı. Boş M3U dosyası oluşturuluyor...")
                return 0
            
            first_id = m.group(1)
            
            # Base URL'i al
            channel_url = active_domain + "channel.html?id=" + first_id
            channel_html = requests.get(channel_url, timeout=10).text
            
            b = re.search(r'const\s+BASE_URL\s*=\s*"([^"]+)"', channel_html)
            
            if not b:
                print("⚠️  Base URL bulunamadı. Boş M3U dosyası oluşturuluyor...")
                return 0
            
            base_url = b.group(1)
            print(f"✅ Base URL bulundu: {base_url}")
            
        except Exception as e:
            print(f"⚠️  Base URL alınırken hata: {str(e)}")
            return 0
        
        # Ana sayfadan dinamik kanal listesi çek
        print("📡 Dinamik kanal listesi alınıyor...")
        try:
            response = requests.get(active_domain, timeout=10)
            response.encoding = 'utf-8'  # veya 'iso-8859-9' (Türkçe için)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # matches-tab class'ı altındaki tüm a elementlerini bul
            matches_tab = soup.find(id='matches-tab')
            
            if not matches_tab:
                print("⚠️  matches-tab bulunamadı. Boş M3U dosyası oluşturuluyor...")
                return 0
            
            channel_links = matches_tab.find_all('a', href=re.compile(r'/channel\.html\?id='))
            
            if not channel_links:
                print("⚠️  Kanal linki bulunamadı. Boş M3U dosyası oluşturuluyor...")
                return 0
            
            channels = []
            for link in channel_links:
                # href'den id'yi çıkar
                href = link.get('href', '')
                id_match = re.search(r'id=([^&]+)', href)
                
                if not id_match:
                    continue
                
                cid = id_match.group(1)
                
                # Kanal adını ve saati al
                channel_name_elem = link.find(class_='channel-name')
                channel_status_elem = link.find(class_='channel-status')
                
                if not channel_name_elem or not channel_status_elem:
                    continue
                
                # İsimden ikon kısmını temizle
                channel_name = channel_name_elem.get_text(strip=True)
                channel_time = channel_status_elem.get_text(strip=True)
                
                # Format: "01:00 | Miami Heat - Minnesota"
                display_name = f"{channel_time} | {channel_name}"
                
                channels.append({
                    'cid': cid,
                    'name': display_name
                })
            
            print(f"✅ {len(channels)} kanal bulundu")
            
        except Exception as e:
            print(f"⚠️  Kanal listesi alınırken hata: {str(e)}")
            return 0
        
        # M3U dosyası oluştur
        print("📝 M3U dosyası oluşturuluyor...")
        lines = []
        
        for channel in channels:
            cid = channel['cid']
            name = channel['name']
            
            # EXTM3U satırını oluştur
            lines.append(f'#EXTINF:-1 group-title="Maç Yayınları" ,{name}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            
            # URL satırını oluştur
            full_url = f"{base_url}{cid}.m3u8"
            lines.append(full_url)
        
        with open("karsilasmalar.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"✅ karsilasmalar.m3u başarıyla oluşturuldu ({len(channels)} kanal)")
        return 0
        
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
