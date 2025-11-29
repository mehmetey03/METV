import re
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import urllib.parse

headers = {"User-Agent": "Mozilla/5.0"}

def find_active_domain(start=1825, end=1850):
    for i in range(start, end+1):
        url = f"https://www.selcuksportshd{i}.xyz/"
        try:
            req = Request(url, headers=headers)
            html = urlopen(req, timeout=5).read().decode()
            if "uxsyplayer" in html:
                print(f"✅ Aktif domain bulundu: {url}")
                return url, html
        except Exception as e:
            print(f"❌ Domain {url} hata: {e}")
            continue
    return None, None

def get_player_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    
    # Tüm tab'lardaki linkleri topla
    tabs = soup.find_all("div", class_="channel-list")
    for tab in tabs:
        for a in tab.find_all("a", attrs={"data-url": True}):
            data_url = a['data-url']
            # URL'yi temizle
            if data_url.startswith('/'):
                # Göreceli URL'leri tam URL'ye çevir
                data_url = "https://main.uxsyplayer329cfc3938.click" + data_url
            clean_url = data_url.split("#")[0]
            # Kanal adını al
            name_div = a.find("div", class_="name")
            channel_name = name_div.text.strip() if name_div else clean_url.split("id=")[-1] if "id=" in clean_url else "Bilinmeyen"
            
            links.append({
                "url": clean_url,
                "name": channel_name
            })
    
    return links

def get_m3u8_url(player_url, referer):
    try:
        req = Request(player_url, headers={"User-Agent": headers["User-Agent"], "Referer": referer})
        html = urlopen(req, timeout=10).read().decode()
        
        # Birden fazla pattern deneyelim
        patterns = [
            r'this\.baseStreamUrl\s*=\s*[\'"]([^\'"]+)',
            r'baseStreamUrl\s*:\s*[\'"]([^\'"]+)',
            r'streamUrl\s*:\s*[\'"]([^\'"]+)',
            r'var\s+baseStreamUrl\s*=\s*[\'"]([^\'"]+)'
        ]
        
        base_url = None
        for pattern in patterns:
            m = re.search(pattern, html)
            if m:
                base_url = m.group(1)
                break
        
        if base_url:
            # ID'yi URL'den çıkar
            id_match = re.search(r'id=([a-zA-Z0-9]+)', player_url)
            if id_match:
                stream_id = id_match.group(1)
                # Base URL'nin sonunda / yoksa ekle
                if not base_url.endswith('/'):
                    base_url += '/'
                m3u8_url = f"{base_url}{stream_id}/playlist.m3u8"
                print(f"✅ M3U8 bulundu: {stream_id}")
                return m3u8_url
        
        print(f"❌ M3U8 bulunamadı: {player_url}")
        return None
        
    except Exception as e:
        print(f"❌ Player hatası: {e}")
        return None

def normalize_tvg_id(name):
    replacements = {
        'ç':'c', 'Ç':'C', 'ş':'s', 'Ş':'S', 'ı':'i', 'İ':'I', 
        'ğ':'g', 'Ğ':'G', 'ü':'u', 'Ü':'U', 'ö':'o', 'Ö':'O', 
        ' ':'-', ':':'-', '.':'-', '/':'-', "'":'', '"':''
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    
    name = re.sub(r'[^a-zA-Z0-9\-]+', '', name)
    return name.lower()

def create_m3u(filename="selcukk.m3u"):
    print("🔍 Aktif domain aranıyor...")
    domain, html = find_active_domain()
    
    if not html:
        print("❌ Aktif domain bulunamadı")
        return

    referer = domain
    print(f"📡 Player linkleri alınıyor...")
    players = get_player_links(html)
    
    if not players:
        print("❌ Player linkleri bulunamadı")
        return

    print(f"📺 {len(players)} kanal bulundu")
    
    m3u_lines = ["#EXTM3U"]
    success_count = 0
    
    for i, player in enumerate(players, 1):
        print(f"🔍 [{i}/{len(players)}] {player['name']} işleniyor...")
        
        m3u8_url = get_m3u8_url(player["url"], referer)
        if m3u8_url:
            name = player["name"]
            tvg_id = normalize_tvg_id(name)
            
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="https://example.com/logo.png" group-title="Spor",{name}')
            m3u_lines.append(f"#EXTVLCOPT:http-referrer={referer}")
            m3u_lines.append(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}")
            m3u_lines.append(m3u8_url)
            success_count += 1
        else:
            print(f"❌ M3U8 alınamadı: {player['name']}")

    # Dosyaya yaz
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    
    print(f"✅ M3U8 dosyası oluşturuldu: {filename}")
    print(f"📊 Başarılı kanal sayısı: {success_count}/{len(players)}")

# Alternatif domain arama fonksiyonu
def find_domain_with_retry():
    ranges = [
        (1825, 1850),
        (1800, 1825),
        (1850, 1875)
    ]
    
    for start, end in ranges:
        print(f"🔍 {start}-{end} aralığı taranıyor...")
        domain, html = find_active_domain(start, end)
        if domain:
            return domain, html
    return None, None

# Geliştirilmiş versiyon
def create_m3u_enhanced(filename="selcukk_enhanced.m3u"):
    print("🚀 Geliştirilmiş M3U oluşturucu başlatılıyor...")
    
    domain, html = find_domain_with_retry()
    if not html:
        print("❌ Hiçbir domain bulunamadı")
        return

    create_m3u(filename)

# Çalıştır
if __name__ == "__main__":
    create_m3u_enhanced()
