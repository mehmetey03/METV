import requests
import json
import re

# Ülke isimlerini Türkçeye çevirme eşleme tablosu
country_mapping = {
    "Germany": ("Almanya", "Almanca"),
    "United Kingdom": ("Birleşik Krallık", "İngilizce"),
    "France": ("Fransa", "Fransızca"),
    "Turkey": ("Türkiye", "Türkçe"),
    "Italy": ("İtalya", "İtalanca"),
    "Spain": ("İspanya", "İspanyolca"),
    "Albania": ("Arnavutluk", "Arnavutça"),
    "Arabia": ("Arabistan", "Arapça"),
    "Balkans": ("Balkanlar", "Türkçe"),
    "Bulgaria": ("Bulgaristan", "Bulgarca"),
    "Netherlands": ("Hollanda", "Felemenkçe"),
    "Poland": ("Polonya", "Lehçe"),
    "Portugal": ("Portekiz", "Portekizce"),
    "Russia": ("Rusya", "Rusça"),
}

DEFAULT_TVG_LOGO_URL = "https://i.hizliresim.com/t6e66bt.png"

def sort_key(tvg_name):
    """Sıralama önceliği belirleme"""
    tvg_name_lower = tvg_name.lower()
    is_bein_spor = "bein" in tvg_name_lower and "spor" in tvg_name_lower
    is_spor = "spor" in tvg_name_lower or "sport" in tvg_name_lower
    
    if is_bein_spor:
        group_priority = 0
    elif is_spor:
        group_priority = 1
    else:
        group_priority = 2
    
    return (group_priority, tvg_name_lower)

# JSON verisini çek
url = "https://www2.vavoo.to/live2/index?countries=all&output=json"
response = requests.get(url)
channels = response.json()

# Türkiye kanallarını filtrele ve işle
turkey_channels = []

for channel in channels:
    group = channel["group"]
    
    # Sadece Turkey (Türkiye) kategorisindeki kanalları işle
    if group != "Turkey":
        continue
    
    logo = channel["logo"]
    name = channel["name"]
    channel_url = channel["url"]
    
    # Ülke adına göre tvg-country ve tvg-language belirleme
    country_name, language_code = country_mapping.get(group, (group, "xx"))
    
    # tvg-id oluşturma (kanal adı + ülke kodu)
    tvg_id = f"{name.lower().replace(' ', '').replace('.', '')}.{language_code}"
    
    # URL formatını değiştirme
    stream_url = channel_url.replace("live2/play", "play").replace(".ts", "/index.m3u8")
    
    # Logo yoksa varsayılan logo kullan
    if not logo:
        logo = DEFAULT_TVG_LOGO_URL
    
    # Kanal bilgilerini listeye ekle
    turkey_channels.append({
        'name': name,
        'tvg_id': tvg_id,
        'logo': logo,
        'language_code': language_code,
        'stream_url': stream_url,
        'sort_priority': sort_key(name)
    })

print(f"Toplam {len(turkey_channels)} kanal bulundu.")

# Sıralama: Önce Bein Spor, sonra diğer spor kanalları, sonra genel kanallar
# Her grup içinde alfabetik
turkey_channels.sort(key=lambda x: x['sort_priority'])

# Kanal sayılarını hesapla
bein_spor_count = sum(1 for c in turkey_channels if c['sort_priority'][0] == 0)
other_spor_count = sum(1 for c in turkey_channels if c['sort_priority'][0] == 1)
general_count = sum(1 for c in turkey_channels if c['sort_priority'][0] == 2)
total_count = len(turkey_channels)

print(f"Bein Spor kanalları: {bein_spor_count}")
print(f"Diğer Spor kanalları: {other_spor_count}")
print(f"Genel kanallar: {general_count}")

# M3U dosya içeriği oluştur
m3u_content = "#EXTM3U\n"

for channel in turkey_channels:
    m3u_content += f'#EXTINF:-1 tvg-id="{channel["tvg_id"]}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="Vavoo Tv" tvg-country="TR" tvg-language="{channel["language_code"]}", {channel["name"]}\n https://renderd-dm9o.onrender.com/proxy/m3u?url={channel["stream_url"]}\n'

# Dosyayı bulunduğu dizine kaydet
with open("vavoo.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

print(f"M3U listesi oluşturuldu: vavoo.m3u")
print("İşlem tamamlandı.")
