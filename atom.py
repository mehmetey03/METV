import requests
from bs4 import BeautifulSoup
import re

# AtomSporTV ana sayfası
ATOMSPORTV_URL = "https://atomsportv480.top/"
OUTPUT_FILE = "atom.m3u"  # atom.m3u olarak değiştirdim

GREEN = "\033[92m"
RESET = "\033[0m"

def debug_page():
    """
    Sayfanın yapısını debug etmek için
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://url24.link/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        print(f"Debug: Sayfa çekiliyor...")
        r = requests.get(ATOMSPORTV_URL, headers=headers, timeout=15)
        r.raise_for_status()
        r.encoding = 'utf-8'
        html = r.text
        
        # Sayfa boyutunu göster
        print(f"Sayfa boyutu: {len(html)} karakter")
        
        # HTML'yi kaydet (analiz için)
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML kaydedildi: debug_page.html")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Tüm linkleri bul
        all_links = soup.find_all('a')
        print(f"\nToplam link sayısı: {len(all_links)}")
        
        # 'matches' içeren linkleri filtrele
        match_links = [link for link in all_links if 'matches' in str(link.get('href', '')).lower()]
        print(f"'matches' içeren linkler: {len(match_links)}")
        
        # İlk 5 match linkini göster
        for i, link in enumerate(match_links[:5]):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:100]
            print(f"  {i+1}. Href: {href}")
            print(f"     Text: {text}")
        
        # Tüm div'leri kontrol et
        all_divs = soup.find_all('div')
        print(f"\nToplam div sayısı: {len(all_divs)}")
        
        # Class'ları kontrol et
        classes_found = set()
        for div in all_divs:
            if div.get('class'):
                classes_found.update(div.get('class'))
        
        print(f"\nBulunan class'lar (ilk 20): {list(classes_found)[:20]}")
        
        # Single-match class'ını ara
        single_matches = soup.find_all(class_='single-match')
        print(f"\n'single-match' class'lı elementler: {len(single_matches)}")
        
        # Tüm a etiketlerini ve href'lerini kontrol et
        print("\nTüm 'a' etiketlerinin href'leri:")
        for i, a in enumerate(all_links[:20]):
            href = a.get('href', '')
            if href:
                print(f"  {i+1}. {href[:100]}")
        
        return html
        
    except Exception as e:
        print(f"Debug hatası: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_all_content():
    """
    Tüm içeriği çek (debug için)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        r = requests.get(ATOMSPORTV_URL, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        
        # Tüm maç linklerini regex ile bul
        matches = re.findall(r'href="(matches\?id=[^"]+)"', r.text)
        unique_matches = list(set(matches))
        
        print(f"Regex ile bulunan match linkleri: {len(unique_matches)}")
        for match in unique_matches[:10]:
            print(f"  - {match}")
        
        return unique_matches
        
    except Exception as e:
        print(f"İçerik çekme hatası: {e}")
        return []

def create_simple_m3u(match_links):
    """
    Basit M3U dosyası oluştur
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for i, match_link in enumerate(match_links):
            match_id = match_link.split('=')[-1] if '=' in match_link else match_link
            channel_name = f"Channel {i+1} - {match_id}"
            
            # Tam URL'yi oluştur
            full_url = f"{ATOMSPORTV_URL}{match_link}"
            
            f.write(f'#EXTINF:-1 tvg-id="{match_id}" group-title="AtomSporTV",{channel_name}\n')
            f.write(f'#EXTVLCOPT:http-referrer={ATOMSPORTV_URL}\n')
            f.write(full_url + "\n")
    
    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    print(f"Toplam {len(match_links)} kanal eklendi.")

# --- ÇALIŞTIR ---
print(f"{GREEN}AtomSporTV Debug & M3U Oluşturucu{RESET}")
print("=" * 50)

# 1. Önce debug yapalım
print("\n1. Sayfa yapısı analiz ediliyor...")
debug_page()

print("\n" + "=" * 50)

# 2. Regex ile tüm maç linklerini bul
print("\n2. Regex ile içerik taraması...")
all_matches = get_all_content()

if all_matches:
    print("\n3. M3U dosyası oluşturuluyor...")
    create_simple_m3u(all_matches)
    
    # GitHub'a eklemek için
    print("\n" + "=" * 50)
    print("GitHub komutları:")
    print(f"git add {OUTPUT_FILE}")
    print("git commit -m 'AtomSporTV M3U güncellemesi'")
    print("git push")
else:
    print("\n❌ Hiç maç/kanal linki bulunamadı!")
    print("Sayfa yapısı değişmiş olabilir veya erişim engellenmiş olabilir.")
