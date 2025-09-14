import requests
import json
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# SSL uyarılarını gizle
urllib3.disable_warnings(InsecureRequestWarning)

def get_canli_tv_m3u():
    """Yeni endpoint'ten HTTP ile veri al"""
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjJhYmM4OTI3LTkwOGMtNDNhZi1iZjg0LTE3ODg5YjYyNGIxZSIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsInNwZ2QiOiJhMDkwODc4NC1kMTI4LTQ2MWYtYjc2Yi1hNTdkZWIxYjgwY2MiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiYXB2IjoiMS4wLjAiLCJhYm4iOiIxMDAwIiwibmJmIjoxNzU3ODYyODQ0LCJleHAiOjE3NTc4NjI5MDQsImlhdCI6MTc1Nzg2Mjg0NH0.flmV7l1T-wcuFnvSNBDQCp3z5LVdHwg_Es98gemRMek"
    
    # 1. Önce handshake yap
    handshake_url = f"https://turksat.midgard.io:4000/socket.io/?EIO=4&transport=polling&token={token}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Origin": "https://tvheryerde.com",
        "Referer": "https://tvheryerde.com/"
    }
    
    try:
        print("🔌 Yeni endpoint'e bağlanılıyor...")
        
        # 1. Handshake
        response = requests.get(handshake_url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        print(f"✅ Handshake başarılı. Status: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
        
        # Handshake response'unu parse et
        if response.text.startswith('0'):
            try:
                json_data = json.loads(response.text[1:])
                sid = json_data.get('sid')
                print(f"📋 Session ID: {sid}")
                
                if not sid:
                    print("❌ Session ID alınamadı")
                    return False
                
                # 2. Kanal verilerini iste
                post_url = f"https://turksat.midgard.io:4000/socket.io/?EIO=4&transport=polling&token={token}&sid={sid}"
                post_data = '42["get_channels",{"token":"' + token + '"}]'
                
                post_headers = headers.copy()
                post_headers["Content-Type"] = "text/plain; charset=UTF-8"
                
                print("📡 Kanal verileri isteniyor...")
                post_response = requests.post(post_url, data=post_data, headers=post_headers, timeout=30, verify=False)
                print(f"📨 POST Response: {post_response.status_code}")
                
                # 3. Yanıtı al
                time.sleep(2)  # Sunucunun yanıt hazırlaması için bekle
                get_response = requests.get(post_url, headers=headers, timeout=30, verify=False)
                
                print(f"📥 GET Response: {get_response.status_code}")
                print(f"📊 Veri: {get_response.text[:200]}...")
                
                # Yanıtı parse etmeye çalış
                if get_response.text:
                    # Socket.io formatında veri: "42["channels_list",{...}]"
                    if get_response.text.startswith('42["channels_list"'):
                        try:
                            # JSON kısmını ayıkla
                            json_str = get_response.text[2:]  # "42"yi kaldır
                            data = json.loads(json_str)
                            
                            if isinstance(data, list) and len(data) >= 2 and data[0] == "channels_list":
                                channels = data[1].get('channels', [])
                                print(f"✅ {len(channels)} kanal bulundu!")
                                
                                # M3U dosyasını oluştur
                                return create_m3u_file(channels)
                            else:
                                print("❌ Beklenen format dışında veri")
                                return False
                                
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON parse hatası: {e}")
                            print(f"Raw response: {get_response.text}")
                            return False
                    else:
                        print("❌ Beklenen channels_list event'i gelmedi")
                        print(f"Gelen veri: {get_response.text}")
                        return False
                else:
                    print("❌ Boş yanıt alındı")
                    return False
                
            except json.JSONDecodeError as e:
                print(f"❌ Handshake JSON hatası: {e}")
                return False
        else:
            print("❌ Beklenen handshake formatı dışında")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout hatası: Sunucu yanıt vermedi")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ağ hatası: {e}")
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
        
        with open("yeni_socketio.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            kanal_sayisi = 0
            for index, channel in enumerate(channels, 1):
                # Farklı formatlar için esneklik
                name = channel.get('Name') or channel.get('name') or f'Kanal {index}'
                stream_url = channel.get('StreamUrl') or channel.get('stream_url') or channel.get('url') or ''
                logo = channel.get('Logo') or channel.get('logo') or channel.get('image') or ''
                
                # Kategori/grup bilgisi
                category = channel.get('Category') or channel.get('category') or channel.get('group') or 'Genel'
                
                if stream_url and name:
                    f.write(f'#EXTINF:-1 tvg-id="{index}" tvg-logo="{logo}" group-title="{category}",{name}\n')
                    f.write(f'{stream_url}\n')
                    kanal_sayisi += 1
        
        print(f"📺 yeni_socketio.m3u dosyası oluşturuldu! ({kanal_sayisi} kanal)")
        return True
        
    except Exception as e:
        print(f"❌ M3U oluşturma hatası: {e}")
        return False

def test_connection():
    """Basit bağlantı testi"""
    try:
        test_url = "https://turksat.midgard.io:4000/"
        response = requests.get(test_url, timeout=10, verify=False)
        print(f"✅ Sunucu erişilebilir. Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Sunucu erişilemiyor: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Yeni CanliTV M3U Oluşturucu")
    print("=" * 50)
    
    if test_connection():
        print("\n🔗 Bağlantı testi başarılı, veri alınıyor...")
        success = get_canli_tv_m3u()
        if success:
            print("\n🎉 İşlem başarıyla tamamlandı!")
        else:
            print("\n❌ Veri alınamadı, token süresi dolmuş olabilir")
    else:
        print("\n❌ Sunucuya erişim sağlanamadı")
