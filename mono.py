import requests
import re
import sys
import urllib3
from bs4 import BeautifulSoup

# SSL uyarılarını sustur
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

def get_active_domain():
    print("🔍 Aktif giriş adresi taranıyor...")
    for sayi in range(530, 600):
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
    print("📡 Yayın sunucusu (base_url) tespit ediliyor...")
    # Sitenin kaynak kodundan m3u8 sunucusunu çekmeye çalışır
    target = f"{active_domain}/channel.html?id=zirve"
    try:
        r = requests.get(target, headers={"Referer": active_domain + "/"}, timeout=10, verify=False)
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            res = match.group(1).rstrip('/') + "/"
            print(f"✅ Otomatik sunucu: {res}")
            return res
    except:
        pass
    
    # Fallback: Eğer bulamazsa bilinen en güncel sunucuyu kullan
    fallback = "https://rei.zirvedesin201.cfd/"
    print(f"⚠️ Sunucu bulunamadı, yedek kullanılıyor: {fallback}")
    return fallback

def main():
    active_domain = get_active_domain()
    if not active_domain:
        sys.exit("❌ MonoTV giriş adresi bulunamadı.")

    base_url = resolve_base_url(active_domain)
    
    try:
        print("📡 Tüm kanallar taranıyor...")
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        m3u_content = ["#EXTM3U"]
        eklenen_kanallar = set() # Çift kayıt olmasın diye

        # Sitedeki tüm <a> etiketlerini tara, içinde id= olanları yakala
        for a in soup.find_all("a", href=re.compile(r'id=([^&]+)')):
            cid = re.search(r'id=([^&]+)', a["href"]).group(1)
            
            if cid in eklenen_kanallar:
                continue
                
            # Kanal adını bul (farklı class isimlerini dene)
            name_tag = a.find(class_="channel-name") or a.find(class_="name") or a.find("span")
            status_tag = a.find(class_="channel-status")
            
            if name_tag:
                name = name_tag.get_text(strip=True)
                status = f"[{status_tag.get_text(strip=True)}] " if status_tag else ""
                
                # M3U Formatına Ekle
                m3u_content.append(f'#EXTINF:-1 group-title="MonoTV Otomatik",{status}{name}')
                m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
                m3u_content.append(f'{base_url}{cid}/mono.m3u8')
                
                eklenen_kanallar.add(cid)

        # Sonuçları Kaydet
        if len(m3u_content) > 1:
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_content))
            print(f"🏁 BAŞARILI: {len(eklenen_kanallar)} kanal mono.m3u dosyasına yazıldı.")
        else:
            print("❌ Hiç kanal bulunamadı.")

    except Exception as e:
        print(f"❌ Beklenmedik Hata: {e}")

if __name__ == "__main__":
    main()
