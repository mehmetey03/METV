import requests
import re
import json
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AdvancedMonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        
    def get_active_domain(self):
        """Aktif domain'i bul"""
        print("🔍 Aktif giriş adresi taranıyor...")
        domains_to_try = [
            "https://monotv.com",
            "https://www.monotv.com",
            "https://monotv.net",
            "https://www.monotv.net",
            "https://monotv.org",
            "https://www.monotv.org",
        ]
        
        # Ayrıca numaralı domain'leri de dene
        for sayi in range(530, 600):
            domains_to_try.append(f"https://monotv{sayi}.com")
        
        for domain in domains_to_try:
            try:
                r = self.session.get(domain, timeout=5, verify=False, headers=self.headers)
                if r.status_code == 200 and "player-channel-area" in r.text:
                    print(f"✅ Aktif site bulundu: {domain}")
                    return domain.rstrip('/')
            except:
                continue
        
        print("❌ Aktif site bulunamadı")
        return None
    
    def extract_channel_info_from_html(self, html_content):
        """HTML içeriğinden kanal bilgilerini çıkar"""
        soup = BeautifulSoup(html_content, 'html.parser')
        channels = []
        
        # "Maçlar" sekmesindeki kanalları bul
        matches_section = soup.find('div', {'id': 'matches-content'})
        if matches_section:
            match_links = matches_section.find_all('a', class_='single-match')
            for link in match_links:
                if 'show' in link.get('class', []):
                    href = link.get('href', '')
                    match = re.search(r'channel\?id=([^&"\']+)', href)
                    if match:
                        channel_id = match.group(1)
                        # Kanal adını bul
                        home_div = link.find('div', class_='home')
                        channel_name = home_div.text.strip() if home_div else channel_id.upper()
                        
                        # Spor türünü bul
                        date_div = link.find('div', class_='date')
                        sport_type = date_div.text.strip() if date_div else "Spor"
                        
                        channels.append({
                            'id': channel_id,
                            'name': channel_name,
                            'sport': sport_type,
                            'type': 'match',
                            'url': href
                        })
        
        # "Kanallar" sekmesindeki kanalları bul
        channels_section = soup.find('div', {'id': 'channels-content'})
        if channels_section:
            channel_links = channels_section.find_all('a', class_='single-match')
            for link in channel_links:
                if 'show' in link.get('class', []):
                    href = link.get('href', '')
                    match = re.search(r'channel\?id=([^&"\']+)', href)
                    if match:
                        channel_id = match.group(1)
                        # Kanal adını bul
                        home_div = link.find('div', class_='home')
                        channel_name = home_div.text.strip() if home_div else channel_id.upper()
                        
                        channels.append({
                            'id': channel_id,
                            'name': channel_name,
                            'sport': '7/24',
                            'type': 'channel',
                            'url': href
                        })
        
        return channels
    
    def extract_m3u8_urls(self, base_url, channel_ids):
        """Kanal ID'lerinden m3u8 URL'lerini oluştur"""
        m3u8_urls = []
        for channel in channel_ids:
            # Farklı URL formatlarını dene
            urls_to_try = [
                f"{base_url}{channel['id']}/mono.m3u8",
                f"{base_url}live/{channel['id']}/mono.m3u8",
                f"{base_url}stream/{channel['id']}/mono.m3u8",
                f"{base_url}hls/{channel['id']}/mono.m3u8"
            ]
            
            for url in urls_to_try:
                try:
                    test_r = self.session.head(url, timeout=3, verify=False)
                    if test_r.status_code == 200:
                        channel['m3u8_url'] = url
                        m3u8_urls.append(channel)
                        print(f"✅ {channel['name']} - m3u8 bulundu")
                        break
                except:
                    continue
        
        return m3u8_urls
    
    def create_m3u_playlist(self, channels, output_file="mono_channels.m3u"):
        """M3U playlist oluştur"""
        if not channels:
            print("❌ Kanal bulunamadı")
            return
        
        m3u_content = ["#EXTM3U"]
        
        for channel in channels:
            if 'm3u8_url' in channel:
                # Grup başlığını belirle
                group_title = "MonoTV"
                if channel['type'] == 'match':
                    group_title = f"MonoTV Maçlar - {channel['sport']}"
                else:
                    group_title = "MonoTV Kanallar"
                
                # EXTINF satırı
                extinf = f'#EXTINF:-1 group-title="{group_title}",{channel["name"]}'
                m3u_content.append(extinf)
                
                # Referrer opsiyonu
                m3u_content.append(f'#EXTVLCOPT:http-referrer={channel.get("site_url", "https://monotv.com")}/')
                
                # m3u8 URL'si
                m3u_content.append(channel['m3u8_url'])
        
        # Dosyaya yaz
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        
        print(f"✅ {len(channels)} kanal bulundu ve '{output_file}' dosyasına kaydedildi.")
        
        # Ayrıca JSON formatında da kaydet
        with open("mono_channels.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
        print(f"📊 Kanal bilgileri 'mono_channels.json' dosyasına kaydedildi.")
    
    def find_m3u8_server(self, html_content):
        """HTML içeriğinde m3u8 sunucusu ara"""
        patterns = [
            r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6}/[^"\']*?/mono\.m3u8)',
            r'["\'](https?://[a-z0-9.-]+\.[a-z]{2,6}/[^"\']*?\.m3u8)',
            r'src:\s*["\'](https?://[^"\']+/[^"\']+\.m3u8)',
            r'["\'](https?://[^"\']+/live/[^"\']+\.m3u8)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # URL'yi temizle
                url = match.replace('\\/', '/')
                # Sadece domain ve path'i al
                server_match = re.match(r'(https?://[^/]+)/', url)
                if server_match:
                    server = server_match.group(1) + "/"
                    print(f"🔍 Sunucu bulundu: {server}")
                    return server
        
        # Varsayılan sunucular
        default_servers = [
            "https://rei.zirvedesin201.cfd/",
            "https://tv.zirvesin.tv/",
            "https://tv.eyvah.tv/",
            "https://tv.monospo.com/"
        ]
        
        for server in default_servers:
            try:
                test_url = f"{server}zirve/mono.m3u8"
                r = self.session.head(test_url, timeout=3, verify=False)
                if r.status_code == 200:
                    print(f"✅ Sunucu testi başarılı: {server}")
                    return server
            except:
                continue
        
        print("⚠️ Sunucu bulunamadı, varsayılan kullanılıyor")
        return "https://rei.zirvedesin201.cfd/"
    
    def scrape(self):
        """Ana scraping fonksiyonu"""
        print("🚀 MonoTV Scraper Başlıyor...")
        
        # 1. Aktif domain'i bul
        domain = self.get_active_domain()
        if not domain:
            return
        
        # 2. Site içeriğini al
        try:
            print("📥 Site içeriği alınıyor...")
            response = self.session.get(domain, headers=self.headers, timeout=10, verify=False)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            print(f"❌ Site içeriği alınamadı: {e}")
            return
        
        # 3. Kanal bilgilerini çıkar
        print("🔍 Kanal bilgileri çıkarılıyor...")
        channels = self.extract_channel_info_from_html(html_content)
        
        if not channels:
            print("⚠️ HTML'den kanal bulunamadı, alternatif yöntem deneniyor...")
            # Alternatif: Regex ile tüm channel?id= değerlerini bul
            all_ids = re.findall(r'channel\?id=([a-zA-Z0-9_-]+)', html_content)
            unique_ids = list(dict.fromkeys(all_ids))
            
            for channel_id in unique_ids:
                # Gereksiz ID'leri filtrele
                if len(channel_id) < 2 or channel_id in ['google', 'facebook', 'twitter', 'analytics']:
                    continue
                
                channels.append({
                    'id': channel_id,
                    'name': channel_id.upper(),
                    'sport': 'Bilinmiyor',
                    'type': 'unknown',
                    'url': f"channel?id={channel_id}"
                })
        
        print(f"📊 {len(channels)} kanal bulundu")
        
        # 4. m3u8 sunucusunu bul
        print("🌐 m3u8 sunucusu aranıyor...")
        m3u8_server = self.find_m3u8_server(html_content)
        
        # 5. m3u8 URL'lerini test et ve oluştur
        print("🔗 m3u8 URL'leri test ediliyor...")
        valid_channels = self.extract_m3u8_urls(m3u8_server, channels)
        
        # 6. Site URL'sini kanallara ekle
        for channel in valid_channels:
            channel['site_url'] = domain
        
        # 7. M3U playlist oluştur
        self.create_m3u_playlist(valid_channels)
        
        # 8. Özet bilgileri göster
        print("\n" + "="*50)
        print("📊 ÖZET BİLGİLER")
        print("="*50)
        print(f"Aktif Site: {domain}")
        print(f"m3u8 Sunucusu: {m3u8_server}")
        print(f"Toplam Kanal: {len(channels)}")
        print(f"Çalışan m3u8 URL: {len(valid_channels)}")
        
        # Kategori bazlı sayıları göster
        match_count = sum(1 for c in valid_channels if c['type'] == 'match')
        channel_count = sum(1 for c in valid_channels if c['type'] == 'channel')
        print(f"- Maç Kanalları: {match_count}")
        print(f"- 7/24 Kanallar: {channel_count}")
        
        # İlk 5 kanalı göster
        print("\n📺 ÖRNEK KANALLAR:")
        for i, channel in enumerate(valid_channels[:5], 1):
            print(f"{i}. {channel['name']} - {channel['id']}")

def main():
    """Ana çalıştırma fonksiyonu"""
    try:
        scraper = AdvancedMonoScraper()
        scraper.scrape()
    except KeyboardInterrupt:
        print("\n⏹️ Program kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
