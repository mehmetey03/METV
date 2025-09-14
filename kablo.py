import requests
import json
import gzip
from io import BytesIO
from datetime import datetime, timedelta
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# SSL uyarılarını gizle
urllib3.disable_warnings(InsecureRequestWarning)

def get_canli_tv_m3u():
    """Orijinal REST API ile kanal verilerini al"""
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjJhYmM4OTI3LTkwOGMtNDNhZi1iZjg0LTE3ODg5YjYyNGIxZSIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsInNwZ2QiOiJhMDkwODc4NC1kMTI4LTQ2MWYtYjc2Yi1hNTdkZWIxYjgwY2MiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiYXB2IjoiMS4wLjAiLCJhYm4iOiIxMDAwIiwibmJmIjoxNzU3ODYyODQ0LCJleHAiOjE3NTc4NjI5MDQsImlhdCI6MTc1Nzg2Mjg0NH0.flmV7l1T-wcuFnvSNBDQCp3z5LVdHwg_Es98gemRMek"
    
    # Orijinal REST API endpoint'i
    url = "https://core-api.kablowebtv.com/api/channels"
    
    # Tarih aralığı (bugün 00:00 - 23:59)
    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d-00:00")
    end_date = now.strftime("%Y-%m-%d-23:59")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://tvheryerde.com/",
        "Origin": "https://tvheryerde.com",
        "Authorization": f"Bearer {token}"
    }
    
    params = {
        "start": start_date,
        "end": end_date
    }
    
    try:
        print("📡 Orijinal REST API'den veri alınıyor...")
        print(f"🔗 URL: {url}")
        print(f"📅 Tarih aralığı: {start_date} - {end_date}")
        
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
        response.raise_for_status()
        
        print(f"✅ API yanıtı alındı. Status: {response.status_code}")
        
        # JSON verisini parse et
        data = response.json()
        
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            print("❌ API'den geçerli veri alınamadı!")
            print(f"Mesaj: {data.get('Message', 'Bilinmeyen hata')}")
            return False
        
        channels = data['Data']['AllChannels']
        print(f"✅ {len(channels)} kanal bulundu")
        
        # M3U dosyasını oluştur
        return create_m3u_file(channels)
        
    except requests.exceptions.Timeout:
        print("❌ Timeout hatası: Sunucu yanıt vermedi")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ağ hatası: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse hatası: {e}")
        print(f"Raw response: {response.text[:200]}...")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False

def create_m3u_file(channels):
    """M3U dosyasını oluştur"""
    try:
        if not channels:
            print("❌ Kanal verisi yok!")
            return False
        
        with open("canlitv_channels.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            kanal_sayisi = 0
            for index, channel in enumerate(channels, 1):
                # Kanal bilgilerini al
                name = channel.get('Name')
                stream_data = channel.get('StreamData', {})
                hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
                logo = channel.get('PrimaryLogoImageUrl', '')
                
                # Kategori bilgisi
                categories = channel.get('Categories', [])
                group = categories[0].get('Name', 'Genel') if categories else 'Genel'
                
                # Bilgilendirme kanallarını atla
                if group == "Bilgilendirme" or not name or not hls_url:
                    continue
                
                # M3U formatında yaz
                f.write(f'#EXTINF:-1 tvg-id="{index}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f'{hls_url}\n')
                
                kanal_sayisi += 1
        
        print(f"📺 canlitv_channels.m3u dosyası oluşturuldu! ({kanal_sayisi} kanal)")
        return True
        
    except Exception as e:
        print(f"❌ M3U oluşturma hatası: {e}")
        return False

def test_token_validity():
    """Token'ın geçerliliğini test et"""
    try:
        import jwt
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjJhYmM4OTI3LTkwOGMtNDNhZi1iZjg0LTE3ODg5YjYyNGIxZSIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsInNwZ2QiOiJhMDkwODc4NC1kMTI4LTQ2MWYtYjc2Yi1hNTdkZWIxYjgwY2MiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiYXB2IjoiMS4wLjAiLCJhYm4iOiIxMDAwIiwibmJmIjoxNzU3ODYyODQ0LCJleHAiOjE3NTc4NjI5MDQsImlhdCI6MTc1Nzg2Mjg0NH0.flmV7l1T-wcuFnvSNBDQCp3z5LVdHwg_Es98gemRMek"
        
        # JWT token'ı decode et (verify=False çünkü secret key yok)
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(decoded['exp'])
        now = datetime.now()
        
        print(f"🔐 Token bilgileri:")
        print(f"   Oluşturulma: {datetime.fromtimestamp(decoded['iat'])}")
        print(f"   Son kullanma: {exp_time}")
        print(f"   Kalan süre: {exp_time - now}")
        
        if now > exp_time:
            print("❌ Token'ın süresi dolmuş!")
            return False
        else:
            print("✅ Token hala geçerli")
            return True
            
    except ImportError:
        print("⚠️  jwt kütüphanesi yüklü değil. Token kontrolü atlanıyor.")
        print("💡 Kurmak için: pip install pyjwt")
        return True
    except Exception as e:
        print(f"❌ Token decode hatası: {e}")
        return False

def get_new_token_from_browser():
    """Yeni token almak için kullanıcıya talimatlar göster"""
    print("\n" + "="*60)
    print("🔑 YENİ TOKEN ALMA TALİMATLARI")
    print("="*60)
    print("1. https://tvheryerde.com sitesine Chrome/Firefox ile gidin")
    print("2. F12 Developer Tools'u açın")
    print("3. Network tab'ına gidin")
    print("4. Sayfayı yenileyin (F5)")
    print("5. 'channels' veya 'api' isteklerini bulun")
    print("6. Headers kısmında 'Authorization: Bearer ...' token'ını kopyalayın")
    print("7. Token'ı script'te güncelleyin")
    print("="*60)

if __name__ == "__main__":
    print("🚀 CanliTV M3U Oluşturucu")
    print("="*40)
    
    # Önce token'ı kontrol et
    if not test_token_validity():
        get_new_token_from_browser()
        exit()
    
    # API'den veri al
    success = get_canli_tv_m3u()
    
    if success:
        print("\n🎉 İşlem başarıyla tamamlandı!")
        print("📁 Dosya: canlitv_channels.m3u")
    else:
        print("\n❌ İşlem başarısız oldu")
        print("💡 Token süresi dolmuş olabilir, yukarıdaki talimatlarla yeni token alın")
