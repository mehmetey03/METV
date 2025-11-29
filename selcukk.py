import requests
from bs4 import BeautifulSoup

# 1. Github txt’den URL al
source_url = "https://raw.githubusercontent.com/mehmetey03/METV2/refs/heads/main/selcuk.txt"
r = requests.get(source_url)
target_url = r.text.strip()

# 2. Hedef HTML’i çek
r2 = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"})
html = r2.text

# 3. HTML parse
soup = BeautifulSoup(html, "html.parser")
channels = soup.select("div.channel-list a[data-url]")

# 4. M3U oluştur
m3u = "#EXTM3U\n"
for a in channels:
    id = a.get("data-id")
    name = a.text.strip()
    logo = a.get("data-logo")
    url = a.get("data-url")
    m3u += f'#EXTINF:-1 tvg-id="{id}" tvg-name="{name}" tvg-logo="{logo}" group-title="Spor",{name}\n'
    m3u += '#EXTVLCOPT:http-referrer=https://www.sporcafe6.xyz/\n'
    m3u += f'{url}\n'

with open("selcukk.m3u", "w", encoding="utf-8") as f:
    f.write(m3u)

print("M3U dosyası oluşturuldu.")
