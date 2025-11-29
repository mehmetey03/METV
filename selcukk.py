import re
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

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
            continue
    return None, None

def extract_player_domain(html):
    """HTML'den player domain'ini dinamik olarak çıkar"""
    patterns = [
        r'https://main\.uxsyplayer[a-z0-9]+\.click',
        r'https://main\.uxsyplayer[a-z0-9]+\.xyz',
        r'data-url="(https://main\.[^"]+)"'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            if 'uxsyplayer' in match:
                domain_match = re.match(r'(https://[^/]+)', match)
                if domain_match:
                    player_domain = domain_match.group(1)
                    print(f"🎯 Player domain bulundu: {player_domain}")
                    return player_domain
    
    print("❌ Player domain bulunamadı")
    return None

def get_player_links(html, player_domain):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    
    # Tüm tab'lardaki linkleri topla
    tabs = soup.find_all("div", class_="channel-list")
    for tab in tabs:
        for a in tab.find_all("a", attrs={"data-url": True}):
            data_url = a['data-url']
            
            # URL'yi normalize et
            if data_url.startswith('/'):
                clean_url = player_domain + data_url
            elif data_url.startswith('https://'):
                clean_url = data_url.split("#")[0]
            else:
                continue  # Geçersiz URL
            
            # Kanal adını al
            name_div = a.find("div", class_="name")
            channel_name = name_div.text.strip() if name_div else "Bilinmeyen"
            
            # ID'yi URL'den çıkar
            stream_id = "unknown"
            id_match = re.search(r'id=([a-zA-Z0-9_\-]+)', clean_url)
            if id_match:
                stream_id = id_match.group(1)
            
            links.append({
                "url": clean_url,
                "name": channel_name,
                "id": stream_id
            })
    
    # Benzersiz linkler
    unique_links = []
    seen_ids = set()
    
    for link in links:
        if link["id"] not in seen_ids and link["id"] != "unknown":
            unique_links.append(link)
            seen_ids.add(link["id"])
    
    print(f"📡 {len(unique_links)} benzersiz kanal bulundu")
    return unique_links

def get_m3u8_url(player_url, referer):
    try:
        req = Request(player_url, headers={
            "User-Agent": headers["User-Agent"], 
            "Referer": referer
        })
        
        response = urlopen(req, timeout=10)
        html = response.read().decode('utf-8')
        
        # Basitleştirilmiş pattern'ler
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
                print(f"🔍 Pattern eşleşti: {base_url}")
                break
        
        if base_url:
            # ID'yi URL'den çıkar
            id_match = re.search(r'id=([a-zA-Z0-9_\-]+)', player_url)
            if id_match:
                stream_id = id_match.group(1)
                
                # Base URL'nin sonunda / yoksa ekle
                if not base_url.endswith('/'):
                    base_url += '/'
                
                m3u8_url = f"{base_url}{stream_id}/playlist.m3u8"
                print(f"✅ M3U8 oluşturuldu: {stream_id}")
                return m3u8_url
        
        print(f"❌ M3U8 bulunamadı: {player_url}")
        return None
        
    except Exception as e:
        print(f"❌ Player hatası: {str(e)}")
        return None

def normalize_tvg_id(name):
    replacements = {
        'ç':'c', 'Ç':'C', 'ş':'s', 'Ş':'S', 'ı':'i', 'İ':'I', 
        'ğ':'g', 'Ğ':'G', 'ü':'u', 'Ü':'U', 'ö':'o', 'Ö':'O', 
        ' ':'-', ':':'-', '.':'-', '/':'-', "'":'', '"':'',
        '&': 'and', '+': 'plus'
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    
    name = re.sub(r'[^a-zA-Z0-9\-]+', '', name)
    return name.lower()

def create_m3u_advanced(filename="selcuk_sports.m3u"):
    print("🚀 Gelişmiş M3U oluşturucu başlatılıyor...")
    
    # Ana domain'i bul
    domain, html = find_active_domain()
    if not html:
        print("❌ Ana domain bulunamadı")
        return

    # Player domain'ini dinamik olarak çıkar
    player_domain = extract_player_domain(html)
    if not player_domain:
        print("❌ Player domain bulunamadı")
        return
    
    print(f"🎯 Kullanılan player domain: {player_domain}")
    
    # Player linklerini al
    players = get_player_links(html, player_domain)
    
    if not players:
        print("❌ Player linkleri bulunamadı")
        return

    print(f"📺 {len(players)} kanal işlenecek")
    
    m3u_lines = ["#EXTM3U"]
    success_count = 0
    
    for i, player in enumerate(players, 1):
        print(f"🔍 [{i}/{len(players)}] {player['name']} ({player['id']})")
        
        m3u8_url = get_m3u8_url(player["url"], domain)
        if m3u8_url:
            name = player["name"]
            tvg_id = normalize_tvg_id(name)
            
            # M3U formatına ekle
            m3u_lines.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="" group-title="Selcuk Sports",{name}')
            m3u_lines.append(f"#EXTVLCOPT:http-referrer={domain}")
            m3u_lines.append(m3u8_url)
            success_count += 1
            print(f"✅ {name} eklendi")
        else:
            print(f"❌ {player['name']} M3U8 alınamadı")

    # Dosyaya yaz
    if success_count > 0:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        
        print(f"✅ M3U8 dosyası oluşturuldu: {filename}")
        print(f"📊 Başarılı kanal sayısı: {success_count}/{len(players)}")
        print(f"🎯 Player Domain: {player_domain}")
        print(f"🏠 Ana Domain: {domain}")
    else:
        print("❌ Hiçbir kanal eklenemedi!")

# Ana fonksiyon
if __name__ == "__main__":
    create_m3u_advanced()
