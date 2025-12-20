import requests

# Sabit AJAX URL
ajax_url = "https://7salamistv.online/ajax?method=channel_stream&stream=s-sport"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Referer": "https://7salamistv.online/",
    "X-Requested-With": "XMLHttpRequest"
}

# Sabit stream çekiyoruz (S Spor kanalı için)
response = requests.get(ajax_url, headers=headers, timeout=10)
data = response.json()
if data.get("ok") and "stream" in data:
    stream_sample = data["stream"].replace("\\/", "/")
    print(f"✔ Örnek stream bulundu: {stream_sample}")
    
    # Domain ve dosya kısmını ayırıyoruz
    domain = stream_sample.rsplit('/', 2)[0]  # https://savatv16.com
else:
    print("❌ Stream alınamadı.")
    exit()

# Kanal listesi
channels = [
    {"name": "BEIN Sport 1", "id": "701"}, {"name": "BEIN Sport 2", "id": "702"},
    {"name": "BEIN Sport 3", "id": "703"}, {"name": "BEIN Sport 4", "id": "704"},
    {"name": "S Spor", "id": "705"}, {"name": "S Spor 2", "id": "730"},
    {"name": "Tivibu Spor 1", "id": "706"}, {"name": "Tivibu Spor 2", "id": "711"},
    {"name": "Tivibu Spor 3", "id": "712"}, {"name": "Tivibu Spor 4", "id": "713"},
    {"name": "Spor Smart 1", "id": "707"}, {"name": "Spor Smart 2", "id": "708"},
    {"name": "A Spor", "id": "709"}, {"name": "NBA", "id": "nba"},
    {"name": "SKYF1", "id": "skyf1"},
]

# M3U oluşturma
m3u_lines = ['#EXTM3U x-tvg-url=""']

for ch in channels:
    m3u_lines.append(f'#EXTINF:-1 tvg-id="spor" tvg-logo="https://i.hizliresim.com/b6xqz10.jpg" group-title="SalamisTV",{ch["name"]}')
    m3u_lines.append(f'#EXTVLCOPT:http-referer=https://3salamistv.online/')
    m3u_lines.append(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
    
    # Eğer ID sayısalsa domain + ID + mono.m3u8 yapıyoruz
    if ch["id"].isdigit():
        url = f'{domain}/{ch["id"]}/mono.m3u8'
    else:
        url = stream_sample  # sayısal değilse (nba, skyf1) örnek stream
    m3u_lines.append(url)

# Dosyaya yaz
with open("salamistv.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

print("\n✅ salamistv.m3u başarıyla oluşturuldu!")
