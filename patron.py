import requests
import re
import urllib3

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
REDIRECT_SOURCE = "https://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

def get_active_domain():
    try:
        r = requests.get(REDIRECT_SOURCE, timeout=10)
        match = re.search(r'URL=(https?://[^">]+)', r.text)
        if match:
            return match.group(1).rstrip('/')
    except: pass
    return "https://hepbetspor5.cfd"

def resolve_base_url(active_domain):
    target = f"{active_domain}/ch.html?id=patron"
    try:
        r = requests.get(target, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=10, verify=False)
        match = re.search(r'["\'](https?://[^\s"\']+?)/[\w\-]+/mono\.m3u8', r.text)
        if match:
            return match.group(1).rstrip('/') + "/"
    except: pass
    return "https://9vy.d72577a9dd0ec19.sbs/"

def main():
    active_domain = get_active_domain()
    base_url = resolve_base_url(active_domain)
    
    print(f"🔗 Aktif Domain: {active_domain}")
    print(f"📡 Yayın Sunucusu: {base_url}")

    try:
        # Ana sayfayı çek
        resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
        content = resp.text

        # HTML içinde gizli olan data-src="/ch.html?id=..." ve kanal isimlerini yakala
        # Bu regex, gönderdiğin HTML yapısındaki verileri ham metin üzerinden çeker.
        pattern = r'data-src="[^"]*id=([^"&]+)".*?class="channel-name-text">([^<]+)'
        matches = re.findall(pattern, content, re.DOTALL)

        m3u_content = ["#EXTM3U"]
        count = 0

        for cid, name in matches:
            name = name.strip()
            # M3U Formatı
            m3u_content.append(f'#EXTINF:-1 group-title="Canlı Yayınlar",{name}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_content.append(f'{base_url}{cid}/mono.m3u8')
            count += 1

        # Eğer regex boş dönerse alternatif basit bir tarama yap (id="..." olan her şeyi al)
        if count == 0:
            simple_ids = re.findall(r'id=([a-z0-9]+)', content)
            # Tekrar edenleri temizle
            for sid in list(set(simple_ids)):
                if sid not in ["matches", "channels", "multiscreen"]:
                    m3u_content.append(f'#EXTINF:-1, Kanal_{sid}')
                    m3u_content.append(f'{base_url}{sid}/mono.m3u8')
                    count += 1

        with open("karsilasmalar3.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))

        print(f"🏁 İşlem Tamam! 'karsilasmalar3.m3u' oluşturuldu.")
        print(f"📊 Toplam {count} kanal yakalandı.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
