import requests
from bs4 import BeautifulSoup
import re

# AtomSporTV ana sayfası - artık buradan çekiyoruz
ATOMSPORTV_URL = "https://atomsportv480.top/"
OUTPUT_FILE = "atomsportv.m3u"

GREEN = "\033[92m"
RESET = "\033[0m"

def get_matches():
    """
    AtomSporTV sayfasından maçları çek
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://url24.link/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        print(f"AtomSporTV sayfası çekiliyor: {ATOMSPORTV_URL}")
        r = requests.get(ATOMSPORTV_URL, headers=headers, timeout=15)
        r.raise_for_status()
        
        # Karakter kodlamasını kontrol et
        r.encoding = 'utf-8'
        html = r.text
        
        soup = BeautifulSoup(html, 'html.parser')
        maclar = []
        
        # Maçları çek (data-tabbed="live" olan kısım)
        live_content = soup.find('div', {'id': 'live-content', 'data-tabbed': 'live'})
        
        if not live_content:
            # Alternatif olarak doğrudan single-match class'larını ara
            match_links = soup.find_all('a', class_='single-match')
            print(f"Direkt single-match bulundu: {len(match_links)}")
            
            for link in match_links:
                if not link.get('href') or 'matches?id=' not in link.get('href', ''):
                    continue
                    
                # Match detaylarını çek
                home_img = link.find('img')
                home_team = link.find('div', class_='home')
                away_team = link.find('div', class_='away')
                event_div = link.find('div', class_='event')
                date_div = link.find('div', class_='date')
                
                if home_team and away_team:
                    href = link.get('href', '')
                    match_id = href.split('matches?id=')[-1] if 'matches?id=' in href else ''
                    
                    # Saat bilgisini event'ten çıkar
                    saat = ""
                    if event_div:
                        event_text = event_div.get_text(strip=True)
                        # Saati bul (örn: "10:00 |")
                        saat_match = re.search(r'(\d{1,2}:\d{2})\s*\|', event_text)
                        if saat_match:
                            saat = saat_match.group(1)
                    
                    # Takım isimleri
                    takimlar = f"{home_team.get_text(strip=True)} vs {away_team.get_text(strip=True)}"
                    
                    # Kanal adı
                    kanal_adi = takimlar
                    if saat:
                        kanal_adi = f"{saat} | {takimlar}"
                    
                    # M3U8 linkini oluştur (AtomSporTV formatına göre)
                    m3u8_link = f"{ATOMSPORTV_URL}matches?id={match_id}"
                    
                    # TV kanalı mı kontrol et
                    is_tv = link.get('data-matchtype') == 'tv' or 'bein-sports' in match_id or 'trt' in match_id or 'aspor' in match_id
                    
                    maclar.append({
                        "saat": saat,
                        "takimlar": takimlar,
                        "canli": True,  # AtomSporTV genelde canlı yayın
                        "dosya": m3u8_link,
                        "kanal_adi": kanal_adi,
                        "tvg_id": match_id,
                        "is_tv": is_tv
                    })
                    
        else:
            # Live content içindeki maçları bul
            match_links = live_content.find_all('a', class_='single-match')
            print(f"Live content içinde match bulundu: {len(match_links)}")
            
            for link in match_links:
                if not link.get('href'):
                    continue
                    
                href = link.get('href', '')
                if 'matches?id=' not in href:
                    continue
                    
                match_id = href.split('matches?id=')[-1]
                
                # Match detaylarını çek
                home_team = link.find('div', class_='home')
                away_team = link.find('div', class_='away')
                event_div = link.find('div', class_='event')
                date_div = link.find('div', class_='date')
                
                if home_team and away_team:
                    # Saat bilgisini event'ten çıkar
                    saat = ""
                    if event_div:
                        event_text = event_div.get_text(strip=True)
                        saat_match = re.search(r'(\d{1,2}:\d{2})\s*\|', event_text)
                        if saat_match:
                            saat = saat_match.group(1)
                    
                    # Takım isimleri
                    takimlar = f"{home_team.get_text(strip=True)} vs {away_team.get_text(strip=True)}"
                    
                    # Kanal adı
                    kanal_adi = takimlar
                    if saat:
                        kanal_adi = f"{saat} | {takimlar}"
                    
                    # M3U8 linkini oluştur
                    m3u8_link = f"{ATOMSPORTV_URL}matches?id={match_id}"
                    
                    # TV kanalı mı kontrol et
                    is_tv = link.get('data-matchtype') == 'tv' or 'bein-sports' in match_id or 'trt' in match_id or 'aspor' in match_id
                    
                    maclar.append({
                        "saat": saat,
                        "takimlar": takimlar,
                        "canli": True,
                        "dosya": m3u8_link,
                        "kanal_adi": kanal_adi,
                        "tvg_id": match_id,
                        "is_tv": is_tv
                    })
        
        # Eğer live-content'te maç yoksa, kanalları çek (data-tabbed="next" olan kısım)
        if not maclar:
            print("Maç bulunamadı, kanallar çekiliyor...")
            next_content = soup.find('div', {'id': 'next-content', 'data-tabbed': 'next'})
            if next_content:
                channel_links = next_content.find_all('a', class_='single-match')
                for link in channel_links:
                    if not link.get('href'):
                        continue
                        
                    href = link.get('href', '')
                    if 'matches?id=' not in href:
                        continue
                        
                    match_id = href.split('matches?id=')[-1]
                    
                    # Kanal detaylarını çek
                    channel_name_div = link.find('div', class_='home')
                    if channel_name_div:
                        channel_name = channel_name_div.get_text(strip=True)
                        
                        # M3U8 linkini oluştur
                        m3u8_link = f"{ATOMSPORTV_URL}matches?id={match_id}"
                        
                        maclar.append({
                            "saat": "24/7",
                            "takimlar": channel_name,
                            "canli": True,
                            "dosya": m3u8_link,
                            "kanal_adi": channel_name,
                            "tvg_id": match_id,
                            "is_tv": True
                        })
        
        return maclar
        
    except Exception as e:
        print(f"Hata: {e}")
        return []


def get_channels():
    """
    AtomSporTV sayfasından TV kanallarını çek
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://url24.link/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        print(f"Kanal bilgileri çekiliyor: {ATOMSPORTV_URL}")
        r = requests.get(ATOMSPORTV_URL, headers=headers, timeout=15)
        r.raise_for_status()
        r.encoding = 'utf-8'
        html = r.text
        
        soup = BeautifulSoup(html, 'html.parser')
        kanallar = []
        
        # Kanallar sekmesini bul (data-tabbed="next")
        next_content = soup.find('div', {'id': 'next-content', 'data-tabbed': 'next'})
        
        if next_content:
            channel_links = next_content.find_all('a', class_='single-match')
            print(f"Kanal bulundu: {len(channel_links)}")
            
            for link in channel_links:
                if not link.get('href'):
                    continue
                    
                href = link.get('href', '')
                if 'matches?id=' not in href:
                    continue
                    
                match_id = href.split('matches?id=')[-1]
                
                # Kanal adını bul
                channel_name_div = link.find('div', class_='home')
                channel_name = channel_name_div.get_text(strip=True) if channel_name_div else match_id
                
                # Logo/kanal resmini bul
                logo_img = link.find('img', src=lambda x: x and ('beinsports' in x or 'trt' in x or 'aspor' in x or 'ssport' in x or 'tivibu' in x))
                
                # M3U8 linkini oluştur
                m3u8_link = f"{ATOMSPORTV_URL}matches?id={match_id}"
                
                kanallar.append({
                    "kanal_adi": channel_name,
                    "dosya": m3u8_link,
                    "tvg_id": match_id,
                    "tvg_logo": logo_img.get('src') if logo_img else "",
                    "group": "TV Kanalları"
                })
        
        return kanallar
        
    except Exception as e:
        print(f"Kanal çekme hatası: {e}")
        return []


