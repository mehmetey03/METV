import requests
import json
import gzip
from io import BytesIO
import time
import socket

def get_canli_tv_m3u():
    url = "https://core-api.kablowebtv.com/api/channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://tvheryerde.com/",
        "Origin": "https://tvheryerde.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6ImE2OTliODNmLTgyNmItNGQ5OS05MzYxLWM4YTMxMzIxOGQ0NiIsInNnZCI6Ijg5NzQxZmVjLTFkMzMtNGMwMC1hZmNkLTNmZGFmZTBiNmEyZCIsInNwZ2QiOiIxNTJiZDUzOS02MjIwLTQ0MjctYTkxNS1iZjRiZDA2OGQ3ZTgiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NDUxNTI4MjUsImV4cCI6MTc0NTE1Mjg4NSwiaWF0IjoxNzQ1MTUyODI1fQ.OSlafRMxef4EjHG5t6TqfAQC7y05IiQjwwgf6yMUS9E"
    }
    
    # DNS çözümleme kontrolü
    try:
        socket.gethostbyname("core-api.kablowebtv.com")
        print("✅ DNS çözümleme başarılı")
    except socket.gaierror:
        print("❌ DNS hatası: Sunucu bulunamadı")
        return False
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"📡 CanliTV API'den veri alınıyor... (Deneme {attempt + 1}/{max_retries})")
            
            # Timeout süresini artır ve retry mekanizması ekle
            response = requests.get(url, headers=headers, timeout=45)
            response.raise_for_status()
            
            print(f"✅ API yanıtı alındı. Status: {response.status_code}")
            
            # Gzip kontrolü
            if response.headers.get('Content-Encoding') == 'gzip':
                with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                    content = gz.read().decode('utf-8')
            else:
                content = response.text
            
            data = json.loads(content)
            
            if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
                print("❌ API'den geçerli veri alınamadı!")
                return False
            
            channels = data['Data']['AllChannels']
            print(f"✅ {len(channels)} kanal bulundu")
            
            with open("yeni.m3u", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                kanal_sayisi = 0
                kanal_index = 1  
                
                for channel in channels:
                    name = channel.get('Name')
                    stream_data = channel.get('StreamData', {})
                    hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
                    logo = channel.get('PrimaryLogoImageUrl', '')
                    categories = channel.get('Categories', [])
                    
                    if not name or not hls_url:
                        continue
                    
                    group = categories[0].get('Name', 'Genel') if categories else 'Genel'
                    
                    if group == "Bilgilendirme":
                        continue

                    tvg_id = str(kanal_index)

                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                    f.write(f'{hls_url}\n')

                    kanal_sayisi += 1
                    kanal_index += 1  
            
            print(f"📺 yeni.m3u dosyası oluşturuldu! ({kanal_sayisi} kanal)")
            return True
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                print(f"⏳ Timeout, {wait_time} saniye bekleniyor...")
                time.sleep(wait_time)
            else:
                print("❌ Maksimum deneme sayısına ulaşıldı. Timeout hatası devam ediyor.")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Ağ hatası: {e}")
            return False
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")
            return False

if __name__ == "__main__":
    get_canli_tv_m3u()
