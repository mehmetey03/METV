import requests
from bs4 import BeautifulSoup
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    PROXY = "https://proxy.freecdn.workers.dev/?url="
    START = "https://taraftariumizle.org"
    FILE_NAME = "taraftariumizle.m3u"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    channels = [
        ("androstreamlivebiraz1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs1", 'TR:beIN Sport 1 HD'),
        ("androstreamlivebs2", 'TR:beIN Sport 2 HD'),
        ("androstreamlivebs3", 'TR:beIN Sport 3 HD'),
        ("androstreamlivebs4", 'TR:beIN Sport 4 HD'),
        ("androstreamlivebs5", 'TR:beIN Sport 5 HD'),
        ("androstreamlivebsm1", 'TR:beIN Sport Max 1 HD'),
        ("androstreamlivebsm2", 'TR:beIN Sport Max 2 HD'),
        ("androstreamlivess1", 'TR:S Sport 1 HD'),
        ("androstreamlivess2", 'TR:S Sport 2 HD'),
        ("androstreamlivets", 'TR:Tivibu Sport HD'),
        ("androstreamlivets1", 'TR:Tivibu Sport 1 HD'),
        ("androstreamlivets2", 'TR:Tivibu Sport 2 HD'),
        ("androstreamlivets3", 'TR:Tivibu Sport 3 HD'),
        ("androstreamlivets4", 'TR:Tivibu Sport 4 HD'),
        ("androstreamlivesm1", 'TR:Smart Sport 1 HD'),
        ("androstreamlivesm2", 'TR:Smart Sport 2 HD'),
        ("androstreamlivees1", 'TR:Euro Sport 1 HD'),
        ("androstreamlivees2", 'TR:Euro Sport 2 HD'),
        ("androstreamlivetb", 'TR:Tabii HD'),
        ("androstreamlivetb1", 'TR:Tabii 1 HD'),
        ("androstreamlivetb2", 'TR:Tabii 2 HD'),
        ("androstreamlivetb3", 'TR:Tabii 3 HD'),
        ("androstreamlivetb4", 'TR:Tabii 4 HD'),
        ("androstreamlivetb5", 'TR:Tabii 5 HD'),
        ("androstreamlivetb6", 'TR:Tabii 6 HD'),
        ("androstreamlivetb7", 'TR:Tabii 7 HD'),
        ("androstreamlivetb8", 'TR:Tabii 8 HD'),
        ("androstreamliveexn", 'TR:Exxen HD'),
        ("androstreamliveexn1", 'TR:Exxen 1 HD'),
        ("androstreamliveexn2", 'TR:Exxen 2 HD'),
        ("androstreamliveexn3", 'TR:Exxen 3 HD'),
        ("androstreamliveexn4", 'TR:Exxen 4 HD'),
        ("androstreamliveexn5", 'TR:Exxen 5 HD'),
        ("androstreamliveexn6", 'TR:Exxen 6 HD'),
        ("androstreamliveexn7", 'TR:Exxen 7 HD'),
        ("androstreamliveexn8", 'TR:Exxen 8 HD'),
    ]

    def get_src(u, ref=None):
        try:
            if ref: headers['Referer'] = ref
            r = requests.get(PROXY + u, headers=headers, verify=False, timeout=20)
            return r.text if r.status_code == 200 else None
        except: return None

    h1 = get_src(START)
    if not h1: return

    s = BeautifulSoup(h1, 'html.parser')
    lnk = s.find('link', rel='amphtml')
    if not lnk: return
    amp = lnk.get('href')

    h2 = get_src(amp)
    if not h2: return

    m = re.search(r'\[src\]="appState\.currentIframe".*?src="(https?://[^"]+)"', h2, re.DOTALL)
    if not m: return
    ifr = m.group(1)

    h3 = get_src(ifr, ref=amp)
    if not h3: return

    bm = re.search(r'baseUrls\s*=\s*\[(.*?)\]', h3, re.DOTALL)
    if not bm: return

    cl = bm.group(1).replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
    srvs = [x.strip() for x in cl.split(',') if x.strip().startswith("http")]
    srvs = list(set(srvs)) # Benzersiz yap

    active_servers = []
    tid = "androstreamlivebs1" 

    # Tüm sunucuları test et
    for sv in srvs:
        sv = sv.rstrip('/')
        turl = f"{sv}/{tid}.m3u8" if "checklist" in sv else f"{sv}/checklist/{tid}.m3u8"
        turl = turl.replace("checklist//", "checklist/")
        
        try:
            headers['Referer'] = ifr
            tr = requests.get(PROXY + turl, headers=headers, verify=False, timeout=5)
            if tr.status_code == 200:
                active_servers.append(sv) # Çalışanı listeye ekle
        except: pass

    if active_servers:
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            # Bulunan her sunucu için listeyi döngüye sok
            for srv in active_servers:
                for cid, cname in channels:
                    furl = f"{srv}/{cid}.m3u8" if "checklist" in srv else f"{srv}/checklist/{cid}.m3u8"
                    furl = furl.replace("checklist//", "checklist/")
                    
                    line = f'#EXTINF:-1 tvg-id="sport.tr" tvg-name="{cname}" tvg-logo="https://i.hizliresim.com/8xzjgqv.jpg" group-title="Andro-Panel",{cname}\n{furl}\n'
                    f.write(line)
                    
        print(f"{FILE_NAME} Saved ({len(active_servers)} servers found).")

if __name__ == "__main__":
    main()
