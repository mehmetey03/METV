import requests
import urllib3
import json
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://patronsports1.cfd/domain.php"
MATCHES_API_URL = "https://patronsports1.cfd/matches.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_base_url_from_api():
    """Domain API'sinden base URL'i al"""
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            base_url = base_url.replace("\\", "").rstrip('/')
            return base_url + "/"
        return None
    except:
        return None

def get_referrer_from_redirect():
    """Redirect kaynağından referrer adresini bul"""
    try:
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=15)
        content = r.text
        referrer_matches = re.findall(r'href="(https?://[^"]+\.cfd)[/"]', content)
        if referrer_matches:
            return referrer_matches[0].rstrip('/')
        return None
    except:
        return None

def extract_static_channels_from_html(html_content):
    """Sabit kanalları HTML'den çıkar"""
    channels = []
    channel_blocks = re.findall(r'<div class="channel-item".*?data-src="/ch\.html\?id=([^"]+)".*?>(.*?)</div>\s*</div>', html_content, re.DOTALL)
    
    for channel_id, block_content in channel_blocks:
        name_match = re.search(r'class="channel-name-text">([^<]+)</span>', block_content)
        if name_match:
            channel_name = name_match.group(1).strip()
            logo_match = re.search(r'<img src="([^"]+)" class="channel-logo-right"', block_content)
            logo_url = logo_match.group(1) if logo_match else ""
            
            channels.append({
                'id': channel_id,
                'name': channel_name,
                'logo': logo_url,
                'type': 'static'
            })
    return channels

def create_double_logo(logo1, logo2):
    """İki logoyu birleştir veya ikisini de göster"""
    if logo1 and logo2:
        # İsteğe bağlı: Logoları yan yana göstermek için özel bir format
        # VLC'de çift logo görünmeyebilir, bu yüzden ev sahibi logosunu tercih ediyoruz
        return logo1  # Ev sahibi logosunu kullan
    return logo1 or logo2 or ""

def main():
    print("🔍 Kaynaklardan bilgiler alınıyor...")
    
    base_url = get_base_url_from_api()
    referrer = get_referrer_from_redirect()
    
    if not base_url or not referrer:
        print("❌ Gerekli bilgiler alınamadı!")
        return
    
    print(f"📡 Referrer: {referrer}")
    print(f"🚀 Yayın Sunucusu: {base_url}")
    
    m3u_list = ["#EXTM3U"]
    all_matches = []  # Tüm maçları tut (kanalları değil)
    static_channels = []
    
    # 1. API'den TÜM MAÇLARI çek (kanal bazlı gruplama YAPMA)
    try:
        print("\n📡 Maç API'sinden veriler alınıyor...")
        response = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15)
        matches = response.json()
        print(f"🔍 API'den {len(matches)} maç kaydı alındı.")
        
        for match in matches:
            url_path = match.get('URL', '')
            channel_id = url_path.split('id=')[-1] if 'id=' in url_path else None
            
            if channel_id:
                home = match.get('HomeTeam', '').strip()
                away = match.get('AwayTeam', '').strip()
                league = match.get('league', 'Spor').strip()
                match_type = match.get('type', 'football').strip()
                match_time = match.get('Time', '').strip()
                
                # Her iki takımın logosunu da al
                home_logo = match.get('HomeLogo', '')
                away_logo = match.get('AwayLogo', '')
                
                # Logo seçimi (ev sahibi logosu öncelikli)
                logo_url = create_double_logo(home_logo, away_logo)
                
                # Kanal adı
                channel_name = f"{home} - {away}"
                if match_time:
                    channel_name += f" [{match_time}]"
                
                all_matches.append({
                    'id': channel_id,
                    'name': channel_name,
                    'logo': logo_url,
                    'home_logo': home_logo,
                    'away_logo': away_logo,
                    'league': league,
                    'type': match_type,
                    'time': match_time,
                    'home': home,
                    'away': away
                })
        
        print(f"✅ {len(all_matches)} maç kaydedildi.")
        
    except Exception as e:
        print(f"⚠️ Maç API'si hatası: {e}")
    
    # 2. Sabit kanalları ekle
    print("\n📺 Sabit kanallar ekleniyor...")
    
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
    print(f"✅ {len(static_channels)} sabit kanal hazır.")
    
    # 3. M3U'ya TÜM MAÇLARI ekle (kanal bazlı gruplama YOK)
    print(f"\n📝 Toplam {len(all_matches)} maç M3U'ya ekleniyor...")
    
    for match in all_matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        
        # EXTINF satırı
        extinf = f'#EXTINF:-1 tvg-logo="{match["logo"]}" group-title="{group}",{match["name"]}'
        
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{match["id"]}/mono.m3u8')
    
    # 4. Sabit kanalları ekle
    print(f"📺 {len(static_channels)} sabit kanal ekleniyor...")
    
    for channel in static_channels:
        extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{channel["id"]}/mono.m3u8')
    
    # 5. Dosyaya kaydet
    output_file = "karsilasmalar4.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_list))
    
    print(f"\n✅ İşlem tamamlandı!")
    print(f"📊 Toplam maç sayısı: {len(all_matches)}")
    print(f"📊 Toplam sabit kanal: {len(static_channels)}")
    print(f"📊 Toplam satır: {len(m3u_list)}")
    print(f"💾 Dosya: {output_file}")

if __name__ == "__main__":
    main()
