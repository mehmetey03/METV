from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

BASE_URL = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"
OUTPUT_FILE = "hdceh_embeds.json"
MAX_PAGES = 50  # sayfa sayısını tahmini veriyoruz

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.delete_all_cookies()

embeds = []

for page_no in range(1, MAX_PAGES+1):
    url = f"{BASE_URL}page/{page_no}/"
    driver.get(url)
    time.sleep(3)  # sayfanın JS ile yüklenmesi için bekleme
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # sayfa 404 veya boş mu kontrol
    if soup.find("h1", string="Sayfa Bulunamadı"):
        print(f"[STOP] Sayfa {page_no} yok, scraping durdu.")
        break

    # her film linki
    film_links = soup.select("div.post-container a")
    if not film_links:
        print(f"[WARN] Sayfa {page_no} film bulunamadı")
        continue

    for film in film_links:
        title = film.get("title")
        href = film.get("href")
        if not href or not title:
            continue

        driver.get(href)
        time.sleep(3)  # JS ile embed yükleniyor
        film_soup = BeautifulSoup(driver.page_source, "html.parser")

        # embed URL iframe veya video tag
        embed_tag = film_soup.select_one("div.video-player iframe, div.video-player video")
        embed_url = embed_tag.get("src") if embed_tag else None
        if embed_url:
            embeds.append({"title": title.strip(), "embed": embed_url})
            print(f"[OK] {title.strip()} -> {embed_url}")

driver.quit()

# JSON olarak kaydet
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(embeds, f, ensure_ascii=False, indent=2)

print(f"[DONE] Toplam {len(embeds)} film kaydedildi → {OUTPUT_FILE}")
