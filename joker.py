import requests
import re
import time

# Sabit URL'ler
JOKERBET_URL = "https://jokerbettv177.com/"
API_URL = "https://maqrizi.com/domain.php"
STREAM_BASE = "https://pix.xsiic.workers.dev/"

# User-Agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_site_content(url, use_proxy=False):
    """Site içeriğini al"""
    try:
        if use_proxy:
            # CORS proxy kullan
            proxy_url = f"https://api.codetabs.com/v1/proxy/?quest={url}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        else:
            # Direk erişim
            response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        
        if response.status_code == 200:
            return response.text
    except:
        pass
    
    return None

def get_base_url():
    """Base URL al"""
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            return response.json().get("baseurl", STREAM_BASE)
    except:
        pass
    return STREAM_BASE

def extract_streams_from_html(html):
    """HTML'den stream'leri çıkar"""
    streams = []
    
    # Pattern 1: data-stream="..." (sabit kanallar)
    pattern1 = r'data-stream="([^"]+)"[^>]*?data-name="([^"]+)"'
    matches1 = re.findall(pattern1, html)
    
    for stream_id, name in matches1:
        if stream_id not in streams:
            streams.append({
                'id': stream_id,
                'name': name.strip().upper(),
                'url': f"{STREAM_BASE}{stream_id}.m3u8"
            })
    
    # Pattern 2: data-stream="betlivematch-..." (canlı maçlar)
    pattern2 = r'data-stream="(betlivematch[^"]+)"[^>]*?data-name="([^"]+)"'
    matches2 = re.findall(pattern2, html)
    
    for stream_id, name in matches2:
        if stream_id not in [s['id'] for s in streams]:
            streams.append({
                'id': stream_id,
                'name': name.strip().upper(),
                'url': f"{STREAM_BASE}{stream_id}.m3u8"
            })
    
    # Pattern 3: Doğrudan m3u8 linkleri
    pattern3 = r'https?://[^\s"\']+\.m3u8'
    matches3 = re.findall(pattern3, html)
    
    for url in matches3:
        if url not in [s['url'] for s in streams]:
            # URL'den isim çıkar
            name = url.split('/')[-1].replace('.m3u8', '').upper()
            streams.append({
                'id': url,
                'name': name,
                'url': url
            })
    
    return streams

def create_m3u_file(streams, referrer):
    """M3U dosyası oluştur"""
    if not streams:
        print("❌ Hiç stream bulunamadı!")
        return False
    
    m3u_content = ["#EXTM3U"]
    
    for stream in streams:
        # Grup belirle
        if "BETLIVEMATCH" in stream['id'].upper():
            group = "⚽ CANLI MAÇLAR"
        elif "-" in stream['name'] and any(x in stream['name'] for x in ["VS", " - ", "V", "MAÇ"]):
            group = "⚽ CANLI MAÇLAR"
        else:
            group = "📺 SABİT KANALLAR"
        
        # M3U girişi
        m3u_content.append(f'#EXTINF:-1 group-title="{group}",{stream["name"]}')
        m3u_content.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_content.append(f'#EXTVLCOPT:http-referrer={referrer}')
        m3u_content.append(stream['url'])
    
    # Dosyaya yaz
    with open("joker.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_content))
    
    return True

def main():
    print("🎬 JOKERBET STREAM TOPLAYICI")
    print("=" * 40)
    
    # 1. Site içeriğini al
    print(f"📡 Siteye bağlanılıyor: {JOKERBET_URL}")
    
    html = get_site_content(JOKERBET_URL, use_proxy=False)
    
    if not html:
        print("⚠️  Direk erişim başarısız, proxy deneniyor...")
        html = get_site_content(JOKERBET_URL, use_proxy=True)
    
    if not html:
        print("❌ Siteye ulaşılamadı!")
        return
    
    print(f"✅ Site içeriği alındı: {len(html)} karakter")
    
    # 2. Stream'leri çıkar
    print("🔄 Stream'ler aranıyor...")
    streams = extract_streams_from_html(html)
    
    if not streams:
        print("⚠️  HTML'de stream bulunamadı, debug için kontrol...")
        
        # HTML'de arama yap
        if 'data-stream' in html:
            print("ℹ️  'data-stream' attribute'ü bulundu ama parse edilemedi")
            # Manually look for patterns
            lines = html.split('\n')
            for i, line in enumerate(lines[:50]):  # İlk 50 satır
                if 'data-stream' in line:
                    print(f"  Satır {i}: {line.strip()[:100]}...")
        return
    
    print(f"✅ {len(streams)} stream bulundu")
    
    # 3. M3U dosyasını oluştur
    print("💾 M3U dosyası oluşturuluyor...")
    if create_m3u_file(streams, JOKERBET_URL):
        print(f"🎉 BAŞARILI: {len(streams)} yayın joker.m3u8 dosyasına kaydedildi!")
        
        # Örnek çıktı
        print("\n📋 İlk 5 yayın:")
        for i, stream in enumerate(streams[:5]):
            print(f"  {i+1}. {stream['name']:30} → {stream['url']}")
    else:
        print("❌ M3U dosyası oluşturulamadı!")

def test_direct_access():
    """Direk erişim testi"""
    print("\n🔧 Direk Erişim Testi:")
    
    try:
        response = requests.get(JOKERBET_URL, headers=HEADERS, timeout=5, verify=False)
        print(f"  Status Code: {response.status_code}")
        print(f"  Content Length: {len(response.text)}")
        
        if response.status_code == 403:
            print("  ⚠️  403 Forbidden - Erişim engellendi")
            return False
        elif response.status_code == 200:
            print("  ✅ Direk erişim başarılı")
            return True
        else:
            print(f"  ⚠️  Beklenmeyen durum: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Hata: {e}")
        return False

if __name__ == "__main__":
    # Önce direk erişim testi
    if not test_direct_access():
        print("\n⚠️  VPN veya proxy önerilir")
    
    # Ana programı çalıştır
    main()
    
    print("\n" + "=" * 40)
    print("ℹ️  NOT: Eğer hala stream bulamazsanız:")
    print("1. Tarayıcıdan siteyi açın")
    print("2. F12 > Elements sekmesinde 'data-stream' ara")
    print("3. Bulduğunuz HTML'i paylaşın")
