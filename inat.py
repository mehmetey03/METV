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
        print(f"{YELLOW}[?] Kanal M3U8 aranıyor: {channel_id}{RESET}")
        
        # Önce direkt olarak stream sunucularını deneyelim
        stream_servers = [
            f"https://tv.ssps.xyz/hls/{channel_id}.m3u8",
            f"https://stream.ssps.xyz/hls/{channel_id}.m3u8",
            f"https://live.ssps.xyz/hls/{channel_id}.m3u8",
            f"{domain}/stream/{channel_id}.m3u8",
            f"{domain}/hls/{channel_id}.m3u8",
            f"{domain}/live/{channel_id}.m3u8",
            f"{domain}/tv/{channel_id}.m3u8",
            f"https://{domain.replace('https://', '').replace('http://', '').split('/')[0]}/stream/{channel_id}.m3u8"
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": domain
        }
        
        for stream_url in stream_servers:
            try:
                print(f"{YELLOW}[?] Test ediliyor: {stream_url}{RESET}")
                r = requests.head(stream_url, headers=headers, timeout=5)
                if r.status_code in [200, 302, 301]:
                    print(f"{GREEN}[✓] M3U8 bulundu: {stream_url}{RESET}")
                    return stream_url
            except:
                continue
        
        # Eğer bulamazsak, channel.html sayfasını çekip içinden ara
        print(f"{YELLOW}[!] Stream URL'leri çalışmadı, channel.html kontrol ediliyor...{RESET}")
        
        channel_url = f"{domain}/channel.html?id={channel_id}"
        r = requests.get(channel_url, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        html_text = r.text
        
        # JavaScript içinde baseurl ara
        baseurl_patterns = [
            r'baseurl\s*=\s*["\']([^"\']+)["\']',
            r'BASE_URL\s*=\s*["\']([^"\']+)["\']',
            r'streamUrl\s*=\s*["\']([^"\']+)["\']',
            r'var\s+\w+\s*=\s*["\']([^"\']+/hls/)["\']',
            r'src\s*=\s*["\']([^"\']+\.m3u8)["\']'
        ]
        
        for pattern in baseurl_patterns:
            matches = re.findall(pattern, html_text)
            for match in matches:
                if '.m3u8' in match:
                    # m3u8 linki bulundu
                    print(f"{GREEN}[✓] M3U8 bulundu (pattern): {match}{RESET}")
                    return match
                elif '/hls/' in match or '/stream/' in match:
                    # baseurl bulundu
                    m3u8_url = f"{match}{channel_id}.m3u8"
                    print(f"{GREEN}[✓] BaseURL bulundu, M3U8: {m3u8_url}{RESET}")
                    return m3u8_url
        
        # Son çare olarak en yaygın pattern'i kullan
        default_url = f"https://tv.ssps.xyz/hls/{channel_id}.m3u8"
        print(f"{YELLOW}[!] Varsayılan M3U8 kullanılıyor: {default_url}{RESET}")
        return default_url
            
    except Exception as e:
        print(f"{RED}[!] M3U8 hatası: {e}{RESET}")
        return f"https://tv.ssps.xyz/hls/{channel_id}.m3u8"

def extract_channels_from_html(html_content, domain):
    """HTML içerisinden kanalları çıkar"""
    soup = BeautifulSoup(html_content, "html.parser")
    maclar = []
    
    # Tüm linkleri bul
    all_links = soup.find_all('a', href=True)
    print(f"{YELLOW}[?] Toplam {len(all_links)} link bulundu{RESET}")
    
    for link in all_links:
        href = link.get('href', '')
        
        # Sadece channel.html linklerini işle
        if '/channel.html?id=' not in href:
            continue
            
        try:
            # Kanal ID'sini çıkar
            match = re.search(r'id=([^&]+)', href)
            if not match:
                continue
                
            kanal_id = match.group(1).strip()
            if not kanal_id:
                continue
            
            # Kanal adını bul
            kanal_adi = ""
            
            # Önce channel-name class'ını dene
            name_div = link.find(class_='channel-name')
            if name_div:
                kanal_adi = clean_text(name_div.get_text(strip=True))
                # İkonları temizle
                kanal_adi = re.sub(r'<i[^>]*>.*?</i>', '', kanal_adi)
                kanal_adi = clean_text(kanal_adi)
            
            # Eğer bulamazsak, link içindeki tüm text'i al
            if not kanal_adi:
                kanal_adi = clean_text(link.get_text(strip=True))
                # İkonları ve fazlalıkları temizle
                kanal_adi = re.sub(r'<[^>]+>', '', kanal_adi)
                kanal_adi = clean_text(kanal_adi)
            
            if not kanal_adi:
                kanal_adi = f"Kanal {kanal_id}"
            
            # Saat bilgisini bul
            saat = ""
            status_div = link.find(class_='channel-status')
            if status_div:
                saat = clean_text(status_div.get_text(strip=True))
            
            # Kategori bilgisini al
            kategori = link.get('data-category', '')
            
            # Canlı durumu
            live = False
            if saat == "7/24" or ":" in saat:
                live = True
            
            # TVG ID
            tvg_id = kanal_id.replace(" ", "_").replace(":", "_")
            
            # M3U8 linkini al
            m3u8_link = get_channel_m3u8(domain, kanal_id)
            if not m3u8_link:
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
                "tvg_id": tvg_id,
                "kategori": kategori
            }
            
            maclar.append(mac)
            print(f"{GREEN}[✓] Kanal eklendi: {display_name} ({kanal_id}){RESET}")
            
        except Exception as e:
            print(f"{RED}[!] Link işlenirken hata: {e}{RESET}")
            continue
    
    return maclar

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
        
        # HTML içeriğini kaydet (debug için)
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"{YELLOW}[?] HTML kaydedildi: debug_page.html{RESET}")
        
        # Kanalları çıkar
        maclar = extract_channels_from_html(r.text, domain)
        
        # Eğer hala kanal bulunamadıysa, alternatif yöntem dene
        if not maclar:
            print(f"{YELLOW}[!] Kanal bulunamadı, alternatif parsing deniyor...{RESET}")
            
            # Regex ile tüm channel.html linklerini bul
            channel_pattern = r'href=["\'](/channel\.html\?id=[^"\']+)["\']'
            channel_matches = re.findall(channel_pattern, r.text)
            
            print(f"{YELLOW}[?] Regex ile {len(channel_matches)} channel linki bulundu{RESET}")
            
            # Her bir channel linkini işle
            for i, href in enumerate(channel_matches[:50]):  # İlk 50 link
                try:
                    # Tam URL'yi oluştur
                    if href.startswith('/'):
                        full_url = domain + href
                    else:
                        full_url = domain + '/' + href
                    
                    # Kanal ID'sini çıkar
                    match = re.search(r'id=([^&]+)', href)
                    if not match:
                        continue
                    
                    kanal_id = match.group(1).strip()
                    
                    # Kanal adını bulmak için link çevresindeki HTML'i ara
                    # Pattern: href="...">(.*?)</a>
                    link_pattern = f'href=["\']{re.escape(href)}["\'][^>]*>(.*?)</a>'
                    link_match = re.search(link_pattern, r.text, re.DOTALL | re.IGNORECASE)
                    
                    kanal_adi = f"Kanal {kanal_id}"
                    saat = ""
                    
                    if link_match:
                        link_content = link_match.group(1)
                        # <div class="channel-name"> içeriğini ara
                        name_match = re.search(r'<div[^>]*class=["\']channel-name["\'][^>]*>(.*?)</div>', link_content, re.DOTALL | re.IGNORECASE)
                        if name_match:
                            kanal_adi = clean_text(name_match.group(1))
                            # İkonları temizle
                            kanal_adi = re.sub(r'<[^>]+>', '', kanal_adi)
                            kanal_adi = clean_text(kanal_adi)
                        
                        # <div class="channel-status"> içeriğini ara
                        status_match = re.search(r'<div[^>]*class=["\']channel-status["\'][^>]*>(.*?)</div>', link_content, re.DOTALL | re.IGNORECASE)
                        if status_match:
                            saat = clean_text(status_match.group(1))
                    
                    # M3U8 linkini al
                    m3u8_link = get_channel_m3u8(domain, kanal_id)
                    if not m3u8_link:
                        continue
                    
                    # Canlı durumu
                    live = False
                    if saat == "7/24" or ":" in saat:
                        live = True
                    
                    # TVG ID
                    tvg_id = kanal_id.replace(" ", "_").replace(":", "_")
                    
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
                        "tvg_id": tvg_id,
                        "kategori": ""
                    }
                    
                    maclar.append(mac)
                    print(f"{GREEN}[✓] Kanal eklendi (regex): {display_name} ({kanal_id}){RESET}")
                    
                except Exception as e:
                    print(f"{RED}[!] Regex kanal işlenirken hata: {e}{RESET}")
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
            f.write("#EXTM3U\n\n")
            
            # Tüm kanallar için
            for kategori, kanallar in kategoriler.items():
                grup_adi = kategori.capitalize() if kategori and kategori != "genel" else "İnat TV"
                
                for kanal in kanallar:
                    # Kanal adını temizle
                    channel_name = kanal["kanal_adi"]
                    
                    # EXTINF satırı
                    f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{channel_name}" group-title="{grup_adi}",{channel_name}\n')
                    
                    # Referer ekle
                    f.write(f'#EXTVLCOPT:http-referrer={domain}\n')
                    
                    # Stream URL
                    f.write(kanal["dosya"] + "\n\n")
        
        print(f"{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
        print(f"{GREEN}[✓] Toplam {len(maclar)} kanal eklendi{RESET}")
        
        # İstatistikleri göster
        print(f"\n{YELLOW}[📊] İSTATİSTİKLER:{RESET}")
        print(f"Toplam Kanal: {len(maclar)}")
        
        for kategori, kanallar in kategoriler.items():
            if kategori:
                grup_adi = kategori.capitalize()
            else:
                grup_adi = "Genel"
            print(f"  {grup_adi}: {len(kanallar)} kanal")
        
        # İlk 10 kanalı göster
        print(f"\n{YELLOW}[📺] İLK 10 KANAL:{RESET}")
        for i, kanal in enumerate(maclar[:10], 1):
            print(f"  {i}. {kanal['kanal_adi']}")
            
    except Exception as e:
        print(f"{RED}[!] M3U dosyası yazılırken hata: {e}{RESET}")
        import traceback
        traceback.print_exc()

# -------------------- ÇALIŞTIR --------------------
if __name__ == "__main__":
    print(f"{GREEN}{'='*50}{RESET}")
    print(f"{GREEN}     İnat Spor M3U Oluşturucu v3.0     {RESET}")
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
            print(f"{YELLOW}[?] Lütfen debug_page.html dosyasını kontrol edin{RESET}")
            
    except Exception as e:
        print(f"{RED}[!] Ana hata: {e}{RESET}")
        import traceback
        traceback.print_exc()
