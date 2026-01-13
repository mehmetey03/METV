import requests
from bs4 import BeautifulSoup
import re
import html
import unicodedata
import time

DOMAIN_TXT_URL = "https://raw.githubusercontent.com/mehmetey03/inatdom/refs/heads/main/domain.txt"
OUTPUT_FILE = "inat.m3u"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# -------------------- Yardımcı Fonksiyon --------------------
def clean_text(text):
    """Metni düzgün Türkçe karakterlerle düzeltir"""
    if not text:
        return ""
    text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    return text

def get_active_domain():
    """ GitHub domain.txt → guncel_domain çek """
    r = requests.get(DOMAIN_TXT_URL, timeout=10)
    if r.status_code != 200:
        raise Exception("domain.txt okunamadı!")
    txt = r.text
    m = re.search(r"guncel_domain\s*=\s*(https?://[^\s]+)", txt)
    if not m:
        raise Exception("guncel_domain bulunamadı!")
    return m.group(1).strip()

def get_channel_m3u8(domain, channel_id):
    """Kanal ID'sinden m3u8 linkini oluştur"""
    try:
        # API endpoint'ini bulmak için ana sayfayı kontrol et
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": domain
        }
        
        # Önce ana sayfayı çek
        r = requests.get(domain, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        html_text = r.text
        
        # JavaScript dosyalarını bul
        js_patterns = [
            r'src="([^"]+\.js)"',
            r'src=\'([^\']+\.js)\'',
            r'<script[^>]+src="([^"]+)"[^>]*>'
        ]
        
        js_files = []
        for pattern in js_patterns:
            js_files.extend(re.findall(pattern, html_text))
        
        # API endpoint'ini bulmak için js dosyalarını ara
        api_base = None
        for js_file in js_files[:5]:  # İlk 5 js dosyasını kontrol et
            try:
                if not js_file.startswith('http'):
                    if js_file.startswith('/'):
                        js_url = domain + js_file
                    else:
                        js_url = domain + '/' + js_file
                else:
                    js_url = js_file
                    
                print(f"{YELLOW}[?] JS dosyası kontrol ediliyor: {js_url}{RESET}")
                
                js_r = requests.get(js_url, headers=headers, timeout=5)
                js_content = js_r.text
                
                # API endpoint pattern'leri
                patterns = [
                    r'baseurl\s*=\s*["\']([^"\']+)["\']',
                    r'apiUrl\s*:\s*["\']([^"\']+)["\']',
                    r'streamUrl\s*:\s*["\']([^"\']+)["\']',
                    r'BASE_URL\s*=\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.search(pattern, js_content)
                    if matches:
                        api_base = matches.group(1)
                        print(f"{GREEN}[✓] API endpoint bulundu: {api_base}{RESET}")
                        break
                
                if api_base:
                    break
                    
            except Exception as e:
                continue
        
        # API endpoint bulunamazsa fallback URL
        if not api_base:
            print(f"{YELLOW}[!] API endpoint bulunamadı, fallback URL kullanılıyor{RESET}")
            # Fallback URL pattern'leri
            fallback_patterns = [
                f"{domain}/stream/",
                f"{domain}/live/",
                f"{domain}/hls/"
            ]
            
            for fallback in fallback_patterns:
                try:
                    test_url = f"{fallback}{channel_id}.m3u8"
                    test_r = requests.head(test_url, headers=headers, timeout=3)
                    if test_r.status_code < 400:
                        api_base = fallback
                        print(f"{GREEN}[✓] Fallback endpoint bulundu: {api_base}{RESET}")
                        break
                except:
                    continue
        
        if not api_base:
            # Son çare olarak domain'den tahmin et
            api_base = f"{domain}/stream/"
            print(f"{YELLOW}[!] Tahmini endpoint kullanılıyor: {api_base}{RESET}")
        
        m3u8_url = f"{api_base}{channel_id}.m3u8"
        
        # URL'i kontrol et
        check_r = requests.head(m3u8_url, headers=headers, timeout=5)
        if check_r.status_code == 200:
            print(f"{GREEN}[✓] M3U8 linki doğrulandı: {m3u8_url}{RESET}")
            return m3u8_url
        else:
            print(f"{YELLOW}[!] M3U8 linki hata verdi (HTTP {check_r.status_code}){RESET}")
            return f"{api_base}{channel_id}.m3u8"
            
    except Exception as e:
        print(f"{RED}[!] M3U8 hatası: {e}{RESET}")
        return ""

def get_matches(domain):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"{YELLOW}[?] Ana sayfa çekiliyor: {domain}{RESET}")
        r = requests.get(domain, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, "html.parser")
        maclar = []
        
        # Birden fazla seçici deneyelim
        selectors = [
            "a.channel-item",
            "div.channel-item",
            "li.channel-item",
            ".match-item",
            ".live-item",
            "a[href*='channel']",
            "div[onclick*='channel']"
        ]
        
        all_items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                print(f"{GREEN}[✓] {len(items)} öğe bulundu ({selector}){RESET}")
                all_items.extend(items)
        
        # Eğer hala öğe yoksa, tüm linkleri kontrol et
        if not all_items:
            print(f"{YELLOW}[!] Selector ile öğe bulunamadı, tüm linkler kontrol ediliyor...{RESET}")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                if 'channel' in link.get('href', '').lower() or 'id=' in link.get('href', ''):
                    all_items.append(link)
        
        print(f"{GREEN}[✓] Toplam {len(all_items)} öğe incelenecek{RESET}")
        
        for item in all_items[:50]:  # İlk 50 öğeyi kontrol et
            try:
                # Href'ten kanal ID'sini çıkar
                href = item.get("href", "")
                if not href:
                    continue
                    
                # URL parametrelerinden ID'yi çıkar
                m = re.search(r'(?:id|channel)=([^&]+)', href)
                if not m:
                    continue
                    
                kanal_id = m.group(1).strip()
                if not kanal_id:
                    continue
                
                print(f"{YELLOW}[?] Kanal ID bulundu: {kanal_id}{RESET}")
                
                # Kanal adını bul
                kanal_adi = ""
                name_selectors = [
                    ".channel-name",
                    ".match-name",
                    ".team-name",
                    ".title",
                    "h3", "h4", "h5",
                    "span",
                    "div"
                ]
                
                for selector in name_selectors:
                    name_el = item.select_one(selector)
                    if name_el:
                        kanal_adi = clean_text(name_el.get_text(strip=True))
                        if kanal_adi:
                            break
                
                if not kanal_adi:
                    kanal_adi = f"Kanal {kanal_id}"
                
                # Saat/durum bilgisini bul
                saat = ""
                status_selectors = [".channel-status", ".time", ".status", ".date"]
                for selector in status_selectors:
                    status_el = item.select_one(selector)
                    if status_el:
                        saat = clean_text(status_el.get_text(strip=True))
                        break
                
                # Canlı durumunu kontrol et
                live = False
                live_indicators = [
                    ".live-badge",
                    ".live-indicator",
                    ".live-now",
                    ".live",
                    "[class*='live']",
                    "[class*='streaming']"
                ]
                for indicator in live_indicators:
                    if item.select_one(indicator):
                        live = True
                        break
                
                # M3U8 linkini al
                print(f"{YELLOW}[?] M3U8 linki alınıyor: {kanal_id}{RESET}")
                m3u8_link = get_channel_m3u8(domain, kanal_id)
                if not m3u8_link:
                    print(f"{RED}[!] M3U8 linki alınamadı: {kanal_id}{RESET}")
                    continue
                
                # Kanal bilgilerini oluştur
                display_name = f"{saat} - {kanal_adi}" if saat else kanal_adi
                if live:
                    display_name = "🔴 " + display_name
                
                mac = {
                    "saat": saat,
                    "takimlar": kanal_adi,
                    "canli": live,
                    "dosya": m3u8_link,
                    "kanal_adi": display_name,
                    "tvg_id": kanal_id
                }
                
                maclar.append(mac)
                print(f"{GREEN}[✓] Kanal eklendi: {display_name}{RESET}")
                
            except Exception as e:
                print(f"{RED}[!] Öğe işlenirken hata: {e}{RESET}")
                continue
        
        return maclar

    except Exception as e:
        print(f"{RED}[!] get_matches hatası: {e}{RESET}")
        return []

def create_m3u(maclar, domain):
    if not maclar:
        print(f"{RED}[!] M3U oluşturulamadı: Maç bulunamadı{RESET}")
        return
    
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U x-tvg-url=\"\"\n")
            for idx, kanal in enumerate(maclar, 1):
                # TVG ID için uygun format
                tvg_id = kanal["tvg_id"].replace(" ", "_").replace(":", "_")
                
                # Kanal adını temizle
                channel_name = kanal["kanal_adi"]
                channel_name = re.sub(r'[^\w\s\-\.:]', '', channel_name)
                
                # EXTINF satırı
                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{channel_name}" group-title="İnat Spor",{channel_name}\n')
                
                # Referer ve user-agent ekle
                f.write(f'#EXTVLCOPT:http-referrer={domain}\n')
                f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n')
                
                # Stream URL
                f.write(kanal["dosya"] + "\n\n")
        
        print(f"{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE} ({len(maclar)} kanal){RESET}")
        
        # İçeriği göster
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"{YELLOW}[?] İlk 5 kanal:{RESET}")
            for i, line in enumerate(lines[:15]):
                if line.strip():
                    print(f"  {i+1}: {line.strip()}")
                    
    except Exception as e:
        print(f"{RED}[!] M3U dosyası yazılırken hata: {e}{RESET}")

