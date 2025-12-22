#!/usr/bin/env python3
"""
Taraftariumizle.org'dan m3u8 linklerini çeken ve M3U oluşturan script
Playwright ile browser otomasyonu kullanır
"""

import re
import json
import time
from playwright.sync_api import sync_playwright
import urllib3

# SSL uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    START_URL = "https://taraftariumizle.org"
    OUTPUT_FILE = "taraftariumizle.m3u"
    
    # Kanal listesi - güncellenmiş
    channels = [
        ("androstreamlivebiraz1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs2", 'TR:beIN Sport 2 HD'),
        ("androstreamlivebs3", 'TR:beIN Sport 3 HD'),
        ("androstreamlivebs4", 'TR:beIN Sport 4 HD'),
        ("androstreamlivebs5", 'TR:beIN Sport 5 HD'),
        ("androstreamlivebsm1", 'TR:beIN Sport Max 1 HD'),
        ("androstreamlivebsm2", 'TR:beIN Sport Max 2 HD'),
        ("androstreamlivess1", 'TR:S Sport 1 HD'),
        ("androstreamlivess2", 'TR:S Sport 2 HD'),
        ("androstreamlivets", 'TR:Tivibu Sport HD'),
        ("androstreamlivets1", 'TR:Tivibu Sport 1 HD'),
        ("androstreamlivets2", 'TR:Tivibu Sport 2 HD'),
        ("androstreamlivets3", 'TR:Tivibu Sport 3 HD'),
        ("androstreamlivets4", 'TR:Tivibu Sport 4 HD'),
        ("androstreamlivesm1", 'TR:Smart Sport 1 HD'),
        ("androstreamlivesm2", 'TR:Smart Sport 2 HD'),
        ("androstreamlivees1", 'TR:Euro Sport 1 HD'),
        ("androstreamlivees2", 'TR:Euro Sport 2 HD'),
        ("androstreamlivetb", 'TR:Tabii HD'),
        ("androstreamlivetb1", 'TR:Tabii 1 HD'),
        ("androstreamlivetb2", 'TR:Tabii 2 HD'),
        ("androstreamlivetb3", 'TR:Tabii 3 HD'),
        ("androstreamlivetb4", 'TR:Tabii 4 HD'),
        ("androstreamlivetb5", 'TR:Tabii 5 HD'),
        ("androstreamlivetb6", 'TR:Tabii 6 HD'),
        ("androstreamlivetb7", 'TR:Tabii 7 HD'),
        ("androstreamlivetb8", 'TR:Tabii 8 HD'),
        ("androstreamliveexn", 'TR:Exxen HD'),
        ("androstreamliveexn1", 'TR:Exxen 1 HD'),
        ("androstreamliveexn2", 'TR:Exxen 2 HD'),
        ("androstreamliveexn3", 'TR:Exxen 3 HD'),
        ("androstreamliveexn4", 'TR:Exxen 4 HD'),
        ("androstreamliveexn5", 'TR:Exxen 5 HD'),
        ("androstreamliveexn6", 'TR:Exxen 6 HD'),
        ("androstreamliveexn7", 'TR:Exxen 7 HD'),
        ("androstreamliveexn8", 'TR:Exxen 8 HD'),
    ]
    
    print("🚀 Taraftariumizle M3U8 Fetcher başlatılıyor...")
    
    with sync_playwright() as p:
        # Tarayıcıyı başlat (headless modda)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # 1. Adım: Ana sayfaya git
            print("📡 Ana sayfaya erişiliyor...")
            page.goto(START_URL, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # 2. Adım: AMP sayfa linkini bul
            amp_link = None
            try:
                amp_link = page.locator('link[rel="amphtml"]').get_attribute('href')
                if amp_link:
                    print(f"🔗 AMP link bulundu: {amp_link}")
            except:
                print("⚠️  AMP link bulunamadı, alternatif yöntem deneniyor...")
            
            # AMP link yoksa ana sayfayı kullan
            target_url = amp_link if amp_link else START_URL
            
            # 3. Adım: Hedef sayfaya git
            print(f"🌐 Hedef sayfaya gidiliyor: {target_url}")
            page.goto(target_url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            
            # 4. Adım: Sayfa kaynağını al
            page_content = page.content()
            
            # 5. Adım: m3u8 sunucularını bul
            print("🔍 M3U8 sunucuları aranıyor...")
            
            # Pattern 1: baseUrls değişkenini ara
            server_patterns = [
                r'baseUrls\s*=\s*\[(.*?)\]',
                r'servers\s*:\s*\[(.*?)\]',
                r'var\s+servers\s*=\s*\[(.*?)\]',
                r'"server"\s*:\s*\[(.*?)\]'
            ]
            
            servers = []
            
            for pattern in server_patterns:
                match = re.search(pattern, page_content, re.DOTALL)
                if match:
                    try:
                        # JSON formatında olabilir
                        content = match.group(1)
                        # Tırnak işaretlerini temizle
                        content = content.replace('"', '').replace("'", "")
                        # Virgülle ayır ve temizle
                        found = [s.strip() for s in content.split(',') if s.strip()]
                        servers.extend([s for s in found if s.startswith('http')])
                        if servers:
                            print(f"✅ {len(servers)} sunucu bulundu (pattern: {pattern[:30]}...)")
                            break
                    except Exception as e:
                        print(f"⚠️  Pattern işleme hatası: {e}")
            
            # Pattern 2: Doğrudan m3u8 linklerini ara
            if not servers:
                m3u8_patterns = [
                    r'https?://[^\s"\']+\.m3u8[^\s"\']*',
                    r'src="(https?://[^"]+\.m3u8[^"]*)"',
                    r"src='(https?://[^']+\.m3u8[^']*)'"
                ]
                
                for pattern in m3u8_patterns:
                    matches = re.findall(pattern, page_content, re.IGNORECASE)
                    if matches:
                        # Base URL'leri çıkar
                        for match in matches:
                            base_url = match.split('/checklist/')[0] if '/checklist/' in match else match.rsplit('/', 1)[0]
                            if base_url.startswith('http'):
                                servers.append(base_url)
                        servers = list(set(servers))  # Tekilleştir
                        if servers:
                            print(f"✅ {len(servers)} sunucu bulundu (m3u8 pattern)")
                            break
            
            # Pattern 3: JavaScript içinde URL'leri ara
            if not servers:
                js_url_pattern = r'https?://[^\s"\']+/checklist/[^\s"\']*'
                matches = re.findall(js_url_pattern, page_content)
                for match in matches:
                    base_url = match.split('/checklist/')[0]
                    if base_url.startswith('http'):
                        servers.append(base_url)
                servers = list(set(servers))
                if servers:
                    print(f"✅ {len(servers)} sunucu bulundu (checklist pattern)")
            
            if not servers:
                print("❌ Hiç sunucu bulunamadı!")
                return
            
            print(f"📊 Toplam {len(servers)} sunucu bulundu:")
            for i, server in enumerate(servers[:5], 1):  # İlk 5'i göster
                print(f"  {i}. {server}")
            if len(servers) > 5:
                print(f"  ... ve {len(servers)-5} daha")
            
            # 6. Adım: Sunucuları test et
            print("🧪 Sunucular test ediliyor...")
            active_servers = []
            test_channel = "androstreamlivebs1"
            
            for server in servers:
                server = server.rstrip('/')
                # İki farklı URL formatını dene
                test_urls = [
                    f"{server}/checklist/{test_channel}.m3u8",
                    f"{server}/{test_channel}.m3u8"
                ]
                
                for test_url in test_urls:
                    try:
                        print(f"  Testing: {test_url[:80]}...")
                        response = page.context.request.get(
                            test_url,
                            headers={
                                'Referer': target_url,
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            },
                            timeout=5000
                        )
                        
                        if response.status in [200, 206]:
                            content = response.text()
                            if '#EXTM3U' in content or '.m3u8' in content:
                                active_servers.append(server)
                                print(f"  ✅ Aktif sunucu: {server}")
                                break
                    except Exception as e:
                        continue
                
                # Her sunucu için maksimum 1 saniye bekle
                time.sleep(0.5)
            
            if not active_servers:
                print("⚠️  Hiç aktif sunucu bulunamadı, bulunan sunucuları kullanıyoruz...")
                active_servers = servers[:3]  # İlk 3 sunucuyu dene
            
            print(f"🎯 {len(active_servers)} aktif sunucu kullanılacak")
            
            # 7. Adım: M3U dosyasını oluştur
            print("📝 M3U dosyası oluşturuluyor...")
            
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U x-tvg-url=\"\"\n\n")
                
                for server in active_servers:
                    server = server.rstrip('/')
                    for channel_id, channel_name in channels:
                        # İki farklı URL formatını oluştur
                        m3u8_url = f"{server}/checklist/{channel_id}.m3u8"
                        alt_m3u8_url = f"{server}/{channel_id}.m3u8"
                        
                        # Kanal için M3U girişi
                        f.write(f'#EXTINF:-1 tvg-id="" tvg-name="{channel_name}" tvg-logo="" group-title="TR Sports",{channel_name}\n')
                        f.write(f"{m3u8_url}\n\n")
            
            print(f"✅ {OUTPUT_FILE} dosyası başarıyla oluşturuldu!")
            print(f"📊 İstatistikler:")
            print(f"   • Toplam kanal: {len(channels)}")
            print(f"   • Aktif sunucu: {len(active_servers)}")
            print(f"   • Toplam kayıt: {len(channels) * len(active_servers)}")
            
            # Ek bilgi dosyası oluştur
            with open("server_info.json", "w", encoding="utf-8") as info_file:
                info_data = {
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "active_servers": active_servers,
                    "total_channels": len(channels),
                    "output_file": OUTPUT_FILE
                }
                json.dump(info_data, info_file, indent=2, ensure_ascii=False)
            
            print("📋 server_info.json oluşturuldu")
            
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
        finally:
            # Tarayıcıyı kapat
            browser.close()
            print("👋 Tarayıcı kapatıldı")

if __name__ == "__main__":
    main()
