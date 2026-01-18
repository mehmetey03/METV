import requests
import re
import sys
from bs4 import BeautifulSoup
import urllib3
import warnings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

# =====================================================
# SABİT KANALLAR
# =====================================================
        fixed_channels = {
            "yayinzirve": ["beIN Sports 1 A", "Inat TV"],
            "yayininat":  ["beIN Sports 1 B", "Inat TV"],
            "yayin1":     ["beIN Sports 1 C", "Inat TV"],
            "yayinb2":    ["beIN Sports 2", "Inat TV"],
            "yayinb3":    ["beIN Sports 3", "Inat TV"],
            "yayinb4":    ["beIN Sports 4", "Inat TV"],
            "yayinb5":    ["beIN Sports 5", "Inat TV"],
            "yayinbm1":   ["beIN Sports 1 Max", "Inat TV"],
            "yayinbm2":   ["beIN Sports 2 Max", "Inat TV"],
            "yayinss":    ["S Sports 1", "Inat TV"],
            "yayinss2":   ["S Sports 2", "Inat TV"],
            "yayint1":    ["Tivibu Sports 1", "Inat TV"],
            "yayint2":    ["Tivibu Sports 2", "Inat TV"],
            "yayint3":    ["Tivibu Sports 3", "Inat TV"],
            "yayint4":    ["Tivibu Sports 4", "Inat TV"],
            "yayinsmarts":["Smart Sports", "Inat TV"],
            "yayinsms2":  ["Smart Sports 2", "Inat TV"],
            "yayinas":    ["A Spor", "Inat TV"],
            "yayintrtspor": ["TRT Spor", "Inat TV"],
            "yayintrtspor2":["TRT Spor Yıldız", "Inat TV"],
            "yayintrt1":  ["TRT 1", "Inat TV"],
            "yayinatv":   ["ATV", "Inat TV"],
            "yayintv85":  ["TV8.5", "Inat TV"],
            "yayinnbatv": ["NBATV", "Inat TV"],
            "yayineu1":   ["Euro Sport 1", "Inat TV"],
            "yayineu2":   ["Euro Sport 2", "Inat TV"],
            "yayinex1":   ["Tâbii 1", "Inat TV"],
            "yayinex2":   ["Tâbii 2", "Inat TV"],
            "yayinex3":   ["Tâbii 3", "Inat TV"],
            "yayinex4":   ["Tâbii 4", "Inat TV"],
            "yayinex5":   ["Tâbii 5", "Inat TV"],
            "yayinex6":   ["Tâbii 6", "Inat TV"],
            "yayinex7":   ["Tâbii 7", "Inat TV"],
            "yayinex8":   ["Tâbii 8", "Inat TV"]
        }

# =====================================================
# AKTİF DOMAIN BUL
# =====================================================
print("🔍 Aktif domain aranıyor...")
active_domain = None

for i in range(1216, 2101):
    url = f"https://inattv{i}.xyz"
    try:
        r = requests.get(url, headers=HEADERS, timeout=2, verify=False)
        if r.status_code == 200:
            active_domain = url
            print(f"✅ Aktif domain: {active_domain}")
            break
    except:
        continue

if not active_domain:
    print("❌ Aktif domain bulunamadı")
    sys.exit(0)

# =====================================================
# SUNUCU (BASE URL) ÇÖZ
# =====================================================
def resolve_base_url(channel_id):
    url = f"{active_domain}/channel.html?id={channel_id}"
    r = requests.get(url, headers={**HEADERS, "Referer": active_domain + "/"}, timeout=5, verify=False)

    # GERÇEK ÇALIŞAN REGEX
    urls = re.findall(
        r'["\'](https?://[a-z0-9.-]+\.(?:sbs|xyz|live|me|net|com)/)["\']',
        r.text
    )
    if urls:
        return urls[0].rstrip("/") + "/"
    return None

# herhangi bir kanaldan base çöz
base_url = resolve_base_url("yayin1")
if not base_url:
    print("❌ Yayın sunucusu çözülemedi")
    sys.exit(0)

print(f"✅ Yayın sunucusu: {base_url}")

# =====================================================
# CANLI MAÇLAR (UTF-8 FIX)
# =====================================================
print("📡 Canlı maçlar alınıyor...")
resp = requests.get(active_domain, headers=HEADERS, timeout=10, verify=False)
resp.encoding = "utf-8"
soup = BeautifulSoup(resp.text, "html.parser")

dynamic_channels = []
matches_tab = soup.find(id="matches-tab")

if matches_tab:
    for a in matches_tab.find_all("a", href=re.compile(r'channel\.html\?id=')):
        cid = re.search(r'id=([^&]+)', a["href"]).group(1)
        name = a.find(class_="channel-name")
        time = a.find(class_="channel-status")
        if name and time:
            title = f"{time.get_text(strip=True)} | {name.get_text(strip=True)}"
            dynamic_channels.append((cid, title))

print(f"✅ {len(dynamic_channels)} canlı maç bulundu")

# =====================================================
# M3U OLUŞTUR
# =====================================================
lines = ["#EXTM3U"]

# CANLI MAÇLAR
for cid, title in dynamic_channels:
    lines.append(f'#EXTINF:-1 group-title="Canlı Maçlar",{title}')
    lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
    lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
    lines.append(f'{base_url}{cid}.m3u8')

# SABİT KANALLAR
for cid, name in fixed_channels.items():
    lines.append(f'#EXTINF:-1 group-title="Inat TV",{name}')
    lines.append('#EXTVLCOPT:http-user-agent=Mozilla/5.0')
    lines.append(f'#EXTVLCOPT:http-referrer={active_domain}')
    lines.append(f'{base_url}{cid}.m3u8')

with open("karsilasmalar.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("🏁 TAMAM → karsilasmalar.m3u oluşturuldu")
