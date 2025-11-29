import re
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0"}

def find_active_domain(start=1825, end=1850):
    for i in range(start, end+1):
        url = f"https://www.selcuksportshd{i}.xyz/"
        try:
            print(f"🔍 Taranıyor: {url}")
            req = Request(url, headers=headers)
            html = urlopen(req, timeout=5).read().decode()
            if "uxsyplayer" in html:
                print(f"✅ Aktif domain bulundu: {url}")
                return url, html
        except Exception as e:
            print(f"❌ Hata: {e}")
            continue
    return None, None

def get_player_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    div = soup.find("div", id="tab1", class_="channel-list")
    if div:
        for a in div.find_all("a", attrs={"data-url": True}):
            links.append(a['data-url'].split("#")[0])
    print(f"🔗 Bulunan player linkleri: {links}")
    return links

def get_m3u8_url(player_url, referer):
    try:
        req = Request(player_url, headers={"User-Agent": headers["User-Agent"], "Referer": referer})
        html = urlopen(req, timeout=5).read().decode()
        m = re.search(r'this\.baseStreamUrl\s*=\s*[\'"]([^\'"]+)', html)
        if m:
            base = m.group(1)
            id_match = re.search(r'id=([a-z0-9]+)', player_url)
            if id_match:
                return f"{base}{id_match.group(1)}/playlist.m3u8"
        else:
            print(f"⚠️ baseStreamUrl bulunamadı: {player_url}")
    except Exception as e:
        print(f"❌ Hata get_m3u8_url: {e}")
        return None
    return None

def normalize_tvg_id(name):
    replacements = {'ç':'c','Ç':'C','ş':'s','Ş':'S','ı':'i','İ':'I','ğ':'g','Ğ':'G','ü':'u','Ü':'U','ö':'o','Ö':'O',' ':'-',
                    ':':'-','.':'-','/':'-'}
    for k,v in replacements.items():
        name = name.replace(k,v)
    name = re.sub(r'[^a-zA-Z0-9\-]+', '', name)
    return name.lower()

def create_m3u(filename="selcukk.m3u"):
    domain, html = find_active_domain()
    if not html:
        print("❌ Aktif domain bulunamadı")
        return

    referer = domain
    players = get_player_links(html)
    if not players:
        print("❌ Tab1 içinde player linki bulunamadı")
        return

    m3u_lines = ["#EXTM3U"]
    for player in players:
        m3u8_url = get_m3u8_url(player, referer)
        if m3u8_url:
            name = player.split("id=")[-1]
            tvg_id = normalize_tvg_id(name)
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="https://example.com/default-logo.png" group-title="Spor",{name}')
            m3u_lines.append(f"#EXTVLCOPT:http-referrer={referer}")
            m3u_lines.append(m3u8_url)
        else:
            print(f"❌ M3U8 URL alınamadı: {player}")

    if len(m3u_lines) > 1:
        with open(filename,"w",encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        print(f"✅ M3U8 dosyası oluşturuldu: {filename}")
    else:
        print("⚠️ M3U8 dosyası oluşturulmadı, link yok.")

create_m3u()
