import requests
import re

url = "https://hepbetspor16.cfd"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    r = requests.get(url, headers=headers, timeout=10, verify=False)
    # Sayfa içindeki tüm API benzeri linkleri ara
    api_links = re.findall(r'[\'"]([^\'"]+\.(?:json|php|js)[^\'"]*)[\'"]', r.text)
    
    print("--- Bulunan Potansiyel Veri Kaynakları ---")
    for link in set(api_links):
        if "match" in link.lower() or "list" in link.lower() or "ajax" in link.lower():
            print(f"🎯 Hedef Olabilir: {link}")
    print("------------------------------------------")
except Exception as e:
    print(f"Hata: {e}")
