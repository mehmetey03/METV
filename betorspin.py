import requests
import re
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Adresler
DOMAIN_API = "https://maqrizi.com/domain.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

# GÜNCELLENMİŞ KANAL LİSTESİ (Türkçe isimler)
SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", 
    "beIN Sports 2": "yayinb2.m3u8", 
    "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", 
    "beIN Sports 5": "yayinb5.m3u8", 
    "beIN Sports Haber": "yayinbeinh.m3u8",
    "beIN Sports MAX 1": "yayinbm1.m3u8",
    "beIN Sports MAX 2": "yayinbm2.m3u8",
    "S Sport 1": "yayinss.m3u8", 
    "S Sport 2": "yayinss2.m3u8", 
    "Smart Spor 1": "yayinsmarts.m3u8", 
    "Smart Spor 2": "yayinsms2.m3u8",
    "Tivibu Spor 1": "yayint1.m3u8",
    "Tivibu Spor 2": "yayint2.m3u8", 
    "Tivibu Spor 3": "yayint3.m3u8", 
    "Tivibu Spor 4": "yayint4.m3u8",
    "TRT Spor": "yayintrtspor.m3u8",
    "TRT Spor Yıldız": "yayintrtspor2.m3u8", 
    "TRT 1": "yayintrt1.m3u8",
    "A Spor": "yayinas.m3u8",
    "ATV": "yayinatv.m3u8",
    "TV 8": "yayintv8.m3u8",
    "TV 8.5": "yayintv85.m3u8",
    "Sky Sports F1": "yayinf1.m3u8",
    "Eurosport 1": "yayineu1.m3u8",
    "Eurosport 2": "yayineu2.m3u8",
    "TABII Spor": "yayinex7.m3u8",
    "TABII Spor 1": "yayinex1.m3u8", 
    "TABII Spor 2": "yayinex2.m3u8", 
    "TABII Spor 3": "yayinex3.m3u8",
    "TABII Spor 4": "yayinex4.m3u8", 
    "TABII Spor 5": "yayinex5.m3u8", 
    "TABII Spor 6": "yayinex6.m3u8",
    "NBA TV": "yayinnba.m3u8",
    "FB TV": "yayinfb.m3u8", 
    "GS TV": "yayingstve.m3u8", 
    "BJK TV": "yayinbjk.m3u8"
}

def test_domain(domain_url):
    """Domain'in çalışıp çalışmadığını test et"""
    try:
        response = requests.get(domain_url, headers=HEADERS, timeout=3, verify=False)
        # Başarılı yanıt ve HTML içeriği kontrolü
        if response.status_code == 200 and "betorspin" in response.text.lower():
            return True, response.text
    except:
        pass
    return False, None

def find_working_domain():
    """63'ten başlayarak çalışan domain'i bul"""
    print("🔍 Çalışan domain aranıyor...")
    
    working_domains = []
    
    # 63'ten 80'e kadar dene
    for i in range(63, 81):
        domain_url = f"https://{i}betorspintv.live/"
        print(f"   {i}. deneme: {domain_url}", end=" ")
        
        is_working, html_content = test_domain(domain_url)
        
        if is_working:
            print("✅ ÇALIŞIYOR")
            working_domains.append((domain_url, html_content))
        else:
            print("❌ Çalışmıyor")
        
        # Çok hızlı istek atmamak için kısa bekleme
        time.sleep(0.1)
    
    # Diğer pattern'ları da dene
    other_patterns = [
        "https://betorspintv.live/",
        "https://betorspin.tv/",
        "https://betorspin.live/",
        "https://63betorspin.tv/",
    ]
    
    for domain_url in other_patterns:
        print(f"   Test: {domain_url}", end=" ")
        is_working, html_content = test_domain(domain_url)
        
        if is_working:
            print("✅ ÇALIŞIYOR")
            working_domains.append((domain_url, html_content))
        else:
            print("❌ Çalışmıyor")
    
    if working_domains:
        print(f"\n✅ {len(working_domains)} çalışan domain bulundu")
        # İlk çalışan domain'i döndür
        return working_domains[0]
    else:
        print("\n❌ Hiçbir domain çalışmıyor, varsayılan kullanılıyor")
        return "https://63betorspintv.live/", ""

def test_channel_url(base_url, channel_file):
    """Kanal URL'sini test et"""
    url = f"{base_url}{channel_file}"
    try:
        response = requests.head(url, timeout=3, verify=False, headers=HEADERS)
        return response.status_code == 200
    except:
        return False

