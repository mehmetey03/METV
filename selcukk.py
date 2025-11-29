import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 1️⃣ Github txt’den hedef URL al
source_url = "https://raw.githubusercontent.com/mehmetey03/METV2/refs/heads/main/selcuk.txt"
r = requests.get(source_url)
target_url = r.text.strip()

# 2️⃣ Hedef HTML’i çek
r2 = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"})
html = r2.text

# 3️⃣ Referrer otomatik al (domain)
parsed_url = urlparse(target_url)
referrer = f"{parsed_url.scheme}://{parsed_url.netloc}/"

# 4️⃣ HTML parse
soup = BeautifulSoup(html, "html.parser")
channels = soup.select("div.channel-list a[data-url]")

# 5️⃣ M3U oluştur
m3u = "#EXTM3U\n"

for a in channels:
    name = a.text.strip()
    id = a.get("data-id") or name.replace(" ", "").lower()
    logo = a.get("data-logo") or "https://example.com/default-logo.png"
    url = a.get("data-url").split("#")[0]  # #poster parametresi kırpıldı

    m3u += f'#EXTINF:-1 tvg-id="{id}" tvg-name="{name}" tvg-logo="{logo}" group-title="Spor",{name}\n'
    m3u += f'#EXTVLCOPT:http-referrer={referrer}\n'
    m3u += f'{url}\n'

# 6️⃣ Dosyaya yaz
with open("selcukk.m3u", "w", encoding="utf-8") as f:
    f.write(m3u)

print("M3U dosyası oluşturuldu.")
