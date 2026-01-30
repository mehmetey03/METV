import requests
import re
import sys
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape():
    # 1. Ayarlar
    # Not: GitHub üzerinden erişim zor olduğu için doğrudan senin paylaştığın yapıya göre optimize edildi
    active_domain = "https://monotv530.com" 
    base_stream_url = "https://rei.zirvedesin201.cfd/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": f"{active_domain}/"
    }

    print(f"📡 {active_domain} taranıyor...")

    try:
        r = requests.get(active_domain, headers=headers, timeout=15, verify=False)
        content = r.text

        # 2. Regex: Kanal ve Maç Bloklarını Yakala
        # Bu regex, paylaştığın <a ... href="channel?id=xxx" ... > yapısına göredir.
        pattern = r'href="channel\?id=([^"]+)".*?class="home">([^<]+)</div>.*?class="away"[^>]*>(.*?)</div>'
        matches = re.findall(pattern, content, re.DOTALL)

        m3u_lines = ["#EXTM3U"]
        count = 0

        for cid, home, away_raw in matches:
            # Away kısmındaki img taglarını temizle, sadece metni al
            away = re.sub(r'<[^>]*>', '', away_raw).strip()
            home = home.strip()
            
            # İsim oluşturma (Eğer away boşsa sadece kanal ismidir)
            full_name = f"{home} - {away}" if away else home
            
            # Grup belirleme (Maç mı Kanal mı?)
            # Eğer isimde 'beIN', 'S SPORT', 'TRT' gibi ifadeler varsa 'KANALLAR' grubuna koy
            is_channel = any(x in full_name.upper() for x in ["BEIN", "SPORT", "TRT", "TIVIBU", "ATV", "TV 8", "TABII"])
            group = "KANALLAR" if is_channel else "MACLAR"

            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{full_name}')
            m3u_lines.append(f'#EXTVLCOPT:http-referrer={active_domain}/')
            m3u_lines.append(f'{base_stream_url}{cid}/mono.m3u8')
            count += 1

        # 3. Yazdırma ve Kaydetme
        if count > 0:
            with open("mono.m3u", "w", encoding="utf-8") as f:
                f.write("\n".join(m3u_lines))
            print(f"✅ İşlem Tamam: {count} yayın eklendi.")
        else:
            # Eğer site içeriği vermezse, manuel bir fallback (yedek) listesi oluşturabiliriz 
            # veya Action'ı durdurabiliriz.
            print("❌ Veri çekilemedi. Site içeriği dinamik olarak gizliyor olabilir.")
            sys.exit(1)

    except Exception as e:
        print(f"⚠️ Hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    scrape()
