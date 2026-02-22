import requests
import urllib3
import json
import re

urllib3.disable_warnings(urqlib3.exceptions.InsecureRequestWarning)

# SADECE VERİLEN KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"
MATCHES_API_URL = "https://patronsports1.cfd/matches.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_base_url_from_api():
    """Sadece domain API'sini kullanarak base URL'i al."""
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            base_url = base_url.replace("\\", "").rstrip('/')
            return base_url + "/"
        else:
            print("⚠️ Domain API'si 'baseurl' döndürmedi.")
            return None
    except Exception as e:
        print(f"⚠️ Domain API'sine erişilemedi: {e}")
        return None

def get_referrer_from_redirect():
    """Redirect kaynağından referrer adresini bul."""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15)
        content = r.text
        
        # .cfd uzantılı linkleri bul
        referrer_matches = re.findall(r'href="(https?://[^"]+\.cfd)[/"]', content)
        if referrer_matches:
            return referrer_matches[0].rstrip('/')
        
        # Alternatif: Sayfa içinde geçen .cfd adresleri
        domain_matches = re.findall(r'(https?://[a-zA-Z0-9.-]+\.cfd)', content)
        if domain_matches:
            return domain_matches[0].rstrip('/')
        
        return None
    except Exception as e:
        print(f"⚠️ Redirect kaynağı işlenirken hata: {e}")
        return None

def extract_static_channels_from_html(html_content):
    """
    Verilen HTML içindeki sabit kanalları çıkar.
    HTML'deki channel-item div'lerinden ID ve kanal adını alır.
    """
    channels = []
    
    # Tüm channel-item bloklarını bul
    channel_blocks = re.findall(r'<div class="channel-item".*?data-src="/ch\.html\?id=([^"]+)".*?>(.*?)</div>\s*</div>', html_content, re.DOTALL)
    
    for channel_id, block_content in channel_blocks:
        # Kanal adını bul
        name_match = re.search(r'class="channel-name-text">([^<]+)</span>', block_content)
        if name_match:
            channel_name = name_match.group(1).strip()
            
            # Logo URL'ini bul
            logo_match = re.search(r'<img src="([^"]+)" class="channel-logo-right"', block_content)
            logo_url = logo_match.group(1) if logo_match else ""
            
            channels.append({
                'id': channel_id,
                'name': channel_name,
                'logo': logo_url,
                'type': 'static',  # Sabit kanal olduğunu belirt
                'league': '7/24 KANALLAR'
            })
    
    return channels