def create_m3u(maclar, kanallar=None):
    """
    M3U dosyası oluştur
    """
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        # Önce canlı maçları yaz
        maç_grubu = "Canlı Maçlar"
        for mac in maclar:
            if not mac.get("is_tv", False):  # TV kanalı değilse (maçsa)
                f.write(f'#EXTINF:-1 tvg-id="{mac["tvg_id"]}" tvg-name="{mac["tvg_id"]}" group-title="{maç_grubu}",{mac["kanal_adi"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={ATOMSPORTV_URL}\n')
                f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n')
                f.write(mac["dosya"] + "\n")
        
        # Sonra TV kanallarını yaz
        if kanallar:
            tv_grubu = "TV Kanalları"
            for kanal in kanallar:
                logo_attr = f' tvg-logo="{kanal["tvg_logo"]}"' if kanal["tvg_logo"] else ""
                f.write(f'#EXTINF:-1 tvg-id="{kanal["tvg_id"]}" tvg-name="{kanal["tvg_id"]}"{logo_attr} group-title="{tv_grubu}",{kanal["kanal_adi"]}\n')
                f.write(f'#EXTVLCOPT:http-referrer={ATOMSPORTV_URL}\n')
                f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n')
                f.write(kanal["dosya"] + "\n")
        else:
            # Eğer ayrı kanal listesi yoksa, maclar içindeki TV kanallarını yaz
            tv_grubu = "TV Kanalları"
            for mac in maclar:
                if mac.get("is_tv", False):  # TV kanalı ise
                    f.write(f'#EXTINF:-1 tvg-id="{mac["tvg_id"]}" tvg-name="{mac["tvg_id"]}" group-title="{tv_grubu}",{mac["kanal_adi"]}\n')
                    f.write(f'#EXTVLCOPT:http-referrer={ATOMSPORTV_URL}\n')
                    f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n')
                    f.write(mac["dosya"] + "\n")

    print(f"\n{GREEN}[✓] M3U dosyası oluşturuldu: {OUTPUT_FILE}{RESET}")
    
    # İstatistikleri göster
    maç_sayısı = sum(1 for m in maclar if not m.get("is_tv", False))
    kanal_sayısı = sum(1 for m in maclar if m.get("is_tv", False)) + (len(kanallar) if kanallar else 0)
    print(f"Toplam {maç_sayısı} maç ve {kanal_sayısı} kanal eklendi.")


# --- ÇALIŞTIR ---
try:
    print(f"{GREEN}AtomSporTV M3U Oluşturucu{RESET}")
    print("=" * 40)
    
    print("1. Canlı maçlar çekiliyor...")
    maclar = get_matches()
    
    print("2. TV kanalları çekiliyor...")
    kanallar = get_channels()
    
    print(f"\n{GREEN}[✓] {len(maclar)} maç bulundu{RESET}")
    print(f"{GREEN}[✓] {len(kanallar)} kanal bulundu{RESET}")
    
    print("3. M3U dosyası oluşturuluyor...")
    create_m3u(maclar, kanallar)
    
    # Örnek çıktıyı göster
    print("\n" + "=" * 40)
    print("İlk 5 kayıt:")
    for i, mac in enumerate(maclar[:5]):
        print(f"{i+1}. {mac['kanal_adi']}")
    
    if kanallar:
        print("\nİlk 5 kanal:")
        for i, kanal in enumerate(kanallar[:5]):
            print(f"{i+1}. {kanal['kanal_adi']}")

except Exception as e:
    print(f"\n{RESET}Hata: {e}")
    import traceback
    traceback.print_exc()
