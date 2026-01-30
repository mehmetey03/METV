import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

def get_active_domain():
    """530'dan başlayarak aktif MonoTV giriş adresini tarar."""
    print("🔍 Aktif giriş adresi taranıyor...")
    for sayi in range(530, 600): # İhtiyaca göre aralık artırılabilir
        url = f"https://monotv{sayi}.com"
        try:
            r = requests.get(url, timeout=5, verify=False)
            if r.status_code == 200:
                print(f"✅ Giriş adresi bulundu: {url}")
                return url.rstrip('/')
        except:
            continue
    return None

def resolve_base_url(active_domain):
    """Sitenin kaynak kodundan yayın sunucusunu (m3u8'in ana adresi) çeker."""
    print("📡 Yayın sunucusu (base_url) tespit ediliyor...")
    target = f"{active_domain}/channel.html?id=zirve" # Örnek bir kanal üzerinden tarar
    try:
        r = requests.get(target, headers={"Referer": active_domain + "/"}, timeout=10, verify=False)
        # m3u8 linkinin önündeki sunucu adresini yakalar
        # Örn: https://rei.zirvedesin201.cfd/zirve/mono.m3u8 içindeki sunucuyu bulur
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
    except:
        pass
    
    # Eğer koddan bulamazsa bilinen sabit sunucuyu döner
    print("⚠️ Sunucu otomatik bulunamadı, sabit sunucu kullanılıyor.")
    return ""

def main():
    active_domain = get_active_domain()
    if not active_domain:
        sys.exit("❌ MonoTV giriş adresi bulunamadı.")

    base_url = resolve_base_url(active_domain)
    print(f"🚀 Base URL: {base_url}")

    # Kanal Listesi
    channels = {
        "zirve": "Zirve TV",
        "tivibu1": "Tivibu Spor 1",
        "ssport1": "S Sport 1",
        "bein1": "beIN Sports 1"
    }

    m3u_content = ["#EXTM3U"]

    # Sitedeki dinamik maçları çekmeye çalışalım
    try:
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Maç tablosunu bul (Sitenin yapısına göre güncellenir)
        for a in soup.find_all("a", href=re.compile(r'id=')):
            cid_match = re.search(r'id=([^&]+)', a["href"])
            name_tag = a.find(class_="channel-name")
            if cid_match and name_tag:
                cid = cid_match.group(1)
                title = name_tag.get_text(strip=True)
                m3u_content.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # Sabit kanalları ekle
        for cid, name in channels.items():
            m3u_content.append(f'#EXTINF:-1 group-title="7/24 Kanallar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')

        # Dosyayı Kaydet
        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 Başarılı! mono.m3u oluşturuldu. ({len(m3u_content)//3} kanal)")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()