def main():
    print("🔍 Kaynaklardan bilgiler alınıyor...")
    
    # 1. Base URL'i al
    base_url = get_base_url_from_api()
    if not base_url:
        print("❌ Base URL alınamadı! İşlem durduruluyor.")
        return
    
    # 2. Referrer adresini al
    referrer = get_referrer_from_redirect()
    if not referrer:
        print("❌ Referrer adresi alınamadı! İşlem durduruluyor.")
        return
    
    print(f"📡 Referrer: {referrer}")
    print(f"🚀 Yayın Sunucusu: {base_url}")
    
    m3u_list = ["#EXTM3U"]
    all_channels = {}  # ID bazlı benzersiz kanallar
    match_count = 0
    static_count = 0
    
    # 3. Maç API'sinden dinamik maçları çek
    try:
        print("\n📡 Maç API'sinden veriler alınıyor...")
        response = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        matches = response.json()
        print(f"🔍 API'den {len(matches)} maç kaydı alındı.")
        
        for match in matches:
            url_path = match.get('URL', '')
            channel_id = url_path.split('id=')[-1] if 'id=' in url_path else None
            
            if channel_id and channel_id not in all_channels:
                home = match.get('HomeTeam', '').strip()
                away = match.get('AwayTeam', '').strip()
                league = match.get('league', 'Spor').strip()
                match_type = match.get('type', 'football').strip()
                match_time = match.get('Time', '').strip()
                
                # Logo URL'i (API'den gelen)
                logo_url = match.get('HomeLogo') or match.get('AwayLogo') or ""
                
                # Kanal adı
                channel_name = f"{home} - {away}"
                if match_time:
                    channel_name += f" [{match_time}]"
                
                all_channels[channel_id] = {
                    'name': channel_name,
                    'logo': logo_url,
                    'league': league,
                    'type': match_type,
                    'source': 'match_api'
                }
                match_count += 1
        
        print(f"✅ API'den {match_count} benzersiz kanal oluşturuldu.")
        
    except Exception as e:
        print(f"⚠️ Maç API'si hatası: {e}")
        print("Devam ediliyor...")
    
    # 4. Sabit kanalları ekle (HTML'den)
    print("\n📺 Sabit kanallar ekleniyor...")
    
    # Sabit kanalların HTML'i (sizin verdiğiniz)
    static_html = """<div id="matchList"><div class="channel-item" data-src="/ch.html?id=patron" data-id="channel_1">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsports1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-ad-item"><a href="https://t.ly/HepbetSpor" target="_blank"><img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjXWzCfu5DzKQDasl97tLxFdcx05Bcx22a0g8ixY0jVtwzlzHa-n8Rz3rp_y9PL_Wq-NfTfg32ggIYNfgXkRoEJzIcXn9mOpdqGCDmnu62g8RevQf0SD86nuUt56P_BY-LF8kxCyxIfZKkOkktcJzcpfMDi7bt5XGm2WURcvkglqFyAYEZwo_pn_kbbRKk/s1600/gif%20yeni.gif" alt="Reklam"></a></div><div class="channel-item" data-src="/ch.html?id=b2" data-id="channel_2">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsports2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-ad-item"><a href="https://t.ly/HepbetSpor" target="_blank"><img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjXWzCfu5DzKQDasl97tLxFdcx05Bcx22a0g8ixY0jVtwzlzHa-n8Rz3rp_y9PL_Wq-NfTfg32ggIYNfgXkRoEJzIcXn9mOpdqGCDmnu62g8RevQf0SD86nuUt56P_BY-LF8kxCyxIfZKkOkktcJzcpfMDi7bt5XGm2WURcvkglqFyAYEZwo_pn_kbbRKk/s1600/gif%20yeni.gif" alt="Reklam"></a></div><div class="channel-item" data-src="/ch.html?id=b3" data-id="channel_3">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS 3</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsports3.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=b4" data-id="channel_4">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS 4</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsports4.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=b5" data-id="channel_5">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS 5</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsports5.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=bm1" data-id="channel_6">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS MAX 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsportsmax1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=bm2" data-id="channel_7">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">BEIN SPORTS MAX 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/beinsportsmax2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ss" data-id="channel_8">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">S SPORT</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/ssport1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ss2" data-id="channel_9">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">S SPORT 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/ssport2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=smarts" data-id="channel_10">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">SMART SPOR</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/smartspor.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=smarts2" data-id="channel_11">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">SMART SPOR 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/smartspor2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=t1" data-id="channel_12">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TİVİBU SPOR 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tivibu1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=t2" data-id="channel_13">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TİVİBU SPOR 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tivibu2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=t3" data-id="channel_14">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TİVİBU SPOR 3</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tivibu3.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=t4" data-id="channel_15">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TİVİBU SPOR 4</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tivibu4.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=trtspor" data-id="channel_16">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TRT SPOR</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/trtspornew.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=trtyildiz" data-id="channel_17">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TRT SPOR YILDIZ</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/trtspor2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=trt1" data-id="channel_18">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TRT 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/trt1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=as" data-id="channel_19">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">A SPOR</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/aspornew.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=atv" data-id="channel_20">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">ATV</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/atv.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=tv8" data-id="channel_21">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TV 8</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tv8.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=tv85" data-id="channel_22">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TV 8,5</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tv85.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex6" data-id="channel_23">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">Sıfır Tv</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/sifirtv.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=skyf1" data-id="channel_24">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">SKY SPORTS F1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/skysportsf1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=eu1" data-id="channel_25">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">EURO SPORT 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/eurosport1.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=eu2" data-id="channel_26">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">EURO SPORT 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/eurosport2.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex7" data-id="channel_27">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex1" data-id="channel_28">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii (1).png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex2" data-id="channel_29">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR 2</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex3" data-id="channel_30">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR 3</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex4" data-id="channel_31">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR 4</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex5" data-id="channel_32">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR 5</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex6" data-id="channel_33">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">TABİİ SPOR 6</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/tabii.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex1" data-id="channel_34">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">EXXEN</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/exxen.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div><div class="channel-item" data-src="/ch.html?id=ex1" data-id="channel_35">
                        <div class="channel-row" style="flex: 1;">
                            <div class="channel-left">
                                <div class="tv-icon-box"></div>
                                <span class="channel-name-text">EXXEN 1</span>
                            </div>
                            <div class="channel-right">
                                <span class="channel-live-badge">CANLI</span>
                                <img src="https://patronsports1.cfd/img/exxen.png" class="channel-logo-right" alt="">
                            </div>
                        </div></div></div>"""
    
    static_channels = extract_static_channels_from_html(static_html)
    
    for channel in static_channels:
        if channel['id'] not in all_channels:
            all_channels[channel['id']] = channel
            static_count += 1
        else:
            print(f"ℹ️ {channel['name']} kanalı zaten mevcut (ID: {channel['id']})")
    
    print(f"✅ {static_count} yeni sabit kanal eklendi.")
    
    # 5. Tüm kanalları M3U formatında yaz
    print(f"\n📝 Toplam {len(all_channels)} kanal M3U'ya ekleniyor...")
    
    for channel_id, info in all_channels.items():
        # Grup başlığını belirle
        if info.get('source') == 'match_api':
            group = f"CANLI MAÇLAR - {info.get('league', 'Spor')}"
        else:
            group = "7/24 KANALLAR"
        
        # EXTINF satırı
        if info.get('logo'):
            extinf = f'#EXTINF:-1 tvg-logo="{info["logo"]}" group-title="{group}",{info["name"]}'
        else:
            extinf = f'#EXTINF:-1 group-title="{group}",{info["name"]}'
        
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{channel_id}/mono.m3u8')
    
    # 6. Dosyaya kaydet
    output_file = "karsilasmalar4.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_list))
    
    print(f"\n✅ İşlem tamamlandı!")
    print(f"📊 Toplam kanal: {len(all_channels)}")
    print(f"   - API'den gelen maç kanalları: {match_count}")
    print(f"   - Sabit kanallar: {static_count}")
    print(f"💾 Dosya: {output_file}")

if __name__ == "__main__":
    main()
