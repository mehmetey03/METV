import requests
import re
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "https://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
}

def get_active_info():
    """Hem site domainini hem de yayın sunucusunu (Base URL) tespit eder."""
    active_domain = "https://hepbetspor5.cfd"
    base_url = "https://ofx.d72577a9dd0ec26.sbs/" # Senin paylaştığın yeni sunucu
    
    try:
        # 1. Adım: GitHub üzerinden güncel site adresini al
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        match = re.search(r'URL=(https?://[^">]+)', r.text)
        if match:
            active_domain = match.group(1).rstrip('/')
        
        # 2. Adım: Site üzerinden yayın sunucusunu (CDN) doğrula
        test_url = f"{active_domain}/ch.html?id=patron"
        r_test = requests.get(test_url, headers={"Referer": active_domain + "/"}, timeout=10, verify=False)
        cdn_match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r_test.text)
        if cdn_match:
            base_url = cdn_match.group(1).rstrip('/') + "/"
            
    except:
        print("⚠️ Otomatik adres tespiti kısıtlı, manuel bilgiler kullanılıyor.")
    
    return active_domain, base_url

def main():
    active_domain, base_url = get_active_info()
    
    print(f"🔗 Site Adresi: {active_domain}")
    print(f"📡 Yayın Sunucusu: {base_url}")

    # Senin paylaştığın HTML'deki tam liste ve ID'ler
    channels = [
        ("patron", "BEIN SPORTS 1"), ("b2", "BEIN SPORTS 2"), ("b3", "BEIN SPORTS 3"),
        ("b4", "BEIN SPORTS 4"), ("b5", "BEIN SPORTS 5"), ("bm1", "BEIN SPORTS MAX 1"),
        ("bm2", "BEIN SPORTS MAX 2"), ("ss", "S SPORT 1"), ("ss2", "S SPORT 2"),
        ("smarts", "SMART SPOR 1"), ("smarts2", "SMART SPOR 2"), ("t1", "TIVIBU SPOR 1"),
        ("t2", "TIVIBU SPOR 2"), ("t3", "TIVIBU SPOR 3"), ("t4", "TIVIBU SPOR 4"),
        ("ex7", "TABII SPOR"), ("ex1", "TABII SPOR 1 / EXXEN 1"), ("ex2", "TABII SPOR 2"),
        ("ex3", "TABII SPOR 3"), ("ex4", "TABII SPOR 4"), ("ex5", "TABII SPOR 5"),
        ("ex6", "TABII SPOR 6"), ("trtspor", "TRT SPOR"), ("trtyildiz", "TRT SPOR YILDIZ"),
        ("as", "A SPOR"), ("tv85", "TV 8.5"), ("skyf1", "SKY SPORTS F1"),
        ("eu1", "EURO SPORT 1"), ("eu2", "EURO SPORT 2")
    ]

    m3u_content = ["#EXTM3U"]
    
    for cid, name in channels:
        m3u_content.append(f'#EXTINF:-1 group-title="PATRON TV",{name}')
        # Bazı oynatıcılar için gerekli User-Agent ve Referrer komutları
        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
        # Yayın linki: Sunucu + ID + /mono.m3u8
        m3u_content.append(f'{base_url}{cid}/mono.m3u8')

    with open("karsilasmalar3.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))

    print(f"🏁 Başarılı! {len(channels)} kanal 'karsilasmalar3.m3u' dosyasına eklendi.")
    print("💡 İpucu: Yayınlar açılmazsa VLC Player veya IPTV Smarters Player kullanın.")

if __name__ == "__main__":
    main()
