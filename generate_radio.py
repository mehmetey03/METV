import urllib.request
import json
import urllib.parse

print("📻 Radyo istasyonları alınıyor...")
try:
    # TÜM istasyonları al, limitsiz
    url = 'https://de1.api.radio-browser.info/json/stations?hidebroken=true&order=votes&reverse=true'
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        data = response.read().decode('utf-8')
        stations = json.loads(data)

    print(f"✅ {len(stations)} istasyon alındı")

except Exception as e:
    print(f"❌ API hatası: {e}")
    exit(1)

# Ülkeleri grupla
countries = {}
for station in stations:
    try:
        if not station.get('country') or not station.get('name') or not station.get('url'):
            continue

        country = station['country'].strip()
        if not country:
            continue

        if country not in countries:
            countries[country] = []

        # URL işleme (.pls dönüşümü)
        stream_url = station['url']
        if '.pls' in stream_url:
            stream_url = stream_url.replace('.pls', '.m3u')
            if stream_url.startswith('http://'):
                stream_url = stream_url.replace('http://', 'https://')

        # Geçerli URL kontrolü
        parsed_url = urllib.parse.urlparse(stream_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            continue

        countries[country].append({
            'name': station['name'].strip(),
            'url': stream_url,
            'logo': station.get('favicon', ''),
            'country': country,
            'votes': station.get('votes', 0)
        })

    except Exception as e:
        continue

print("📝 M3U dosyası oluşturuluyor...")
m3u_output = '#EXTM3U x-tvg-url=""\n\n'

# Önce Türkiye'yi al, sonra diğer ülkeleri alfabetik sırala
country_names = sorted(countries.keys())
if 'Turkey' in country_names:
    country_names.remove('Turkey')
    country_names.insert(0, 'Turkey')
elif 'Türkiye' in country_names:
    country_names.remove('Türkiye')
    country_names.insert(0, 'Türkiye')

# Ülke kategorilerine göre sırala ve ekle
for country in country_names:
    m3u_output += f'#EXTINF:-1 tvg-id="" tvg-logo="" group-title="{country}",{country}\n'
    m3u_output += f'#EXTGRP:{country}\n\n'

    # İstasyonları oylara göre sırala
    stations_sorted = sorted(countries[country], key=lambda x: x['votes'], reverse=True)

    for i, station in enumerate(stations_sorted):
        safe_name = station['name'].replace('"', '\\"').replace(',', '')
        logo = station['logo'].replace('"', '\\"') if station['logo'] else ''

        m3u_output += f'#EXTINF:-1 tvg-id="{country}_{i}" tvg-name="{safe_name}" tvg-logo="{logo}" group-title="{country}",{safe_name}\n'
        m3u_output += '#EXTVLCOPT:http-user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"\n'
        m3u_output += f'{station["url"]}\n\n'

# Dosyaya yaz
try:
    with open('global_radio.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_output)

    print("✅ M3U dosyası başarıyla oluşturuldu!")
    print(f"📊 Toplam {len(countries)} ülke, {sum(len(stations) for stations in countries.values())} istasyon")

except Exception as e:
    print(f"❌ Dosya yazma hatası: {e}")
    exit(1)
