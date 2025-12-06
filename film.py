import requests
import re

BASE = "https://dizipall30.com"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

def get_html(url):
    try:
        response = SESSION.get(url, timeout=10)
        return response.text
    except:
        return ""

# 1. sayfayı çek
url = f"{BASE}/filmler"
html = get_html(url)

# HTML'i analiz et
print(f"HTML uzunluğu: {len(html)} karakter")

# Film bloklarını farklı pattern'lerle ara
patterns = [
    r'<li[^>]*>(.*?)</li>',
    r'<div[^>]*class="[^"]*movie[^"]*"[^>]*>(.*?)</div>',
    r'<article[^>]*>(.*?)</article>',
    r'<a[^>]*href="/film/[^"]*"[^>]*>(.*?)</a>',
    r'<div[^>]*class="[^"]*group[^"]*"[^>]*>(.*?)</div>',
    r'<div[^>]*class="[^"]*flex[^"]*"[^>]*>(.*?)</div>',
]

print("\nPattern testleri:")
for i, pattern in enumerate(patterns, 1):
    matches = re.findall(pattern, html, re.DOTALL)
    print(f"{i}. Pattern: {pattern[:50]}... → {len(matches)} eşleşme")

# Belirli class isimlerini ara
class_patterns = [
    'w-1/2',
    'movie',
    'film',
    'card',
    'item',
    'post',
    'grid',
    'flex'
]

print("\nClass içeren div/li'ler:")
for class_name in class_patterns:
    pattern = fr'<[^>]*class="[^"]*{class_name}[^"]*"[^>]*>.*?</[^>]*>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    if matches:
        print(f"'{class_name}' class'ı: {len(matches)} eşleşme")
        # İlk eşleşmeyi göster
        print(f"  Örnek: {matches[0][:200]}...")

# Tüm li elementlerini bul
print("\nTüm li elementleri:")
li_pattern = r'<li[^>]*>.*?</li>'
li_matches = re.findall(li_pattern, html, re.DOTALL | re.IGNORECASE)
print(f"Toplam li sayısı: {len(li_matches)}")

# w-1/2 class'ı olan li'leri bul
w_half_pattern = r'<li[^>]*class="[^"]*w-1/2[^"]*"[^>]*>.*?</li>'
w_half_matches = re.findall(w_half_pattern, html, re.DOTALL | re.IGNORECASE)
print(f"\nw-1/2 class'lı li sayısı: {len(w_half_matches)}")

if w_half_matches:
    print("\nİlk w-1/2 li içeriği:")
    print("-" * 50)
    print(w_half_matches[0][:500] + "..." if len(w_half_matches[0]) > 500 else w_half_matches[0])
    print("-" * 50)

# HTML'yi dosyaya kaydet
with open("debug_html.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"\nHTML debug_html.html dosyasına kaydedildi")
