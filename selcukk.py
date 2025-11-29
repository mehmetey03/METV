import requests
import re
from urllib.parse import urlparse

# 1️⃣ Github txt’den hedef URL al
source_url = "https://raw.githubusercontent.com/mehmetey03/METV2/refs/heads/main/selcuk.txt"
r = requests.get(source_url)
target_url = r.text.strip()
print("Target URL:", target_url)

# Referrer
parsed_url = urlparse(target_url)
referrer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
print("Referrer:", referrer)

headers = {"User-Agent": "Mozilla/5.0", "Referer": referrer}

# 2️⃣ Target URL aç ve player domaini bul
r2 = requests.get(target_url, headers=headers, timeout=20)
html = r2.text

# Dynamic player domain
player_match = re.search(r'https?://main\.uxsyplayer[0-9a-zA-Z\-]+\.click', html)
if not player_match:
    print("❌ Player domain bulunamadı!")
    exit(1)

player_domain = player_match.group(0)
print("Player domain:", player_domain)

# 3️⃣ Player sayfasını aç ve M3U8 linkini çek
# Örnek olarak ilk kanal: selcukbeinsports1
first_id = "selcukbeinsports1"
player_url = f"{player_domain}/index.php?id={first_id}"

r3 = requests.get(player_url, headers=headers, timeout=20)
player_html = r3.text

m3u8_match = re.search(r'https://.*?\.click/live/.*?/playlist\.m3u8', player_html)
if not m3u8_match:
    print("❌ M3U8 URL bulunamadı!")
    exit(1)

m3u8_url = m3u8_match.group(0)
print("Bulunan M3U8 URL:", m3u8_url)

# 4️⃣ selcukk.m3u dosyası oluştur
m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="selcukk" tvg-name="Selcuksport" tvg-logo="https://example.com/default-logo.png" group-title="Spor",Selcuksport
#EXTVLCOPT:http-referrer={referrer}
{m3u8_url}
"""

with open("selcukk.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

print("✅ M3U dosyası oluşturuldu: selcukk.m3u")
