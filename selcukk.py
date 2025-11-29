import re
import os
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

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

def find_dynamic_player_domain(html):
    m = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html)
    if m:
        return "https://" + m.group(1)
    return None

def extract_m3u8_from_player(player_domain, first_id, referer):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": referer}
    try:
        req = Request(f"{player_domain}/index.php?id={first_id}", headers=headers)
        resp = urlopen(req, timeout=5).read().decode('utf-8')
        m = re.search(r'https://.*?\.click/live/.*?/playlist\.m3u8', resp)
        if m:
            return m.group(0)
    except:
        pass
    return None

def parse_channel_list_html(html):
    channels = []
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", class_="channel-list")
    if div:
        for a in div.find_all("a", attrs={"data-url": True}):
            name = a.text.strip()
            url = a["data-url"].split("#")[0]
            channels.append({"name": name, "url": url})
    return channels

def write_m3u_file(channels, filename="selcukk.m3u", referer=""):
    lines = ["#EXTM3U"]
    for ch in channels:
        tvg_id = ch['name'].lower().replace(" ", "-")
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
    player_domain = find_dynamic_player_domain(html)
    if player_domain:
        first_id = "selcukbeinsports1"
        m3u8 = extract_m3u8_from_player(player_domain, first_id, referer_url)
        if m3u8:
            channels.append({"name": "Selcuksport", "url": m3u8})

        # div.channel-list içinden kanalları ekle
        extra_channels = parse_channel_list_html(html)
        channels.extend(extra_channels)

        write_m3u_file(channels, "selcukk.m3u", referer_url)
    else:
        print("❌ Player domain bulunamadı.")
else:
    print("⛔ Hiçbir domain çalışmıyor.")
