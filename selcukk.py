#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_target_url(txt_url="https://metvmetvmetv7.serv00.net/selcuk.txt"):
    try:
        r = requests.get(txt_url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.text.strip()
    except:
        pass
    return None

def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

def parse_channels(html):
    soup = BeautifulSoup(html, "html.parser")
    channel_list = []

    # <a data-url="..."> olan tüm kanalları bul
    for a in soup.select("div.channel-list a[data-url]"):
        name = a.get_text(strip=True)
        url = a.get("data-url")
        logo = a.get("data-logo", "")
        group = a.get("data-group", "Spor")
        if url:
            channel_list.append({
                "name": name,
                "url": url,
                "logo": logo,
                "group": group
            })
    return channel_list

def write_m3u(channels, filename="selcukk.m3u", referer=""):
    lines = ["#EXTM3U"]
    for ch in channels:
        lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}')
        lines.append(f"#EXTVLCOPT:http-referrer={referer}")
        lines.append(ch["url"])
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"M3U dosyası yazıldı: {filename}, Kanal sayısı: {len(channels)}")

def main():
    target_url = fetch_target_url()
    if not target_url:
        print("Selcuk.txt URL'sinden yönlendirme alınamadı.")
        return

    html = fetch_html(target_url)
    if not html:
        print("Hedef HTML alınamadı.")
        return

    channels = parse_channels(html)
    if not channels:
        print("Kanal listesi bulunamadı.")
        return

    write_m3u(channels, referer=target_url)

if __name__ == "__main__":
    main()
