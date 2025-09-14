import requests
import json
import socketio
import logging
from datetime import datetime

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_canli_tv_m3u_socketio():
    """Yeni Socket.io endpoint'ini kullanarak kanal verilerini al"""
    
    # Token ve endpoint bilgileri
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjJhYmM4OTI3LTkwOGMtNDNhZi1iZjg0LTE3ODg5YjYyNGIxZSIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsInNwZ2QiOiJhMDkwODc4NC1kMTI4LTQ2MWYtYjc2Yi1hNTdkZWIxYjgwY2MiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiYXB2IjoiMS4wLjAiLCJhYm4iOiIxMDAwIiwibmJmIjoxNzU3ODYyODQ0LCJleHAiOjE3NTc4NjI5MDQsImlhdCI6MTc1Nzg2Mjg0NH0.flmV7l1T-wcuFnvSNBDQCp3z5LVdHwg_Es98gemRMek"
    socketio_url = "https://turksat.midgard.io:4000"
    
    try:
        print("🔌 Socket.io bağlantısı kuruluyor...")
        
        # Socket.io client oluştur
        sio = socketio.Client()
        
        # Event handler'lar
        @sio.event
        def connect():
            print("✅ Socket.io bağlantısı başarılı")
            # Kanal listesi isteği gönder
            sio.emit('get_channels', {'token': token})
        
        @sio.event
        def channels_list(data):
            print(f"📡 {len(data.get('channels', []))} kanal alındı")
            
            # M3U dosyasını oluştur
            create_m3u_file(data.get('channels', []))
            
            # Bağlantıyı kapat
            sio.disconnect()
        
        @sio.event
        def disconnect():
            print("🔌 Socket.io bağlantısı kesildi")
        
        # Bağlan
        sio.connect(socketio_url, transports=['websocket'], auth={'token': token})
        sio.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ Socket.io hatası: {e}")
        return False

def get_canli_tv_m3u_http():
    """HTTP polling yöntemi ile veri al (fallback)"""
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjJhYmM4OTI3LTkwOGMtNDNhZi1iZjg0LTE3ODg5YjYyNGIxZSIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsInNwZ2QiOiJhMDkwODc4NC1kMTI4LTQ2MWYtYjc2Yi1hNTdkZWIxYjgwY2MiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiYXB2IjoiMS4wLjAiLCJhYm4iOiIxMDAwIiwibmJmIjoxNzU3ODYyODQ0LCJleHAiOjE3NTc4NjI5MDQsImlhdCI6MTc1Nzg2Mjg0NH0.flmV7l1T-wcuFnvSNBDQCp3z5LVdHwg_Es98gemRMek"
    polling_url = f"https://turksat.midgard.io:4000/socket.io/?token={token}&EIO=4&transport=polling"
    
    try:
        print("📡 HTTP polling ile veri alınıyor...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "*/*",
            "Origin": "https://tvheryerde.com",
            "Referer": "https://tvheryerde.com/"
        }
        
        response = requests.get(polling_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Socket.io polling formatını parse et
        # Format genellikle: "0{"sid":"...","upgrades":[],"pingInterval":25000,"pingTimeout":5000}"
        data = response.text
        if data.startswith('0'):
            try:
                # JSON kısmını al
                json_str = data[1:]
                handshake_data = json.loads(json_str)
                print("✅ Handshake başarılı")
                print(f"Session ID: {handshake_data.get('sid')}")
                
                # Şimdi kanal verilerini almak için POST isteği yap
                post_url = f"https://turksat.midgard.io:4000/socket.io/?token={token}&EIO=4&transport=polling&sid={handshake_data['sid']}"
                post_data = '42["get_channels",{"token":"' + token + '"}]'
                
                post_response = requests.post(post_url, data=post_data, headers=headers, timeout=30)
                if post_response.status_code == 200:
                    print("✅ Kanal verisi isteği gönderildi")
                    # Cevabı oku
                    print("Response:", post_response.text)
                    
                    # Cevabı parse etmek için bir sonraki GET isteği
                    get_response = requests.get(post_url, headers=headers, timeout=30)
                    print("Kanal verisi:", get_response.text)
                    
                    return True
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse hatası: {e}")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ HTTP polling hatası: {e}")
        return False

def create_m3u_file(channels):
    """M3U dosyasını oluştur"""
    try:
        if not channels:
            print("❌ Kanal verisi yok!")
            return False
        
        with open("yeni_socketio.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            for index, channel in enumerate(channels, 1):
                name = channel.get('Name', channel.get('name', f'Kanal {index}'))
                stream_url = channel.get('StreamUrl', channel.get('stream_url', ''))
                logo = channel.get('Logo', channel.get('logo', ''))
                group = channel.get('Category', channel.get('category', 'Genel'))
                
                if stream_url:
                    f.write(f'#EXTINF:-1 tvg-id="{index}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                    f.write(f'{stream_url}\n')
        
        print(f"📺 yeni_socketio.m3u dosyası oluşturuldu! ({len(channels)} kanal)")
        return True
        
    except Exception as e:
        print(f"❌ M3U oluşturma hatası: {e}")
        return False

def test_simple_http():
    """Basit HTTP testi"""
    try:
        test_url = "https://turksat.midgard.io:4000/"
        response = requests.get(test_url, timeout=10, verify=False)
        print(f"✅ Sunucu erişilebilir. Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Sunucu erişilemiyor: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Yeni endpoint test ediliyor...")
    
    # Önce basit bir test yap
    if test_simple_http():
        # Önce Socket.io deneyelim
        print("\n1. Socket.io yöntemi deneniyor...")
        if not get_canli_tv_m3u_socketio():
            # Socket.io başarısız olursa HTTP polling deneyelim
            print("\n2. HTTP polling yöntemi deneniyor...")
            if not get_canli_tv_m3u_http():
                print("\n❌ Her iki yöntem de başarısız oldu")
    else:
        print("❌ Sunucuya erişim yok")
