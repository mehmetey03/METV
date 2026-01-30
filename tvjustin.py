import re
import sys
import time
from urllib.parse import urlparse, parse_qs, urljoin
from playwright.sync_api import sync_playwright

JUSTINTV_DOMAIN = "https://tvjustin.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"

def scrape_default_channel_info(page):
    try:
        page.goto(JUSTINTV_DOMAIN, timeout=25000, wait_until='domcontentloaded')
        iframe_selector = "iframe#customIframe"
        page.wait_for_selector(iframe_selector, timeout=15000)
        iframe_element = page.query_selector(iframe_selector)
        if not iframe_element: return None, None
        
        iframe_src = iframe_element.get_attribute('src')
        event_url = urljoin(JUSTINTV_DOMAIN, iframe_src)
        parsed_event_url = urlparse(event_url)
        query_params = parse_qs(parsed_event_url.query)
        stream_id = query_params.get('id', [None])[0]
        return event_url, stream_id
    except Exception:
        return None, None

def extract_base_m3u8_url(page, event_url):
    try:
        page.goto(event_url, timeout=20000, wait_until="domcontentloaded")
        content = page.content()
        base_url_match = re.search(r"['\"](https?://[^'\"]+/checklist/)['\"]", content)
        return base_url_match.group(1) if base_url_match else None
    except Exception:
        return None

def get_channel_group(channel_name):
    channel_name_lower = channel_name.lower()
    # Maç yayını kontrolü (Saat formatı veya tire varsa)
    if re.search(r'\d{2}:\d{2}', channel_name) or ' - ' in channel_name:
        return "1_Maç Yayınları" # Sıralama için başına 1 koyduk
    
    group_mappings = {
        '2_BeinSports': ['bein sports', 'beın sports', ' bs', ' bein '],
        '3_Spor': ['s sport', 'tivibu', 'exxen', 'smart spor', 'nba tv', 'eurosport', 'sport tv', 'premier sports', 'ht spor', 'd smart'],
        '4_Ulusal Kanallar': ['a spor', 'trt spor', 'trt 1', 'tv8', 'atv', 'kanal d', 'show tv', 'star tv', 'trt yıldız', 'a2', 'ntv', 'haber'],
        '5_Diğer': ['tjk tv', 'belgesel', 'national', 'discovery', 'film', 'dizi', 'sinema']
    }
    
    for group, keywords in group_mappings.items():
        for keyword in keywords:
            if keyword in channel_name_lower:
                return group
    return "6_Diğer Kanallar"

def scrape_all_channels(page):
    print(f"\n📡 Kanallar {JUSTINTV_DOMAIN} adresinden toplanıyor...")
    channels = []
    seen_ids = set() # Yinelenenleri engellemek için set kullanıyoruz
    
    try:
        page.goto(JUSTINTV_DOMAIN, timeout=45000, wait_until='networkidle')
        page.wait_for_timeout(3000)
        
        channel_elements = page.query_selector_all(".mac[data-url]")
        
        for element in channel_elements:
            data_url = element.get_attribute('data-url')
            if not data_url: continue
            
            # ID Çıkarma
            parsed_data_url = urlparse(data_url)
            stream_id = parse_qs(parsed_data_url.query).get('id', [None])[0]
            
            if stream_id and stream_id not in seen_ids:
                name_element = element.query_selector(".takimlar")
                channel_name = name_element.inner_text().replace('CANLI', '').strip() if name_element else "İsimsiz"
                
                time_element = element.query_selector(".saat")
                time_str = time_element.inner_text().strip() if time_element else ""
                
                final_name = f"{channel_name} ({time_str})" if time_str and time_str != "CANLI" else channel_name
                
                channels.append({
                    'name': final_name,
                    'id': stream_id,
                    'group': get_channel_group(final_name)
                })
                seen_ids.add(stream_id) # Bu ID'yi kaydet

        # SIRALAMA: Önce grup (Maçlar en üstte), sonra isim
        channels.sort(key=lambda x: (x['group'], x['name']))
        return channels
    except Exception as e:
        print(f"Hata: {e}")
        return []

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        default_event_url, _ = scrape_default_channel_info(page)
        if not default_event_url: sys.exit(1)

        base_m3u8_url = extract_base_m3u8_url(page, default_event_url)
        if not base_m3u8_url: sys.exit(1)

        channels = scrape_all_channels(page)
        
        output_filename = "justintv_sirali.m3u8"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"#EXT-X-USER-AGENT:{USER_AGENT}\n")
            f.write(f"#EXT-X-REFERER:{JUSTINTV_DOMAIN}\n")
            f.write(f"#EXT-X-ORIGIN:{JUSTINTV_DOMAIN.rstrip('/')}\n\n")
            
            for c in channels:
                # Grup ismindeki sıralama numarasını (1_, 2_) temizle
                display_group = re.sub(r'^\d+_', '', c['group'])
                f.write(f'#EXTINF:-1 tvg-name="{c["name"]}" group-title="{display_group}",{c["name"]}\n')
                f.write(f"{base_m3u8_url}{c['id']}.m3u8\n")
        
        print(f"✅ İşlem bitti! {len(channels)} benzersiz kanal '{output_filename}' dosyasına maçlar en üstte olacak şekilde kaydedildi.")
        browser.close()

if __name__ == "__main__":
    main()
