#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

CHANNELS = [
    {"id": "bein1", "source_id": "selcukbeinsports1", "name": "BeIN Sports 1", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/5rhmw31628798883.png", "group": "Spor"},
    {"id": "bein2", "source_id": "selcukbeinsports2", "name": "BeIN Sports 2", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/7uv6x71628799003.png", "group": "Spor"},
    {"id": "bein3", "source_id": "selcukbeinsports3", "name": "BeIN Sports 3", "logo": "https://r2.thesportsdb.com/images/media/channel/logo/u3117i1628798857.png", "group": "Spor"},
    # diğer kanalları ekleyin
]

def fetch_target_url(txt_url="https://metvmetvmetv7.serv00.net/selcuk.txt"):
    try:
        r = requests.get(txt_url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.text.strip()
    except:
        pass
    return None

def fetch_html(target_url):
    try:
        r = requests.get(target_url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

def find_stream_domain(html):
    match = re.search(r'https?://(main\.uxsyplayer[0-9a-zA-Z\-]+\.click)', html)
    return f"https://{match.group(1)}" if match else None

def extract_base_url(html):
    match = re.search(r'this\.adsBaseUrl\s*=\s*[\'"]([^\'"]+)', html)
    return match.group(1) if match else None

def fetch_streams(domain, referer):
    result = []
    for ch in CHANNELS:
        full_url = f"{domain}/index.php?id={ch['source_id']}"
        try:
            r = requests.get(full_url, headers={**HEADERS, "Referer": referer}, timeout=5)
            if r.status_code == 200:
                base = extract_base_url(r.text)
                if base:
                    stream = f"{base}{ch['source_id']}/playlist.m3u8"
                    print(f"{ch['name']} → {stream}")
                    result.append((ch, stream))
        except:
            pass
    return result

def write_m3u(links, filename="selcukk.m3u", referer=""):
    print(f"\nM3U dosyası yazılıyor: {filename}")
    lines = ["#EXTM3U"]
    for ch, url in links:
        lines.append(f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}')
        lines.append(f"#EXTVLCOPT:http-referrer={referer}")
        lines.append(url)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Tamamlandı. Kanal sayısı:", len(links))

def main():
    target_url = fetch_target_url()
    if not target_url:
        print("Selcuk.txt URL'sinden yönlendirme alınamadı.")
        return

    html = fetch_html(target_url)
    if not html:
        print("Hedef HTML alınamadı.")
        return

    stream_domain = find_stream_domain(html)
    if not stream_domain:
        print("Yayın domaini bulunamadı.")
        return

    print(f"Yayın domaini: {stream_domain}")
    streams = fetch_streams(stream_domain, target_url)
    if streams:
        write_m3u(streams, referer=target_url)
    else:
        print("Hiçbir yayın alınamadı.")

if __name__ == "__main__":
    main()
