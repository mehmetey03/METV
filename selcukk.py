import requests
from urllib.parse import urlparse
import re
import os

# 1️⃣ Github txt’den hedef URL al
source_url = "https://raw.githubusercontent.com/mehmetey03/METV2/refs/heads/main/selcuk.txt"
r = requests.get(source_url)
target_url = r.text.strip()
print("Target URL:", target_url)

# Referrer otomatik al
parsed_url = urlparse(target_url)
referrer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
print("Referrer:", referrer)

# 2️⃣ Player sayfasını aç ve M3U8 linkini çek
headers = {"User-Agent": "Mozilla/5.0", "Referer": referrer}
r2 = requests.get(target_url, headers=headers, timeout=20)
html = r2.text

# 3️⃣ M3U8 linkini regex ile bul
match = re.search(r'https://.*?\.click/live/.*?/playlist\.m3u8', html)
if match:
    m3u8_url = match.group(0)
    print("Bulunan M3U8 URL:", m3u8_url)
else:
    print("❌ M3U8 URL bulunamadı!")
    exit(1)

# 4️⃣ M3U dosyasını oluştur (kök dizine)
m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="selcukk" tvg-name="Selcuksport" tvg-logo="https://example.com/default-logo.png" group-title="Spor",Selcuksport
#EXTVLCOPT:http-referrer={referrer}
{m3u8_url}
"""

with open("selcukk.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

print("✅ M3U dosyası oluşturuldu: selcukk.m3u")
