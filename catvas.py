import requests
import json
import time
from typing import List, Dict, Any

class CatCastM3UGenerator:
    def __init__(self):
        self.base_url = "https://api.catcast.tv/api/channels?page={}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://catcast.tv/'
        })
        
    def fetch_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Tek bir sayfadan verileri çeker"""
        url = self.base_url.format(page_num)
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"Sayfa {page_num} çekiliyor... (Deneme {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') == 1 and 'data' in data:
                    channels = data['data']['list']['data']
                    print(f"Sayfa {page_num}: {len(channels)} kanal bulundu")
                    return channels
                else:
                    print(f"Sayfa {page_num} için geçersiz yanıt: {data.get('status')}")
                    return []
                    
            except requests.exceptions.RequestException as e:
                print(f"Sayfa {page_num} hatası: {e}")
                if attempt < max_retries - 1:
                    print(f"{retry_delay} saniye bekleniyor...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Sayfa {page_num} için maksimum deneme sayısına ulaşıldı")
                    return []
        
        return []
    
    def generate_m3u_content(self, channels: List[Dict[str, Any]], page_num: int) -> str:
        """Kanal listesini M3U formatına dönüştürür"""
        m3u_content = ""
        
        for channel in channels:
            if not self.is_valid_channel(channel):
                continue
                
            channel_id = channel.get('id', '')
            channel_name = channel.get('name', '').strip()
            channel_logo = channel.get('logo', '')
            shortname = channel.get('shortname', '').strip()
            
            if not all([channel_id, channel_name, shortname]):
                continue
            
            # Stream URL'sini oluştur
            stream_url = f"https://example.com/?id={shortname}.m3u8"
            
            # M3U girişi oluştur
            m3u_content += f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" tvg-logo="{channel_logo}" group-title="Sayfa {page_num}",{channel_name}\n'
            m3u_content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n'
            m3u_content += f'#EXTVLCOPT:http-referer=https://catcast.tv/\n'
            m3u_content += f'{stream_url}\n'
        
        return m3u_content
    
    def is_valid_channel(self, channel: Dict[str, Any]) -> bool:
        """Kanalın geçerli olup olmadığını kontrol eder"""
        required_fields = ['id', 'name', 'shortname']
        return all(field in channel and channel[field] for field in required_fields)
    
    def generate_playlist(self):
        """Tüm sayfaları çekip M3U playlist oluşturur"""
        # SAYFA SAYISI 23'ten 50'ye ÇIKARILDI - 480 ve 481 KORUNDU
        pages = list(range(1, 51)) + [480, 481]  # 1-50 + 480, 481
        
        all_m3u_content = "#EXTM3U\n"
        
        total_channels = 0
        
        for page_num in pages:
            channels = self.fetch_page(page_num)
            if channels:
                page_content = self.generate_m3u_content(channels, page_num)
                all_m3u_content += page_content
                total_channels += len([ch for ch in channels if self.is_valid_channel(ch)])
            
            # API'ye aşırı yük bindirmemek için kısa bekleme
            time.sleep(1)
        
        print(f"Toplam {total_channels} kanal işlendi")
        
        # M3U dosyasını kaydet
        with open('catcast_tv.m3u', 'w', encoding='utf-8') as f:
            f.write(all_m3u_content)
        
        print("catcast_tv.m3u dosyası başarıyla oluşturuldu!")

def main():
    generator = CatCastM3UGenerator()
    generator.generate_playlist()

if __name__ == "__main__":
    main()
