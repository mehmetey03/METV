import requests
import re
import base64
import json

print("AtomSporTV — Tüm kanallar çekiliyor...")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# ---------------------------------------------------------
# 1) Aktif domain bul
# ---------------------------------------------------------
active_domain = None
for i in range(500, 600):
    test_url = f"https://www.atomsportv{i}.top"
    try:
        r = requests.get(test_url, headers=headers, timeout=5)
        if r.status_code == 200 and "AtomSpor" in r.text:
            active_domain = test_url
            break
    except:
        pass

if not active_domain:
    print("Aktif domain bulunamadı.")
    exit()

print(f"Aktif domain: {active_domain}")
print("Base:", active_domain)

# ---------------------------------------------------------
# 2) Anasayfadan kanal ID’lerini çek
# ---------------------------------------------------------
html = requests.get(active_domain, headers=headers).text

matches = re.findall(r'/watch/([a-z0-9\-]+)"', html)
matches = list(dict.fromkeys(matches))  # duplicate temizle

print(f"Toplam {len(matches)} kanal bulundu.")

channels = []
for ch in matches:
    channels.append({
        "id": ch,
        "name": ch.replace("-", " ").title()
    })

# ---------------------------------------------------------
# 3) Her kanal için gerçek M3U8 bul
# ---------------------------------------------------------

def get_real_m3u8(channel_id):
    try:
        url = f"{active_domain}/matches?id={channel_id}"
        r = requests.get(url, headers=headers, timeout=10)
        html = r.text

        # fetch("/home/channels.php?id=bein-sports-3")
        fetch_match = re.search(r'fetch\(\s*[\'"](/home/.*?)[\'"]', html)
        if not fetch_match:
            return None

        fetch_url = active_domain + fetch_match.group(1)

        # fetch isteğini yap
        r2 = requests.get(fetch_url, headers=headers, timeout=10)
        data = r2.text

        # 1) Gerçek M3U8 burada → "deis": "base64"
        real_match = re.search(r'"deis"\s*:\s*"([^"]+)"', data)
        if real_match:
            try:
                decoded = base64.b64decode(real_match.group(1)).decode().strip()
                if decoded.startswith("http"):
                    return decoded
            except:
                pass

        # 2) Yedek : proxy link → "deismackanal"
        proxy_match = re.search(r'"deismackanal"\s*:\s*"([^"]+)"', data)
        if proxy_match:
            return proxy_match.group(1).replace("\\", "")

        return None

    except Exception as e:
        return None


# ---------------------------------------------------------
# 4) Çalışan kanalları test et
# ---------------------------------------------------------
print("\nKanal test ediliyor...\n")

working = []

for ch in channels:
    print(f"→ {ch['id']}", end="  ")

    m3u8 = get_real_m3u8(ch["id"])

    if m3u8 is not None and m3u8.startswith("http"):
        print("✔ bulundu")
        ch["url"] = m3u8
        working.append(ch)
    else:
        print("✗ yok")

print(f"\nBiten toplam kanal: {len(working)}")

# ---------------------------------------------------------
# 5) M3U dosyası yaz
# ---------------------------------------------------------
print("M3U oluşturuluyor...")

content = "#EXTM3U\n"
for ch in working:
    content += f'#EXTINF:-1 tvg-name="{ch["name"]}",{ch["name"]}\n'
    content += ch["url"] + "\n"

with open("atom.m3u", "w", encoding="utf-8") as f:
    f.write(content)

print(f"[✓] atom.m3u oluşturuldu ({len(working)} kanal).")
