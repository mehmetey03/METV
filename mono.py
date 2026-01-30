import requests
import re
import json
import urllib3
import time
from urllib.parse import urljoin

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimpleMonoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        
    def get_active_domain(self):
        """Aktif domain'i bul"""
        print("🔍 Aktif site aranıyor...")
        
        # Öncelikle bilinen domain'leri dene
        domains = [
            "https://monotv530.com",
            "https://monotv531.com",
            "https://monotv532.com",
            "https://monotv.com",
            "https://monotv.net",
        ]
        
        for domain in domains:
            try:
                print(f"  Testing: {domain}")
                r = self.session.get(domain, timeout=5, verify=False, headers=self.headers)
                if r.status_code == 200:
                    # Site içeriğinde kanal olup olmadığını kontrol et
                    if any(x in r.text for x in ['single-match', 'channel?id=', 'player-channel-area']):
                        print(f"✅ Aktif site bulundu: {domain}")
                        return domain.rstrip('/')
            except Exception as e:
                print(f"  ❌ {domain}: {str(e)[:50]}")
                continue
        
        print("❌ Aktif site bulunamadı")
        return None
    
    def extract_channels_direct(self, html_content):
        """Doğrudan regex ile kanalları çıkar"""
        print("🔍 Regex ile kanal ID'leri çıkarılıyor...")
        
        channels = []
        
        # Pattern 1: href="channel?id=XXX"
        pattern1 = r'href=["\']channel\?id=([a-zA-Z0-9_-]+)["\']'
        matches1 = re.findall(pattern1, html_content)
        
        # Pattern 2: data-matchtype ile birlikte
        pattern2 = r'data-matchtype=["\'][^"\']*["\'].*?href=["\']channel\?id=([a-zA-Z0-9_-]+)["\']'
        matches2 = re.findall(pattern2, html_content, re.DOTALL)
        
        # Pattern 3: single-match class'ı ile
        pattern3 = r'class=["\'][^"\']*single-match[^"\']*["\'][^>]*?href=["\']channel\?id=([a-zA-Z0-9_-]+)["\']'
        matches3 = re.findall(pattern3, html_content, re.DOTALL)
        
        # Tüm eşleşmeleri birleştir
        all_matches = matches1 + matches2 + matches3
        unique_ids = list(dict.fromkeys(all_matches))
        
        print(f"  Bulunan ID'ler: {unique_ids}")
        
        # Gereksiz ID'leri filtrele
        filtered_ids = []
        for channel_id in unique_ids:
            # Çok kısa veya bilinen analitik ID'leri atla
            if len(channel_id) < 2:
                continue
            if any(bad_id in channel_id.lower() for bad_id in ['google', 'facebook', 'twitter', 'analytics', 'track', 'pixel']):
                continue
            filtered_ids.append(channel_id)
        
        # Kanal isimlerini çıkar
        for channel_id in filtered_ids:
            # Kanal ismini bulmak için pattern
            name_pattern = rf'channel\?id={re.escape(channel_id)}["\'][^>]*?>.*?<div[^>]*class=["\'][^"\']*home["\'][^>]*>([^<]+)</div'
            name_match = re.search(name_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            channel_name = name_match.group(1).strip() if name_match else channel_id.upper()
            
            # Kanal grubunu belirle
            if channel_id in ['zirve', 'b2', 'b3', 'b4', 'b5', 'bm1', 'bm2']:
                group = "BeIN Sports"
            elif channel_id in ['ss', 'ss2']:
                group = "S Sport"
            elif channel_id.startswith('t'):
                group = "Tivibu"
            elif channel_id.startswith('ex'):
                group = "Tabii Spor"
            else:
                group = "Diğer"
            
            channels.append({
                'id': channel_id,
                'name': channel_name,
                'group': group,
                'm3u8_url': f"https://rei.zirvedesin201.cfd/{channel_id}/mono.m3u8"
            })
        
        return channels
    
    def test_m3u8_urls(self, channels):
        """m3u8 URL'lerini test et"""
        print("🔗 m3u8 URL'leri test ediliyor...")
        
        working_channels = []
        total = len(channels)
        
        for idx, channel in enumerate(channels, 1):
            print(f"  {idx}/{total}: {channel['id']} - {channel['name'][:20]}...", end=" ")
            
            # URL formatlarını test et
            url_formats = [
                f"https://rei.zirvedesin201.cfd/{channel['id']}/mono.m3u8",
                f"https://tv.zirvesin.tv/{channel['id']}/mono.m3u8",
                f"https://tv.eyvah.tv/{channel['id']}/mono.m3u8",
                f"https://tv.monospo.com/{channel['id']}/mono.m3u8",
                f"https://cdn1.eyvah.tv/{channel['id']}/mono.m3u8",
                f"https://cdn2.eyvah.tv/{channel['id']}/mono.m3u8",
            ]
            
            working_url = None
            for url in url_formats:
                try:
                    # HEAD isteği ile hızlı kontrol
                    r = self.session.head(url, timeout=3, verify=False, headers=self.headers)
                    if r.status_code == 200:
                        # GET ile içeriği kontrol et
                        r2 = self.session.get(url, timeout=3, verify=False, headers=self.headers)
                        if '#EXTM3U' in r2.text:
                            working_url = url
                            channel['m3u8_url'] = url
                            break
                except:
                    continue
            
            if working_url:
                print(f"✅ Çalışıyor")
                working_channels.append(channel)
            else:
                print(f"❌ Çalışmıyor")
            
            # Rate limiting
            time.sleep(0.1)
        
        return working_channels
    
    def create_playlists(self, channels):
        """M3U playlist'leri oluştur"""
        if not channels:
            print("❌ Çalışan kanal bulunamadı!")
            return
        
        print(f"\n🎬 {len(channels)} çalışan kanal bulundu. Playlist oluşturuluyor...")
        
        # Gruplara ayır
        groups = {}
        for channel in channels:
            group = channel['group']
            if group not in groups:
                groups[group] = []
            groups[group].append(channel)
        
        # Ana M3U playlist
        m3u_content = ["#EXTM3U"]
        
        for group_name, group_channels in groups.items():
            for channel in group_channels:
                # EXTINF satırı
                extinf = f'#EXTINF:-1 group-title="{group_name}",{channel["name"]}'
                m3u_content.append(extinf)
                
                # Referrer ekle
                m3u_content.append(f'#EXTVLCOPT:http-referrer=https://monotv530.com/')
                
                # m3u8 URL'si
                m3u_content.append(channel['m3u8_url'])
        
        # Dosyaya yaz
        with open("monotv_all.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        
        print(f"✅ Ana playlist oluşturuldu: monotv_all.m3u ({len(channels)} kanal)")
        
        # Grup bazlı playlist'ler oluştur
        for group_name, group_channels in groups.items():
            group_filename = f"monotv_{group_name.lower().replace(' ', '_')}.m3u"
            group_content = ["#EXTM3U"]
            
            for channel in group_channels:
                extinf = f'#EXTINF:-1 group-title="{group_name}",{channel["name"]}'
                group_content.append(extinf)
                group_content.append(f'#EXTVLCOPT:http-referrer=https://monotv530.com/')
                group_content.append(channel['m3u8_url'])
            
            with open(group_filename, "w", encoding="utf-8") as f:
                f.write("\n".join(group_content))
            
            print(f"  📁 {group_name}: {len(group_channels)} kanal -> {group_filename}")
        
        # JSON çıktısı
        with open("monotv_channels.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
        
        print(f"📊 JSON çıktısı: monotv_channels.json")
    
    def manual_channel_list(self):
        """Manuel kanal listesi - verdiğiniz HTML'den"""
        print("📋 Manuel kanal listesi oluşturuluyor...")
        
        # Verdiğiniz HTML'den kanal ID'leri
        manual_channels = [
            # Maçlar sekmesi
            {'id': 'smarts', 'name': 'SMART SPOR', 'group': 'Smart Spor'},
            {'id': 'b5', 'name': 'BEIN SPORTS 5', 'group': 'BeIN Sports'},
            {'id': 'trtspor', 'name': 'TRT SPOR', 'group': 'TRT'},
            {'id': 'b2', 'name': 'BEIN SPORTS 2', 'group': 'BeIN Sports'},
            {'id': 'zirve', 'name': 'BEIN SPORTS 1', 'group': 'BeIN Sports'},
            {'id': 'ss2', 'name': 'S SPORT 2', 'group': 'S Sport'},
            {'id': 't1', 'name': 'TIVIBU SPOR 1', 'group': 'Tivibu'},
            {'id': 'ss', 'name': 'S SPORT', 'group': 'S Sport'},
            {'id': 't2', 'name': 'TIVIBU SPOR 2', 'group': 'Tivibu'},
            
            # Kanallar sekmesi
            {'id': 'b3', 'name': 'BEIN SPORTS 3', 'group': 'BeIN Sports'},
            {'id': 'b4', 'name': 'BEIN SPORTS 4', 'group': 'BeIN Sports'},
            {'id': 'bm1', 'name': 'BEIN SPORTS MAX 1', 'group': 'BeIN Sports Max'},
            {'id': 'bm2', 'name': 'BEIN SPORTS MAX 2', 'group': 'BeIN Sports Max'},
            {'id': 'sms2', 'name': 'SMART SPOR 2', 'group': 'Smart Spor'},
            {'id': 't3', 'name': 'TIVIBU SPOR 3', 'group': 'Tivibu'},
            {'id': 't4', 'name': 'TIVIBU SPOR 4', 'group': 'Tivibu'},
            {'id': 'trtspor2', 'name': 'TRT SPOR YILDIZ', 'group': 'TRT'},
            {'id': 'trt1', 'name': 'TRT 1', 'group': 'TRT'},
            {'id': 'as', 'name': 'A SPOR', 'group': 'A Spor'},
            {'id': 'atv', 'name': 'ATV', 'group': 'TV Kanalları'},
            {'id': 'tv8', 'name': 'TV 8', 'group': 'TV Kanalları'},
            {'id': 'tv85', 'name': 'TV 8,5', 'group': 'TV Kanalları'},
            {'id': 'f1', 'name': 'SKY SPORTS F1', 'group': 'Sky Sports'},
            {'id': 'eu1', 'name': 'EURO SPORT 1', 'group': 'Eurosport'},
            {'id': 'eu2', 'name': 'EURO SPORT 2', 'group': 'Eurosport'},
            {'id': 'ex7', 'name': 'TABII SPOR', 'group': 'Tabii Spor'},
            {'id': 'ex1', 'name': 'TABII SPOR 1', 'group': 'Tabii Spor'},
            {'id': 'ex2', 'name': 'TABII SPOR 2', 'group': 'Tabii Spor'},
            {'id': 'ex3', 'name': 'TABII SPOR 3', 'group': 'Tabii Spor'},
            {'id': 'ex4', 'name': 'TABII SPOR 4', 'group': 'Tabii Spor'},
            {'id': 'ex5', 'name': 'TABII SPOR 5', 'group': 'Tabii Spor'},
            {'id': 'ex6', 'name': 'TABII SPOR 6', 'group': 'Tabii Spor'},
        ]
        
        return manual_channels
    
    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("="*50)
        print("🔄 MonoTV Scraper Başlıyor...")
        print("="*50)
        
        # 1. Domain'i bul
        domain = self.get_active_domain()
        if not domain:
            print("\n⚠️ Otomatik site bulunamadı, manuel moda geçiliyor...")
            channels = self.manual_channel_list()
        else:
            # 2. Site içeriğini al
            try:
                print(f"\n📥 {domain} içeriği alınıyor...")
                response = self.session.get(domain, headers=self.headers, timeout=10, verify=False)
                html_content = response.text
                
                # 3. Kanalları çıkar
                channels = self.extract_channels_direct(html_content)
                
                if len(channels) < 5:  # Çok az kanal bulunduysa
                    print(f"⚠️ Sadece {len(channels)} kanal bulundu, manuel listeye geçiliyor...")
                    channels = self.manual_channel_list()
            
            except Exception as e:
                print(f"❌ Hata: {e}")
                print("⚠️ Manuel listeye geçiliyor...")
                channels = self.manual_channel_list()
        
        # 4. m3u8 URL'lerini test et
        print(f"\n🔍 {len(channels)} kanal test ediliyor...")
        working_channels = self.test_m3u8_urls(channels)
        
        # 5. Playlist'leri oluştur
        self.create_playlists(working_channels)
        
        # 6. Özet
        print("\n" + "="*50)
        print("📊 ÇALIŞMA ÖZETİ")
        print("="*50)
        print(f"Toplam Kanal: {len(channels)}")
        print(f"Çalışan Kanal: {len(working_channels)}")
        print(f"Başarı Oranı: {(len(working_channels)/len(channels)*100):.1f}%")
        
        # Çalışan kanalları göster
        if working_channels:
            print("\n✅ ÇALIŞAN KANALLAR:")
            for i, channel in enumerate(working_channels[:15], 1):  # İlk 15'i göster
                print(f"  {i:2d}. {channel['name']:<25} ({channel['id']})")
            
            if len(working_channels) > 15:
                print(f"  ... ve {len(working_channels)-15} kanal daha")
        
        print("\n🎉 İşlem tamamlandı!")

def main():
    """Ana fonksiyon"""
    try:
        scraper = SimpleMonoScraper()
        scraper.run()
    except KeyboardInterrupt:
        print("\n\n⏹️ Program durduruldu.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
