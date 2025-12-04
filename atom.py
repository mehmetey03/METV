from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

# AtomSporTV ana sayfası
ATOMSPORTV_URL = "https://atomsportv480.top/"
OUTPUT_FILE = "atom.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

def setup_driver():
    """Selenium driver'ını kur"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Arka planda çalıştır
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_content_with_selenium():
    """Selenium ile dinamik içeriği çek"""
    print("Selenium ile sayfa yükleniyor...")
    driver = None
    
    try:
        driver = setup_driver()
        driver.get(ATOMSPORTV_URL)
        
        # Sayfanın tam yüklenmesini bekle
        time.sleep(5)
        
        # Maçların yüklenmesi için daha fazla bekle
        print("Maç listesi yükleniyor, bekleniyor...")
        time.sleep(3)
        
        # Sayfa kaynağını al
        page_source = driver.page_source
        
        # Debug için kaydet
        with open("selenium_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Selenium HTML kaydedildi: selenium_page.html")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Tüm linkleri kontrol et
        all_links = soup.find_all('a')
        print(f"\nSelenium ile bulunan toplam link: {len(all_links)}")
        
        # matches içeren linkleri bul
        match_links = []
        for link in all_links:
            href = link.get('href', '')
            if href and 'matches' in href.lower():
                match_links.append((href, link.get_text(strip=True)))
        
        print(f"'matches' içeren linkler: {len(match_links)}")
        
        # Linkleri göster
        for i, (href, text) in enumerate(match_links[:10]):
            print(f"  {i+1}. Href: {href}")
            print(f"     Text: {text[:50]}...")
        
        # Eğer hala match yoksa, iframe veya başka elementleri kontrol et
        if not match_links:
            print("\nMatch linki bulunamadı, alternatif tarama...")
            
            # Tüm onclick eventlerini kontrol et
            onclick_elements = soup.find_all(attrs={"onclick": True})
            print(f"onclick elementleri: {len(onclick_elements)}")
            
            # Tüm script tag'lerini kontrol et
            scripts = soup.find_all('script')
            print(f"Script tag'leri: {len(scripts)}")
            
            # Script'lerde matches kelimesini ara
            matches_in_scripts = []
            for script in scripts:
                if script.string and 'matches' in script.string.lower():
                    matches_in_scripts.append(script.string[:200])
            
            print(f"'matches' içeren script'ler: {len(matches_in_scripts)}")
        
        return match_links
        
    except Exception as e:
        print(f"Selenium hatası: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if driver:
            driver.quit()

def get_matches_from_api():
    """
    API veya alternatif kaynaktan maçları çekmeyi dene
    """
    print("\nAlternatif kaynaklardan veri çekiliyor...")
    
    # Farklı URL'leri deneyelim
    urls_to_try = [
        "https://atomsportv480.top/",
        "https://atomsportv481.top/",
        "https://trgoals1472.xyz/",
    ]
    
    all_matches = []
    
    for url in urls_to_try:
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            print(f"\n{url} deneniyor...")
            r = requests.get(url, headers=headers, timeout=10)
            
            # Regex ile tüm matches linklerini bul
            matches = re.findall(r'(matches\?id=[^"\s]+)', r.text)
            if matches:
                unique_matches = list(set(matches))
                print(f"  {len(unique_matches)} match bulundu")
                all_matches.extend([(match, "") for match in unique_matches])
                
                # İlk 3'ü göster
                for match in unique_matches[:3]:
                    print(f"    - {match}")
            else:
                print("  Match bulunamadı")
                
        except Exception as e:
            print(f"  Hata: {e}")
    
    return all_matches

def create_m3u_from_links(match_links):
    """Linklerden M3U dosyası oluştur"""
    if not match_links:
        print("❌ M3U oluşturmak için yeterli veri yok!")
        return
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for i, (href, text) in enumerate(match_links):
            # Href tam URL mi kontrol et
            if href.startswith('http'):
                full_url = href
            else:
                full_url = f"{ATOMSPORTV_URL}{href}" if not href.startswith('/') else f"{ATOMSPORTV_URL.rstrip('/')}{href}"
            
            # Match ID'yi çıkar
            match_id = ""
            if 'id=' in href:
                match_id = href.split('id=')[-1].split('&')[0]
            else:
                match_id = href.split('/')[-1] if '/' in href else href
            
            # Kanal adı
            if text:
                channel_name = text
            else:
                channel_name = f"Channel {i+1} - {match_id}"
            
            # Kısa isim
            short_name = channel_name[:50]
            
            f.write(f'#EXTINF:-1 tvg-id="{match_id}" group-title="AtomSporTV",{short_name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={ATOMSPORTV_URL}\n')
            f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n')
            f.write(full_url + "\n")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {len(match_links)} kanal eklendi.")

# --- ANA PROGRAM ---
print(f"{GREEN}AtomSporTV M3U Oluşturucu (Selenium){RESET}")
print("=" * 60)

# 1. Önce Selenium ile deneyelim
print("\n1. Selenium ile dinamik içerik çekiliyor...")
selenium_matches = get_content_with_selenium()

if selenium_matches:
    print("\n2. M3U dosyası oluşturuluyor...")
    create_m3u_from_links(selenium_matches)
else:
    print("\nSelenium ile maç bulunamadı, alternatif yöntemler deneniyor...")
    
    # 2. API/alternatif kaynakları dene
    print("\n3. Alternatif kaynaklardan veri çekiliyor...")
    api_matches = get_matches_from_api()
    
    if api_matches:
        print("\n4. M3U dosyası oluşturuluyor...")
        create_m3u_from_links(api_matches)
    else:
        print("\n❌ Hiçbir kaynaktan veri alınamadı!")
        print("\nOlası nedenler:")
        print("1. Sayfa yapısı tamamen değişmiş")
        print("2. JavaScript engelleniyor")
        print("3. IP/Cihaz engeli var")
        print("4. Site çalışmıyor olabilir")
        
        # Fallback: Manuel liste
        print("\n5. Manuel fallback listesi oluşturuluyor...")
        manual_matches = [
            ("matches?id=bein-sports-1", "BEIN SPORTS 1"),
            ("matches?id=bein-sports-2", "BEIN SPORTS 2"),
            ("matches?id=bein-sports-3", "BEIN SPORTS 3"),
            ("matches?id=bein-sports-4", "BEIN SPORTS 4"),
            ("matches?id=s-sport", "S SPORT"),
            ("matches?id=s-sport-2", "S SPORT 2"),
            ("matches?id=tivibu-spor-1", "TİVİBU SPOR 1"),
            ("matches?id=tivibu-spor-2", "TİVİBU SPOR 2"),
            ("matches?id=aspor", "ASPOR"),
            ("matches?id=trt-spor", "TRT SPOR"),
        ]
        
        create_m3u_from_links(manual_matches)

print("\n" + "=" * 60)
print("GitHub komutları:")
print(f"git add {OUTPUT_FILE}")
print('git commit -m "AtomSporTV M3U güncellemesi"')
print("git push")