# -------------------- ÇALIŞTIR --------------------
if __name__ == "__main__":
    print(f"{GREEN}=== İnat Spor M3U Oluşturucu ==={RESET}")
    try:
        print("1. Güncel domain alınıyor...")
        domain = get_active_domain()
        print(f"{GREEN}[✓] Kullanılan domain: {domain}{RESET}")
        
        print("\n2. Maçlar çekiliyor...")
        maclar = get_matches(domain)
        print(f"{GREEN}[✓] {len(maclar)} geçerli maç/kanal bulundu.{RESET}")
        
        if maclar:
            print("\n3. M3U oluşturuluyor...")
            create_m3u(maclar, domain)
            
            # Özet
            print(f"\n{GREEN}=== İŞLEM TAMAMLANDI ==={RESET}")
            print(f"Toplam Kanal: {len(maclar)}")
            live_count = sum(1 for m in maclar if m["canli"])
            print(f"Canlı Yayın: {live_count}")
            print(f"Bekleyen: {len(maclar) - live_count}")
            print(f"Çıktı Dosyası: {OUTPUT_FILE}")
        else:
            print(f"{RED}[!] Maç bulunamadı, M3U oluşturulamadı.{RESET}")
            
    except Exception as e:
        print(f"{RED}[!] Ana hata: {e}{RESET}")
        import traceback
        traceback.print_exc()
