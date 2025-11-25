import requests
import re

print("Test")

active_domain = None
REF_SITE = None

for i in range(1, 100):
    test_site = f"https://ontvizle{i}.live"
    try:
        r = requests.get(test_site, timeout=5)
        if r.status_code == 200 and len(r.text) > 500:
            active_domain = test_site
            REF_SITE = test_site
            print(f"Active domain found: {active_domain}")
            break
    except:
        pass

if not active_domain:
    print("No active domain found.")
    exit()

print("Scanning source code...")
html = requests.get(active_domain).text
all_m3u8 = re.findall(r'https?://[^\'" ]+\.m3u8', html)

if not all_m3u8:
    print("No m3u8 links found.")
    exit()

domains = list(set([link.split("/")[0] + "//" + link.split("/")[2] for link in all_m3u8]))
print(f"Found stream domains: {domains}")

working_stream_domain = None
test_headers = {
    "Referer": REF_SITE,
    "Origin": REF_SITE,
    "User-Agent": "Mozilla/5.0"
}

print("Testing domains...")

for domain in domains:
    test_url = f"{domain}/705/mono.m3u8"
    try:
        r = requests.get(test_url, headers=test_headers, timeout=5)
        if r.status_code == 200 and "#EXTM3U" in r.text[:100]:
            working_stream_domain = domain
            print(f"ACTIVE STREAM: {domain}")
            break
        else:
            print(f"Inactive: {domain}")
    except:
        print(f"Error: {domain}")

if not working_stream_domain:
    print("No working stream domain found.")
    exit()

channels = {
    701: "beIN sport 1",
    702: "beIN sport 2",
    703: "beIN sport 3",
    704: "beIN sport 4",
    705: "S sport 1",
    706: "Tivibu sport 1",
    707: "smart sport 1",
    708: "Tivibu spor",
    709: "a spor",
    710: "smart sport 2",
    711: "Tivibu sport 2",
    713: "Tivibu sport 4",
    715: "beIN sport max 2",
    730: "S sport 2",
    "tabii": "tabii spor",
    "tabii1": "tabii spor 1",
    "tabii2": "tabii spor 2", 
    "tabii3": "tabii spor 3",
    "tabii4": "tabii spor 4",
    "tabii5": "tabii spor 5",
    "tabii6": "tabii spor 6"
}

print("Adding channels...")

m3u = "#EXTM3U\n\n"

for cid, name in channels.items():
    stream_url = f"{working_stream_domain}/{cid}/mono.m3u8"
    try:
        r = requests.head(stream_url, headers=test_headers, timeout=5)
        if r.status_code == 200:
            print(f"ADDED: {name}")
        else:
            print(f"INACTIVE: {name}")
    except:
        print(f"ERROR: {name}")
    
    m3u += f'''#EXTINF:-1 tvg-logo="https://i.hizliresim.com/ska5t9e.jpg" group-title="SPORTS", {name}
#EXTVLCOPT:http-referrer={REF_SITE}
#EXTVLCOPT:http-origin={REF_SITE}
{stream_url}

'''

file_name = "DeaTHLesS-sports.m3u"
with open(file_name, "w", encoding="utf-8") as f:
    f.write(m3u)

print("Complete!")
print(f"File created: {file_name}")
