import requests
import json
import csv
from pathlib import Path

RAW_URL = "https://raw.githubusercontent.com/9851392751/4079638272/refs/heads/main/736519378"

def fetch_raw():
    resp = requests.get(RAW_URL, timeout=15)
    resp.raise_for_status()
    return resp.text

def save_json(data, filename="data.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON kaydedildi: {filename}")

def to_m3u(items, filename="channels.m3u"):
    lines = ["#EXTM3U"]
    for e in items:
        name = e.get("B", "")
        url = e.get("G", "")
        logo = e.get("F", "")
        if url:
            lines.append(f'#EXTINF:-1 tvg-logo="{logo}",{name}')
            lines.append(url)
    Path(filename).write_text("\n".join(lines), encoding="utf-8")
    print(f"M3U kaydedildi: {filename}")

def to_csv(items, filename="channels.csv"):
    # tüm anahtarları al
    keys = set()
    for e in items:
        keys |= set(e.keys())
    keys = sorted(keys)
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for e in items:
            writer.writerow(e)
    print(f"CSV kaydedildi: {filename}")

def main():
    raw = fetch_raw()
    data = json.loads(raw)
    # Örnek: eğer JSON {"X":[...], "Y":[...]} gibi ise:
    items = []
    if isinstance(data, dict):
        # toplu listeleri birleştir
        for k in data:
            if isinstance(data[k], list):
                items.extend(data[k])
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Beklenmeyen JSON yapısı")

    save_json(items, "output.json")
    to_m3u(items, "channels.m3u")
    to_csv(items, "channels.csv")

if __name__ == "__main__":
    main()
