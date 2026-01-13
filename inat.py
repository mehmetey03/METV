import requests
from bs4 import BeautifulSoup
import re
import html
import unicodedata
import json
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
        print(f"{YELLOW}[?] Kanal M3U8: {channel_id}{RESET}")
        
        # Bilinen stream sunucuları
        stream_servers = [
            f"https://tv.ssps.xyz/hls/{channel_id}.m3u8",
            f"https://stream.ssps.xyz/hls/{channel_id}.m3u8",
            f"https://live.ssps.xyz/hls/{channel_id}.m3u8",
            f"{domain}/stream/{channel_id}.m3u8",
            f"{domain}/hls/{channel_id}.m3u8",
            f"{domain}/live/{channel_id}.m3u8",
            f"{domain}/tv/{channel_id}.m3u8",
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": domain
        }
        
        # İlk geçerli URL'yi döndür
        for stream_url in stream_servers:
            try:
                r = requests.head(stream_url, headers=headers, timeout=3)
                if r.status_code in [200, 302, 301]:
                    print(f"{GREEN}[✓] M3U8: {stream_url}{RESET}")
                    return stream_url
            except:
                continue
        
        # Varsayılan URL
        default_url = f"https://tv.ssps.xyz/hls/{channel_id}.m3u8"
        print(f"{YELLOW}[!] Varsayılan M3U8: {default_url}{RESET}")
        return default_url
            
    except Exception as e:
        print(f"{RED}[!] M3U8 hatası: {e}{RESET}")
        return f"https://tv.ssps.xyz/hls/{channel_id}.m3u8"

