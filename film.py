import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

BASE = "https://dizipall30.com/filmler/"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

all_movies = []

def get_page(url):
    driver.get(url)
    time.sleep(3)  # Cloudflare bekleme
    return driver.page_source


def parse_movies(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".ml-item")
    movies = []

    for item in items:
        a = item.find("a")

        if not a:
            continue

        title = a.get("oldtitle") or a.get("title") or "?"
        link = a.get("href")

        img = item.find("img")
        image = img.get("data-original") if img else ""

        movies.append({
            "title": title.strip(),
            "link": link,
            "image": image
        })

    return movies


print("🔍 Film taraması başlıyor...")

page = 1
while True:
    url = BASE + str(page)
    print(f"→ Tarama: {url}")

    html = get_page(url)
    movies = parse_movies(html)

    if len(movies) == 0:
        print("❌ Film yok → Tarama bitti.")
        break

    all_movies.extend(movies)
    page += 1

print(f"\n🎉 Toplam film: {len(all_movies)}")

with open("film.json", "w", encoding="utf8") as f:
    json.dump(all_movies, f, ensure_ascii=False, indent=2)

print("💾 film.json kaydedildi!")
driver.quit()
