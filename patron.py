import requests
import re
import urllib3
import json
from typing import Optional, List, Dict
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://hepbetspor16.cfd/",
    "X-Requested-With": "XMLHttpRequest"
}

class IPTVPlaylistGenerator:
    def __init__(self):
        self.main_site = "https://hepbetspor16.cfd"
        self.base_url = None
        self.m3u_list = ["#EXTM3U"]
        self.found_count = 0
        
    def get_base_url(self) -> str:
        """Yayın sunucusunun base URL'ini alır"""
        try:
            r = requests.get(
                DOMAIN_API_URL, 
                headers=HEADERS, 
                timeout=10, 
                verify=False
            )
            base_url = r.json().get("baseurl", "").replace("\\", "").rstrip('/') + "/"
            logging.info(f"Base URL alındı: {base_url}")
            return base_url
        except requests.exceptions.RequestException as e:
            logging.warning(f"Base URL alınamadı, varsayılan kullanılacak: {e}")
            return "https://obv.d72577a9dd0ec28.sbs/"
        except json.JSONDecodeError as e:
            logging.warning(f"JSON parse hatası: {e}")
            return "https://obv.d72577a9dd0ec28.sbs/"
    
    def fetch_page_content(self) -> Optional[str]:
        """Ana sayfanın içeriğini çeker"""
        try:
            response = requests.get(
                self.main_site, 
                headers=HEADERS, 
                timeout=15, 
                verify=False
            )
            response.raise_for_status()
            logging.info(f"Sayfa içeriği çekildi: {len(response.text)} karakter")
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Sayfa çekilemedi: {e}")
            return None
    
    def parse_channel_blocks(self, html_content: str) -> List[Dict]:
        """HTML içinden kanal bloklarını parse eder"""
        channels = []
        
        # Metod 1: channel-item bloklarını bul
        blocks = re.findall(
            r'<div class="channel-item".*?>(.*?)</div>\s*</div>', 
            html_content, 
            re.DOTALL
        )
        
        for block in blocks:
            channel_info = self.extract_channel_info(block)
            if channel_info:
                channels.append(channel_info)
        
        # Metod 2: data-src pattern'i ile ara
        if not channels:
            matches = re.findall(
                r'data-src="/ch\.html\?id=(.*?)".*?class="team-name">(.*?)</span>.*?class="team-name">(.*?)</span>',
                html_content, 
                re.DOTALL
            )
            for match in matches:
                channels.append({
                    'id': match[0],
                    'name': f"{match[1]} - {match[2]}",
                    'teams': [match[1], match[2]]
                })
        
        logging.info(f"Bulunan kanal sayısı: {len(channels)}")
        return channels
    
    def extract_channel_info(self, block: str) -> Optional[Dict]:
        """Bir kanal bloğundan bilgileri çıkarır"""
        try:
            # ID'yi bul
            cid_match = re.search(r'id=([^&"\'\s>]+)', block)
            if not cid_match:
                return None
            
            cid = cid_match.group(1)
            
            # Takım isimlerini bul
            teams = re.findall(r'class="team-name">(.*?)</span>', block)
            
            # Kanal adını oluştur
            if teams and len(teams) >= 2:
                name = f"{teams[0]} - {teams[1]}"
            elif teams:
                name = teams[0]
            else:
                name = f"Kanal {cid}"
            
            return {
                'id': cid,
                'name': name,
                'teams': teams
            }
        except Exception as e:
            logging.debug(f"Kanal bilgisi çıkarılamadı: {e}")
            return None
    
    def add_channel_to_playlist(self, channel: Dict):
        """Kanalı M3U playlist'ine ekler"""
        self.m3u_list.append(f'#EXTINF:-1 group-title="CANLI MAÇLAR",{channel["name"]}')
        self.m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        self.m3u_list.append(f'#EXTVLCOPT:http-referrer={self.main_site}/')
        self.m3u_list.append(f'{self.base_url}{channel["id"]}/mono.m3u8')
        self.found_count += 1
    
    def add_fallback_channels(self):
        """Hiç kanal bulunamazsa varsayılan kanalları ekler"""
        logging.info("Yedek kanallar ekleniyor...")
        fixed_channels = ["patron", "b2", "b3", "t2", "ss1"]
        for f_id in fixed_channels:
            self.m3u_list.append(f'#EXTINF:-1 group-title="7/24 KANALLAR",Kanal {f_id}')
            self.m3u_list.append(f'{self.base_url}{f_id}/mono.m3u8')
            self.found_count += 1
    
    def save_playlist(self, filename: str = "patron_final.m3u"):
        """Playlist'i dosyaya kaydeder"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(self.m3u_list))
            logging.info(f"Playlist kaydedildi: {filename}")
        except IOError as e:
            logging.error(f"Dosya kaydedilemedi: {e}")
    
    def run(self):
        """Ana çalıştırma fonksiyonu"""
        logging.info(f"Bağlanılıyor: {self.main_site}")
        
        # Base URL'i al
        self.base_url = self.get_base_url()
        logging.info(f"Yayın Sunucusu: {self.base_url}")
        
        # Sayfa içeriğini çek
        html_content = self.fetch_page_content()
        if not html_content:
            logging.error("Sayfa içeriği alınamadı, işlem sonlandırılıyor.")
            return
        
        # Kanalları parse et
        channels = self.parse_channel_blocks(html_content)
        
        # Kanalları playlist'e ekle
        for channel in channels:
            self.add_channel_to_playlist(channel)
        
        # Eğer hiç kanal bulunamadıysa yedek kanalları ekle
        if self.found_count == 0:
            logging.warning("HTML içinde maç bulunamadı, alternatif kanallar ekleniyor...")
            self.add_fallback_channels()
        
        # Playlist'i kaydet
        self.save_playlist()
        logging.info(f"İşlem tamamlandı. Eklenen kanal sayısı: {self.found_count}")

def main():
    generator = IPTVPlaylistGenerator()
    generator.run()

if __name__ == "__main__":
    main()
