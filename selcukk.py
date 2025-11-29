import requests
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_target_url(txt_url="https://metvmetvmetv7.serv00.net/selcuk.txt"):
    r = requests.get(txt_url, headers=HEADERS)
    return r.text.strip() if r.status_code == 200 else None

def fetch_html(url):
    r = requests.get(url, headers=HEADERS)
    return r.text if r.status_code == 200 else None

def parse_channels(html):
    # a data-url="URL">Kanal Adı</a>
    pattern = r'<a[^>]+data-url="([^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html)
    channels = []
    for url, name in matches:
        channels.append({
            "name": name.strip(),
            "url": url.strip(),
            "logo": "",
            "group": "Spor"
        })
    return channels

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