def extract_channels_from_js(html_content):
    """JavaScript içinden kanal bilgilerini çıkar"""
    kanallar = []
    
    # JavaScript içinde kanal array'leri ara
    patterns = [
        # Array pattern: [...]
        r'\[([^\]]+channel[^\]]+)\]',
        r'var\s+\w+\s*=\s*\[([^\]]+)\]',
        # JSON pattern
        r'\{[^{}]*channel[^{}]*\}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if 'yayin' in match.lower():
                print(f"{YELLOW}[?] JS pattern bulundu: {match[:100]}...{RESET}")
    
    # Daha spesifik arama: HTML içinde kanal linkleri
    # Pattern: <a ... href="...id=yayin..." ...> ... </a>
    channel_pattern = r'<a[^>]*href=[\'"][^\'"]*id=([a-zA-Z0-9_\-]+)[^\'"]*[\'"][^>]*>([^<]*(?:<[^>]+>[^<]*)*)</a>'
    matches = re.findall(channel_pattern, html_content, re.IGNORECASE)
    
    for kanal_id, html_content in matches:
        if 'yayin' in kanal_id.lower():
            # HTML'den text çıkar
            text = re.sub(r'<[^>]+>', '', html_content)
            text = clean_text(text)
            
            # Saat bilgisini ayır (eğer varsa)
            saat = ""
            if ' - ' in text:
                parts = text.split(' - ', 1)
                saat = parts[0].strip()
                kanal_adi = parts[1].strip()
            elif ':' in text and len(text) < 10:
                saat = text
                kanal_adi = f"Kanal {kanal_id}"
            else:
                kanal_adi = text if text else f"Kanal {kanal_id}"
            
            kanallar.append({
                'id': kanal_id,
                'adi': kanal_adi,
                'saat': saat
            })
    
    return kanallar

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
        html_content = r.text
        
        # Debug için kaydet
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"{YELLOW}[?] HTML kaydedildi: debug_page.html ({len(html_content)} karakter){RESET}")
        
        # 1. Önce doğrudan regex ile kanal linklerini ara
        print(f"{YELLOW}[?] Regex ile kanal arama...{RESET}")
        
        # Tüm olası kanal ID'lerini topla
        kanal_ids = set()
        
        # Pattern 1: id=yayinXXX
        id_patterns = [
            r'id=([a-zA-Z0-9_\-]+)',
            r'["\']id["\']\s*:\s*["\']([^"\']+)["\']',
            r'channelId["\']?\s*:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if 'yayin' in match.lower():
                    kanal_ids.add(match)
        
        print(f"{YELLOW}[?] Bulunan kanal ID'leri: {len(kanal_ids)}{RESET}")
        
        # Eğer yayin ID'leri bulunduysa
        if kanal_ids:
            maclar = []
            for kanal_id in kanal_ids:
                # Kanal adını bulmaya çalış
                kanal_adi = f"Kanal {kanal_id}"
                saat = ""
                
                # Kanal adı için HTML'de arama yap
                # Pattern: ...id=kanal_id...>...< veya ...kanal_id...
                ad_pattern = f'{re.escape(kanal_id)}[^>]*>([^<]+)'
                ad_match = re.search(ad_pattern, html_content, re.IGNORECASE)
                if ad_match:
                    kanal_adi = clean_text(ad_match.group(1))
                
                # M3U8 linkini al
                m3u8_link = get_channel_m3u8(domain, kanal_id)
                if m3u8_link:
                    # TVG ID
                    tvg_id = kanal_id.replace(" ", "_").replace(":", "_")
                    
                    # Canlı durumu
                    live = True  # Varsayılan olarak canlı
                    
                    # Kanal bilgilerini oluştur
                    display_name = f"{saat} - {kanal_adi}" if saat else kanal_adi
                    
                    mac = {
                        "saat": saat,
                        "takimlar": kanal_adi,
                        "canli": live,
                        "dosya": m3u8_link,
                        "kanal_adi": display_name,
                        "tvg_id": tvg_id,
                        "kategori": ""
                    }
                    
                    maclar.append(mac)
                    print(f"{GREEN}[✓] Kanal eklendi: {display_name} ({kanal_id}){RESET}")
            
            if maclar:
                return maclar
        
        # 2. Manuel olarak bilinen kanalları ekle
        print(f"{YELLOW}[!] Otomatik bulunamadı, manuel kanallar ekleniyor...{RESET}")
        
        # HTML'den bilinen kanalları çıkar
        bilinen_kanallar = []
        
        # Yaygın kanal ID'leri
        common_channels = [
            # BeIN Sports
            ("yayininat", "BeIN Sports 1"),
            ("yayinb2", "BeIN Sports 2"),
            ("yayinb3", "BeIN Sports 3"),
            ("yayinb4", "BeIN Sports 4"),
            ("yayinb5", "BeIN Sports 5"),
            ("yayinbm1", "BeIN Max 1"),
            ("yayinbm2", "BeIN Max 2"),
            
            # S Sport
            ("yayinss", "S Sport"),
            ("yayinss2", "S Sport 2"),
            
            # Tivibu
            ("yayint1", "Tivibu 1"),
            ("yayint2", "Tivibu 2"),
            ("yayint3", "Tivibu 3"),
            ("yayint4", "Tivibu 4"),
            
            # Diğer
            ("yayinas", "A Spor"),
            ("yayintrtspor", "TRT Spor"),
            ("yayintrtspor2", "TRT Spor 2"),
            ("yayinsmarts", "Smartspor"),
            ("yayinsms2", "Smartspor 2"),
            ("yayineu1", "Euro Sport 1"),
            ("yayineu2", "Euro Sport 2"),
            ("yayinnbatv", "NBA TV"),
        ]
        
        # HTML'de hangi kanalların geçtiğini kontrol et
        for kanal_id, kanal_adi in common_channels:
            if kanal_id in html_content.lower():
                bilinen_kanallar.append((kanal_id, kanal_adi))
        
        print(f"{YELLOW}[?] HTML'de bulunan bilinen kanallar: {len(bilinen_kanallar)}{RESET}")
        
        # Manuel kanalları ekle
        maclar = []
        for kanal_id, kanal_adi in bilinen_kanallar:
            m3u8_link = get_channel_m3u8(domain, kanal_id)
            if m3u8_link:
                tvg_id = kanal_id.replace(" ", "_").replace(":", "_")
                
                mac = {
                    "saat": "7/24",
                    "takimlar": kanal_adi,
                    "canli": True,
                    "dosya": m3u8_link,
                    "kanal_adi": f"🔴 7/24 - {kanal_adi}",
                    "tvg_id": tvg_id,
                    "kategori": "7/24"
                }
                
                maclar.append(mac)
                print(f"{GREEN}[✓] Manuel kanal eklendi: {kanal_adi} ({kanal_id}){RESET}")
        
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
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U x-tvg-url=\"\"\n\n")
            
            for kanal in maclar:
                channel_name = kanal["kanal_adi"]
                
                # EXTINF satırı
                f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{channel_name}" group-title="İnat TV",{channel_name}\n')
                
                # Referer ekle
                f.write(f'#EXTVLCOPT:http-referrer={domain}\n')
                f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n')
                
                # Stream URL
                f.write(kanal["dosya"] + "\n\n")
        
        print(f"{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
        print(f"{GREEN}[✓] Toplam {len(maclar)} kanal eklendi{RESET}")
        
        # İstatistikleri göster
        print(f"\n{YELLOW}[📊] İSTATİSTİKLER:{RESET}")
        print(f"Toplam Kanal: {len(maclar)}")
        
        # Kanal listesi
        print(f"\n{YELLOW}[📺] KANAL LİSTESİ:{RESET}")
        for i, kanal in enumerate(maclar, 1):
            print(f"  {i:2d}. {kanal['kanal_adi']}")
            
    except Exception as e:
        print(f"{RED}[!] M3U dosyası yazılırken hata: {e}{RESET}")

# -------------------- ÇALIŞTIR --------------------
if __name__ == "__main__":
    print(f"{GREEN}{'='*50}{RESET}")
    print(f"{GREEN}     İnat Spor M3U Oluşturucu v4.0     {RESET}")
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
            print(f"{YELLOW}[?] Alternatif yöntem deneniyor...{RESET}")
            
            # Alternatif: Sabit kanal listesi
            print(f"{YELLOW}[!] Sabit kanal listesi kullanılıyor{RESET}")
            
            # Sabit kanal listesi (en yaygın kanallar)
            fixed_channels = [
                ("yayininat", "BeIN Sports 1"),
                ("yayinb2", "BeIN Sports 2"),
                ("yayinb3", "BeIN Sports 3"),
                ("yayinb4", "BeIN Sports 4"),
                ("yayinb5", "BeIN Sports 5"),
                ("yayinbm1", "BeIN Max 1"),
                ("yayinbm2", "BeIN Max 2"),
                ("yayinss", "S Sport"),
                ("yayinss2", "S Sport 2"),
                ("yayinas", "A Spor"),
                ("yayintrtspor", "TRT Spor"),
                ("yayintrtspor2", "TRT Spor 2"),
                ("yayint1", "Tivibu 1"),
                ("yayint2", "Tivibu 2"),
                ("yayint3", "Tivibu 3"),
                ("yayint4", "Tivibu 4"),
                ("yayineu1", "Euro Sport 1"),
                ("yayineu2", "Euro Sport 2"),
                ("yayinnbatv", "NBA TV"),
            ]
            
            maclar = []
            for kanal_id, kanal_adi in fixed_channels:
                m3u8_link = get_channel_m3u8(domain, kanal_id)
                if m3u8_link:
                    tvg_id = kanal_id.replace(" ", "_").replace(":", "_")
                    
                    mac = {
                        "saat": "7/24",
                        "takimlar": kanal_adi,
                        "canli": True,
                        "dosya": m3u8_link,
                        "kanal_adi": f"🔴 7/24 - {kanal_adi}",
                        "tvg_id": tvg_id,
                        "kategori": "7/24"
                    }
                    
                    maclar.append(mac)
                    print(f"{GREEN}[✓] Sabit kanal eklendi: {kanal_adi}{RESET}")
            
            if maclar:
                create_m3u(maclar, domain)
            else:
                print(f"{RED}[!] Hiçbir kanal eklenemedi!{RESET}")
            
    except Exception as e:
        print(f"{RED}[!] Ana hata: {e}{RESET}")
        import traceback
        traceback.print_exc()
