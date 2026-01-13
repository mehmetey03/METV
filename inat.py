import requests
import re
import sys

def main():
    try:
        # Domain aralığı (25–99)
        active_domain = None
        print("🔍 Aktif domain aranıyor...")
        
        for i in range(1204, 2000):
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
            create_empty_m3u()
            return 0
        
        # İlk kanal ID'si al
        print("📡 Kanal ID'si alınıyor...")
        try:
            html = requests.get(active_domain, timeout=10).text
            m = re.search(r'<iframe[^>]+id="customIframe"[^>]+src="/channel.html\?id=([^"]+)"', html)
            
            if not m:
                print("⚠️  Kanal ID bulunamadı. Boş M3U dosyası oluşturuluyor...")
                create_empty_m3u()
                return 0
            
            first_id = m.group(1)
            print(f"✅ Kanal ID bulundu: {first_id}")
            
        except Exception as e:
            print(f"⚠️  HTML alınırken hata: {str(e)}")
            create_empty_m3u()
            return 0
        
        # Base URL çek
        print("🔗 Base URL alınıyor...")
        try:
            event_source = requests.get(active_domain + "channel.html?id=" + first_id, timeout=10).text
            b = re.search(r'const\s+BASE_URL\s*=\s*"([^"]+)"', event_source)
            
            if not b:
                print("⚠️  Base URL bulunamadı. Boş M3U dosyası oluşturuluyor...")
                create_empty_m3u()
                return 0
            
            base_url = b.group(1)
            print(f"✅ Base URL bulundu: {base_url}")
            
        except Exception as e:
            print(f"⚠️  Event source alınırken hata: {str(e)}")
            create_empty_m3u()
            return 0
        
        # Kanal listesi
        channel_ids = {
            "yayinzirve": ["beIN Sports 1 A", "Inat TV"],
            "yayininat":  ["beIN Sports 1 B", "Inat TV"],
            "yayin1":     ["beIN Sports 1 C️", "Inat TV"],
            "yayinb2":    ["beIN Sports 2", "Inat TV"],
            "yayinb3":    ["beIN Sports 3", "Inat TV"],
            "yayinb4":    ["beIN Sports 4", "Inat TV"],
            "yayinb5":    ["beIN Sports 5", "Inat TV"],
            "yayinbm1":   ["beIN Sports 1 Max", "Inat TV"],
            "yayinbm2":   ["beIN Sports 2 Max", "Inat TV"],
            "yayinss":    ["S Sports 1", "Inat TV"],
            "yayinss2":   ["S Sports 2", "Inat TV"],
            "yayint1":    ["Tivibu Sports 1", "Inat TV"],
            "yayint2":    ["Tivibu Sports 2", "Inat TV"],
            "yayint3":    ["Tivibu Sports 3", "Inat TV"],
            "yayint4":    ["Tivibu Sports 4", "Inat TV"],
            "yayinsmarts":["Smart Sports", "Inat TV"],
            "yayinsms2":  ["Smart Sports 2", "Inat TV"],
            "yayineu1":  ["Euro Sport 1", "Inat TV"],
            "yayineu2":  ["Euro Sport 2", "Inat TV"],
            "yayinex1":   ["Tâbii 1", "Inat TV"],
            "yayinex2":   ["Tâbii 2", "Inat TV"],
            "yayinex3":   ["Tâbii 3", "Inat TV"],
            "yayinex4":   ["Tâbii 4", "Inat TV"],
            "yayinex5":   ["Tâbii 5", "Inat TV"],
            "yayinex6":   ["Tâbii 6", "Inat TV"],
            "yayinex7":   ["Tâbii 7", "Inat TV"],
            "yayinex8":   ["Tâbii 8", "Inat TV"]
        }
        
        # M3U dosyası oluştur
        print("📝 M3U dosyası oluşturuluyor...")
        lines = ["\n"]
        for cid, details in channel_ids.items():
            name = details[0]  # Listenin ilk elemanı: Kanal Adı (Örn: beIN Sports 1 A)
            title = details[1] # Listenin ikinci elemanı: Grup (Örn: Inat TV)
            
            # EXTM3U satırını oluştur
            lines.append(f'#EXTINF:-1 group-title="Inat TV" ,{name}')
            lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5)')
            lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
            
            # URL satırını oluştur (Sözlük anahtarı olan 'cid' kullanılıyor)
            full_url = f"{base_url}{cid}.m3u8"
            lines.append(full_url)
        
        with open("inattv.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"✅ inattv.m3u başarıyla oluşturuldu ({len(channel_ids)} kanal)")
        return 0
        
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
        print("⚠️  Boş M3U dosyası oluşturuluyor...")
        create_empty_m3u()
        return 0

def create_empty_m3u():
    """Hata durumunda boş/placeholder M3U dosyası oluştur"""
    try:
        with open("inattv.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("# Kanal listesi şu anda kullanılamıyor\n")
        print("✅ Placeholder M3U dosyası oluşturuldu")
    except Exception as e:
        print(f"❌ M3U dosyası oluşturulamadı: {str(e)}")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)





