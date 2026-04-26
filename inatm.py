import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
# Eğer verdiğiniz URL değişirse, sistem numara artırarak deneme yapacak
START_URL = "https://inattv1295.xyz" 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def find_working_domain(start_url):
    """Verilen domainden başlayarak ileriye dönük aktif domaini arar."""
    print("🔍 Aktif domain taranıyor...")
    
    # Mevcut domaini kontrol et
    try:
        r = requests.get(start_url, headers=HEADERS, timeout=5, verify=False)
        if r.status_code == 200:
            return start_url.rstrip('/')
    except:
        pass

    # Eğer çalışmazsa, numara kısmını bulup artırarak dene
    match = re.search(r'(https?://inattv)(\.?[0-9]+)(\.xyz|\.link|\.pw)', start_url)
    if match:
        base, num, tld = match.groups()
        num_val = int(num.replace('.', ''))
        
        # Sonraki 10 domaini dene
        for i in range(1, 15):
            test_url = f"{base}{num_val + i}{tld}"
            try:
                print(f"🔄 Deneniyor: {test_url}")
                r = requests.get(test_url, headers=HEADERS, timeout=3, verify=False)
                if r.status_code == 200:
                    print(f"✅ Yeni domain bulundu: {test_url}")
                    return test_url
            except:
                continue
    return None

def resolve_base_url(active_domain):
    """Yayın sunucusunun base (stream) adresini bulur."""
    target = f"{active_domain}/channel.html?id=yayininat"
    try:
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        # Regex ile m3u8 yolunu içeren sunucuyu yakala
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
        
        alt_match = re.search(r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|pw|site)/)', r.text)
        if alt_match:
            return alt_match.group(1).rstrip('/') + "/"
    except: 
        pass
    return None

def main():
    active_domain = find_working_domain(START_URL)
    
    if not active_domain:
        print("❌ Aktif domain bulunamadı. Lütfen START_URL'yi manuel güncelleyin.")
        sys.exit()

    base_url = resolve_base_url(active_domain)
    if not base_url:
        # Sunucu bulunamazsa en sık kullanılan fallback
        base_url = "hz8.d72577a9dd0ec62.cfd" 
        print(f"⚠️ Yayın sunucusu otomatik bulunamadı, fallback: {base_url}")
    else:
        print(f"✅ Yayın sunucusu tespit edildi: {base_url}")

    fixed_channels = {
        "zirve": "beIN Sports 1 A", "patron": "beIN Sports 1 B", "taraftarium": "beIN Sports 1 C",
        "patron": "beIN Sports 1 D", "b2": "beIN Sports 2", "b3": "beIN Sports 3",
        "b4": "beIN Sports 4", "b5": "beIN Sports 5", "bm1": "beIN Sports 1 Max",
        "bm2": "beIN Sports 2 Max", "ss1": "S Sports 1", "ss2": "S Sports 2",
        "smarts": "Smart Sports", "sms2": "Smart Sports 2", "t1": "Tivibu Sports 1",
        "t2": "Tivibu Sports 2", "t3": "Tivibu Sports 3", "t4": "Tivibu Sports 4",
        "as": "A Spor", "trtspor": "TRT Spor", "trtspor2": "TRT Spor Yıldız",
        "trt1": "TRT 1", "atv": "ATV", "tv85": "TV8.5", "nbatv": "NBA TV",
        "eu1": "Euro Sport 1", "eu2": "Euro Sport 2",
        "ex1": "Tâbii 1", "ex2": "Tâbii 2", "ex3": "Tâbii 3", "ex4": "Tâbii 4"
    }

    try:
        print("📡 Canlı maçlar taranıyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        m3u_content = ["#EXTM3U"]
        
        # 1. Canlı Maçlar
        matches_tab = soup.find(id="matches-tab")
        if matches_tab:
            for a in matches_tab.find_all("a", href=re.compile(r'id=')):
                cid_match = re.search(r'id=([^&]+)', a["href"])
                name = a.find(class_="channel-name")
                status = a.find(class_="channel-status")
                if cid_match and name:
                    cid = cid_match.group(1)
                    title = f"{status.get_text(strip=True) if status else 'CANLI'} | {name.get_text(strip=True)}"
                    m3u_content.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
                    m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
                    m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                    m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # 2. Sabit Kanallar
        for cid, name in fixed_channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        with open("karsilasmalar.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 BAŞARILI → karsilasmalar.m3u oluşturuldu.")

    except Exception as e:
        print(f"❌ Liste oluşturulurken hata: {e}")

if __name__ == "__main__":
    main()
