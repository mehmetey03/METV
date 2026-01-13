import requests
from bs4 import BeautifulSoup
import re
import html
import unicodedata
import json

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
    # Fazla boşlukları temizle
    text = re.sub(r'\s+', ' ', text).strip()
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
        # İlk olarak channel.html sayfasını çek ve baseurl'i bul
        channel_url = f"{domain}/channel.html?id={channel_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": domain
        }
        
        print(f"{YELLOW}[?] Channel sayfası çekiliyor: {channel_url}{RESET}")
        
        r = requests.get(channel_url, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        html_text = r.text
        
        # baseurl'i ara (JavaScript içinde)
        baseurl_patterns = [
            r'baseurl\s*=\s*["\']([^"\']+)["\']',
            r'BASE_URL\s*=\s*["\']([^"\']+)["\']',
            r'streamUrl\s*=\s*["\']([^"\']+)["\']'
        ]
        
        baseurl = None
        for pattern in baseurl_patterns:
            match = re.search(pattern, html_text)
            if match:
                baseurl = match.group(1).strip()
                print(f"{GREEN}[✓] BaseURL bulundu: {baseurl}{RESET}")
                break
        
        # Eğer baseurl bulunamazsa, yayın sunucusu URL'ini ara
        if not baseurl:
            # Alternatif pattern: sunucu URL'si
            server_patterns = [
                r'https?://[^"\']+\.m3u8',
                r'src\s*=\s*["\']([^"\']+\.m3u8)["\']',
                r'file\s*:\s*["\']([^"\']+\.m3u8)["\']'
            ]
            
            for pattern in server_patterns:
                matches = re.findall(pattern, html_text)
                for match in matches:
                    if channel_id in match:
                        baseurl = match.replace(channel_id + ".m3u8", "")
                        print(f"{GREEN}[✓] Alternatif URL bulundu: {baseurl}{RESET}")
                        break
                if baseurl:
                    break
        
        # Eğer hala baseurl yoksa, domain'den tahmin et
        if not baseurl:
            # Yaygın m3u8 path pattern'leri
            common_paths = [
                f"{domain}/stream/",
                f"{domain}/live/",
                f"{domain}/hls/",
                f"{domain}/tv/",
                "https://tv.ssps.xyz/hls/",
                "https://stream.ssps.xyz/hls/",
                "https://live.ssps.xyz/hls/"
            ]
            
            for path in common_paths:
                baseurl = path
                print(f"{YELLOW}[!] Tahmini baseurl kullanılıyor: {baseurl}{RESET}")
                break
        
        # m3u8 URL'ini oluştur
        m3u8_url = f"{baseurl}{channel_id}.m3u8"
        
        print(f"{GREEN}[✓] M3U8 URL oluşturuldu: {m3u8_url}{RESET}")
        return m3u8_url
            
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
        
        # Tüm channel-item'ları bul
        channel_items = soup.select("a.channel-item")
        print(f"{GREEN}[✓] {len(channel_items)} kanal öğesi bulundu{RESET}")
        
        for item in channel_items:
            try:
                # Href'ten kanal ID'sini çıkar
                href = item.get("href", "")
                if not href:
                    continue
                
                # URL parametrelerinden ID'yi çıkar
                match = re.search(r'id=([^&]+)', href)
                if not match:
                    continue
                    
                kanal_id = match.group(1).strip()
                if not kanal_id:
                    continue
                
                print(f"{YELLOW}[?] Kanal ID bulundu: {kanal_id}{RESET}")
                
                # Kanal adını bul
                kanal_adi = ""
                name_el = item.select_one(".channel-name")
                if name_el:
                    # İkonları temizle
                    kanal_adi = clean_text(name_el.get_text(strip=True))
                    # İkonları kaldır
                    kanal_adi = re.sub(r'^<i[^>]*></i>\s*', '', kanal_adi)
                
                if not kanal_adi:
                    kanal_adi = f"Kanal {kanal_id}"
                
                # Saat/durum bilgisini bul
                saat = ""
                status_el = item.select_one(".channel-status")
                if status_el:
                    saat = clean_text(status_el.get_text(strip=True))
                
                # Kategori bilgisini al
                kategori = item.get("data-category", "")
                
                # Canlı durumunu belirle (7/24 veya saat bilgisine göre)
                live = False
                if saat == "7/24" or ":" in saat:
                    live = True
                
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
                
                # TVG ID için uygun format
                tvg_id = kanal_id.replace(" ", "_").replace(":", "_")
                
                mac = {
                    "saat": saat,
                    "takimlar": kanal_adi,
                    "canli": live,
                    "dosya": m3u8_link,
                    "kanal_adi": display_name,
                    "tvg_id": tvg_id,
                    "kategori": kategori
                }
                
                maclar.append(mac)
                print(f"{GREEN}[✓] Kanal eklendi: {display_name}{RESET}")
                
            except Exception as e:
                print(f"{RED}[!] Öğe işlenirken hata: {e}{RESET}")
                continue
        
        return maclar

    except Exception as e:
        print(f"{RED}[!] get_matches hatası: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return []

def create_m3u(maclar, domain):
    if not maclar:
        print(f"{RED}[!] M3U oluşturulamadı: Kanal bulunamadı{RESET}")
        return
    
    try:
        # Kategorilere göre grupla
        kategoriler = {}
        for kanal in maclar:
            kategori = kanal.get("kategori", "genel")
            if kategori not in kategoriler:
                kategoriler[kategori] = []
            kategoriler[kategori].append(kanal)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U x-tvg-url=\"\"\n\n")
            
            # Tüm kanallar için
            for kategori, kanallar in kategoriler.items():
                grup_adi = kategori.capitalize() if kategori else "Genel"
                
                for idx, kanal in enumerate(kanallar, 1):
                    # Kanal adını temizle
                    channel_name = kanal["kanal_adi"]
                    channel_name = re.sub(r'[^\w\s\-\.:🔴]', '', channel_name)
                    
                    # EXTINF satırı
                    f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{channel_name}" group-title="İnat {grup_adi}",{channel_name}\n')
                    
                    # Referer ve user-agent ekle
                    f.write(f'#EXTVLCOPT:http-referrer={domain}\n')
                    f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n')
                    
                    # Stream URL
                    f.write(kanal["dosya"] + "\n\n")
        
        print(f"{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE} ({len(maclar)} kanal){RESET}")
        
        # İstatistikleri göster
        print(f"\n{YELLOW}[📊] İSTATİSTİKLER:{RESET}")
        print(f"Toplam Kanal: {len(maclar)}")
        
        for kategori, kanallar in kategoriler.items():
            grup_adi = kategori.capitalize() if kategori else "Genel"
            print(f"  {grup_adi}: {len(kanallar)} kanal")
        
        live_count = sum(1 for m in maclar if m["canli"])
        print(f"Canlı Yayın: {live_count}")
        
        # İlk 5 kanalı göster
        print(f"\n{YELLOW}[📺] İLK 5 KANAL:{RESET}")
        for i, kanal in enumerate(maclar[:5], 1):
            print(f"  {i}. {kanal['kanal_adi']}")
            
    except Exception as e:
        print(f"{RED}[!] M3U dosyası yazılırken hata: {e}{RESET}")
        import traceback
        traceback.print_exc()

# -------------------- ÇALIŞTIR --------------------
if __name__ == "__main__":
    print(f"{GREEN}{'='*50}{RESET}")
    print(f"{GREEN}     İnat Spor M3U Oluşturucu v2.0     {RESET}")
    print(f"{GREEN}{'='*50}{RESET}\n")
    
    try:
        print("1. Güncel domain alınıyor...")
        domain = get_active_domain()
        print(f"{GREEN}[✓] Kullanılan domain: {domain}{RESET}")
        
        print("\n2. Kanal listesi çekiliyor...")
        maclar = get_matches(domain)
        print(f"{GREEN}[✓] {len(maclar)} geçerli kanal bulundu.{RESET}")
        
        if maclar:
            print("\n3. M3U dosyası oluşturuluyor...")
            create_m3u(maclar, domain)
            
            print(f"\n{GREEN}{'='*50}{RESET}")
            print(f"{GREEN}      İŞLEM BAŞARIYLA TAMAMLANDI      {RESET}")
            print(f"{GREEN}{'='*50}{RESET}")
            print(f"📁 Çıktı Dosyası: {OUTPUT_FILE}")
            print(f"🌐 Domain: {domain}")
            print(f"🎯 Toplam Kanal: {len(maclar)}")
        else:
            print(f"{RED}[!] Kanal bulunamadı, M3U oluşturulamadı.{RESET}")
            
    except Exception as e:
        print(f"{RED}[!] Ana hata: {e}{RESET}")
        import traceback
        traceback.print_exc()
