import requests
import re

# Direkt yönlendirme URL'si
BASE_URL = "https://url24.link/AtomSporTV"
OUTPUT_FILE = "atom.m3u"

# HTML'den kanal ID'lerini çıkar
html_content = """
[TÜM HTML BURAYA - KOPYALA YAPIŞTIR]
"""

# Tüm matches?id= linklerini bul
pattern = r'matches\?id=([^"\']+)'
matches = re.findall(pattern, html_content)
channel_ids = list(set(matches))

print(f"Toplam {len(channel_ids)} kanal bulundu")

# Her kanal için m3u8 linkini al
def get_m3u8_url(channel_id):
    try:
        # yayinlink.php endpoint'i
        url = f"https://analyticsjs.sbs/load/yayinlink.php?id={channel_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.atomsportv480.top/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            content = response.text.strip()
            # m3u8 linkini ara
            m3u8_match = re.search(r'(https?://[^\s]+\.m3u8[^\s]*)', content)
            if m3u8_match:
                return m3u8_match.group(1)
    except:
        pass
    return None

# M3U dosyasını oluştur
success_count = 0
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    
    for i, channel_id in enumerate(channel_ids):
        # Kanal adını oluştur
        if channel_id.isdigit():
            channel_name = f"Maç {channel_id}"
        elif "bein-sports" in channel_id:
            channel_name = channel_id.replace("-", " ").upper()
        elif "trt" in channel_id:
            channel_name = channel_id.upper().replace("-", " ")
        elif "aspor" in channel_id:
            channel_name = "ASPOR"
        elif "s-sport" in channel_id:
            channel_name = channel_id.replace("-", " ").upper()
        elif "tivibu" in channel_id:
            channel_name = channel_id.replace("-", " ").upper()
        elif "futboi" in channel_id:
            name = channel_id.replace("-futboi", "").replace("-", " vs ").title()
            channel_name = f"{name} (Futbol)"
        elif "basketboi" in channel_id:
            name = channel_id.replace("-basketboi", "").replace("-", " vs ").title()
            channel_name = f"{name} (Basketbol)"
        else:
            channel_name = channel_id.replace("-", " ").title()
        
        # Grup belirle
        group = "Diğer"
        if any(x in channel_id for x in ['bein-sports', 'trt', 'aspor', 's-sport', 'tivibu']):
            group = "TV Kanalları"
        elif 'futboi' in channel_id:
            group = "Futbol"
        elif 'basketboi' in channel_id:
            group = "Basketbol"
        
        print(f"{i+1:2d}. {channel_name[:40]:40s}...", end=" ")
        
        # m3u8 linkini al
        m3u8_url = get_m3u8_url(channel_id)
        
        if m3u8_url:
            print("✓")
            success_count += 1
            
            # M3U'ya yaz
            f.write(f'#EXTINF:-1 tvg-id="{channel_id}" group-title="{group}",{channel_name}\n')
            f.write(f'#EXTVLCOPT:http-referrer=https://www.atomsportv480.top/\n')
            f.write(m3u8_url + "\n")
        else:
            print("✗")

print(f"\n✓ {success_count}/{len(channel_ids)} kanal başarıyla eklendi")
print(f"✓ Dosya: {OUTPUT_FILE}")