def main():
    m3u_list = ["#EXTM3U"]
    
    try:
        print("=" * 60)
        print("📡 BetOrSpin M3U8 Playlist Oluşturucu")
        print("=" * 60)
        
        # 1. Yayın Sunucusunu Al
        print("\n📡 Sunucu adresi alınıyor...")
        try:
            domain_response = requests.get(DOMAIN_API, timeout=10)
            if domain_response.status_code == 200:
                domain_data = domain_response.json()
                base_url = domain_data.get("baseurl", "")
                if base_url:
                    print(f"✅ Sunucu URL (API'den): {base_url}")
                else:
                    print("⚠️ Base URL bulunamadı, son bilinen kullanılıyor...")
                    base_url = "https://bnw.zirvedesin119.lat/"
            else:
                print("⚠️ Domain API yanıt vermedi, son bilinen kullanılıyor...")
                base_url = "https://bnw.zirvedesin119.lat/"
        except:
            print("⚠️ Domain API'ye bağlanılamadı, son bilinen kullanılıyor...")
            base_url = "https://bnw.zirvedesin119.lat/"
        
        # 2. Referrer URL'yi bul (63'ten başlayarak)
        referrer_url, html_content = find_working_domain()
        print(f"\n✅ Seçilen Referrer URL: {referrer_url}")
        
        # 3. HTML'de kanal bilgilerini ara (opsiyonel)
        if html_content:
            # HTML'de channel?id= ifadelerini ara
            channel_ids = re.findall(r'channel\?id=([^"\']+)', html_content)
            if channel_ids:
                print(f"🔍 HTML'de {len(set(channel_ids))} benzersiz kanal ID'si bulundu")
        
        # 4. Kanal sayısını göster
        print(f"\n📺 Toplam {len(SABIT_KANALLAR)} kanal işleniyor...")
        
        # 5. Her kanal için M3U girişi oluştur
        working_channels = 0
        tested_channels = 0
        
        for name, file in SABIT_KANALLAR.items():
            url = f"{base_url}{file}"
            
            # Kanalı test et (isteğe bağlı)
            if tested_channels < 3:  # Sadece ilk 3 kanalı test et
                is_working = test_channel_url(base_url, file)
                status = "✓" if is_working else "?"
                print(f"   {status} {name} {'(Test Başarılı)' if is_working else '(Test Edilemedi)'}")
                tested_channels += 1
            else:
                print(f"   ✓ {name}")
            
            m3u_list.append(f'#EXTINF:-1 group-title="BetOrSpin Kanallar",{name}')
            m3u_list.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer_url}')
            m3u_list.append(f'{url}')
            
            working_channels += 1
        
        # 6. Dosyaya Kaydet
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"betorspin_{timestamp}.m3u8"
        simple_output_file = "betorspin.m3u8"  # Sabit isim
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        # Aynı zamanda sabit isimle de kaydet
        with open(simple_output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_list))
        
        # 7. Alternatif dosya (VLC için basit versiyon)
        vlc_output_file = "betorspin_vlc.m3u"
        vlc_list = ["#EXTM3U"]
        for name, file in SABIT_KANALLAR.items():
            url = f"{base_url}{file}"
            vlc_list.append(f'#EXTINF:-1 group-title="BetOrSpin",{name}')
            vlc_list.append(f'{url}')
        
        with open(vlc_output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(vlc_list))
        
        print("\n" + "=" * 60)
        print(f"✅ İŞLEM TAMAMLANDI!")
        print(f"📊 {working_channels} kanal eklendi")
        print(f"📂 {output_file} - Zaman damgalı dosya")
        print(f"📂 {simple_output_file} - Sabit isimli dosya")
        print(f"📂 {vlc_output_file} - VLC için basit versiyon")
        print("=" * 60)
        
        # 8. Kullanım talimatları
        print("\n📖 KULLANIM TALİMATLARI:")
        print("1. VLC Media Player'ı açın")
        print("2. Medya > Aç Dosya... yolunu izleyin")
        print(f"3. '{simple_output_file}' dosyasını seçin")
        print("4. veya doğrudan oynatma listesine sürükleyin")
        
        # 9. Hızlı test için
        print("\n🔗 HIZLI TEST LİNKLERİ (ilk 3 kanal):")
        for i, (name, file) in enumerate(list(SABIT_KANALLAR.items())[:3]):
            print(f"   {i+1}. {name}")
            print(f"      URL: {base_url}{file}")
            print(f"      Referrer: {referrer_url}")
            print()
            
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
