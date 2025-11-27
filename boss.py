import requests
import re
import os

def get_active_domain():
    for i in range(216, 1000):
        domain = f"https://bosssports{i}.com"
        try:
            response = requests.get(domain, timeout=5)
            if response.status_code == 200:
                return domain
        except:
            continue
    return None

def get_iframe_src(domain):
    try:
        response = requests.get(domain)
        src_match = re.search(r'src="(/play\.html\?[^"]+)"', response.text)
        return src_match.group(1) if src_match else None
    except:
        return None

def create_m3u(domain, iframe_src):
    params_match = re.search(r'_1=([^&]+)&_2=([^&]+)', iframe_src)
    if not params_match:
        return None
    
    pages_dev = params_match.group(1)
    hash_code = params_match.group(2)
    
    channels = [
        {"id": "777", "name": "beIN Sports 1"},
        {"id": "778", "name": "beIN Sports 2"},
        {"id": "779", "name": "beIN Sports 3"},
        {"id": "780", "name": "beIN Sports 4"},
        {"id": "781", "name": "beIN Sports Max 1"},
        {"id": "782", "name": "beIN Sports Max 2"},
        {"id": "786", "name": "beIN Sports 5"},
        {"id": "763", "name": "S Sport"},
        {"id": "610", "name": "Spor Smart"},
        {"id": "1010", "name": "CBC Sport"},
        {"id": "1020", "name": "İDMAN TV"},
        {"id": "1030", "name": "İCTİMAİ TV"},
        {"id": "69", "name": "TV8,5"},
        {"id": "73", "name": "A Spor"},
        {"id": "74", "name": "HT Spor"},
        {"id": "75", "name": "Tivibu Spor"},
        {"id": "76", "name": "FB TV"},
        {"id": "77", "name": "TRT Spor"},
        {"id": "78", "name": "beIN Sports Haber"},
        {"id": "79", "name": "TRT Spor Yıldız"},
        {"id": "1080", "name": "tabii Spor"},
        {"id": "46", "name": "Ekol Sports"},
        {"id": "631", "name": "Eurosport 1"},
        {"id": "641", "name": "Eurosport 2"},
        {"id": "464", "name": "sportstv"},
        {"id": "608", "name": "NBA TV"}
    ]
    
    m3u_content = '#EXTM3U\n'
    
    for channel in channels:
        m3u8_url = f"https://{pages_dev}/{hash_code}/-/{channel['id']}/playlist.m3u8"
        m3u_content += f'#EXTINF:-1 tvg-logo="https://i.hizliresim.com/ska5t9e.jpg" group-title="BOSS-SPORTS", {channel["name"]}\n'
        m3u_content += f'#EXTVLCOPT:http-referrer={domain}\n'
        m3u_content += f'#EXTVLCOPT:http-origin={domain}\n'
        m3u_content += f'{m3u8_url}\n\n'
    
    return m3u_content

def save_file(content, filename="bossh.m3u"):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return filename
    except:
        return None

def main():
    domain = get_active_domain()
    if not domain:
        print("Aktif domain bulunamadı")
        return
    
    iframe_src = get_iframe_src(domain)
    if not iframe_src:
        print("Iframe src bulunamadı")
        return
    
    m3u_content = create_m3u(domain, iframe_src)
    if not m3u_content:
        print("M3U içeriği oluşturulamadı")
        return
    
    saved_path = save_file(m3u_content)
    if saved_path:
        print(f"M3U dosyası oluşturuldu: {saved_path}")
    else:
        print("Dosya kaydedilemedi")

if __name__ == "__main__":

    main()
