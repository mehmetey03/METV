import re
import os
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

# Türkçe karakterleri dönüştür
def normalize_tvg_id(name):
    replacements = {
        'ç': 'c', 'Ç': 'C',
        'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I',
        'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        ' ': '-', ':': '-', '.': '-', '/': '-', ',': '-'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = re.sub(r'[^a-zA-Z0-9\-]+', '', name)  # Kalan özel karakterleri temizle
    return name.lower()

def find_working_selcuksportshd(start=1825, end=1850):
    print("🧭 Selcuksportshd domainleri taranıyor...")
    headers = {"User-Agent": "Mozilla/5.0"}
    for i in range(start, end+1):
        url = f"https://www.selcuksportshd{i}.xyz/"
        print(f"🔍 Taranıyor: {url}")
        try:
            req = Request(url, headers=headers)
            html = urlopen(req, timeout=5).read().decode('utf-8')
            if "uxsyplayer" in html:
                print(f"✅ Aktif domain bulundu: {url}")
                return html, url
        except:
            continue
    print("❌ Aktif domain bulunamadı.")
    return None, None

def parse_channel_list_html(html):
    channels = []
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", class_="channel-list")
    if div:
        for a in div.find_all("a", attrs={"data-url": True}):
            name = a.text.strip()
            url = a["data-url"].split("#")[0]  # #poster parametresi kırpıldı
            channels.append({"name": name, "url": url})
    return channels

def write_m3u_file(channels, filename="selcukk.m3u", referer=""):
    lines = ["#EXTM3U"]
    for ch in channels:
        tvg_id = normalize_tvg_id(ch['name'])
        lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{ch["name"]}" tvg-logo="https://example.com/default-logo.png" group-title="Spor",{ch["name"]}')
        lines.append(f"#EXTVLCOPT:http-referrer={referer}")
        lines.append(ch['url'])
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ M3U dosyası oluşturuldu: {filename}")

# -------- Ana işlem --------
html, referer_url = find_working_selcuksportshd()
channels = []

if html:
    channels = parse_channel_list_html(html)
    if channels:
        write_m3u_file(channels, "selcukk.m3u", referer_url)
    else:
        print("❌ Kanal listesi bulunamadı.")
else:
    print("⛔ Hiçbir domain çalışmıyor.")
