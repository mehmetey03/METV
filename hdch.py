import json
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# ===============================
# AYARLAR
# ===============================

BASE_URL = "https://www.hdfilmcehennemi.ws/filmler/sayfa/{}/"
MAX_PAGES = 1124  # sitenin gösterdiği gerçek sayı
WAIT_JS = 3       # JS yüklenmesi için bekleme süresi
OUTPUT_JSON = "hdceh.json"
SUMMARY_JSON = "hdceh_summary.json"

# ===============================
# LOG AYARLARI
# ===============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ===============================
# SELENIUM BAŞLAT
# ===============================

def start_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=opts)


# ===============================
# TEK SAYFAYI SCRAPE ET
# ===============================

def scrape_page(driver, page):
    url = BASE_URL.format(page)
    logging.info(f"Scraping page {page}: {url}")

    try:
        driver.get(url)
    except WebDriverException as e:
        logging.error(f"Driver error: {e}")
        return []

    time.sleep(WAIT_JS)  # JS film kartlarını yüklesin

    try:
        items = driver.find_elements(By.CSS_SELECTOR, ".ml-item")
    except:
        items = []

    logging.info(f"Found film containers: {len(items)}")

    films = []

    for item in items:
        try:
            a = item.find_element(By.CSS_SELECTOR, "a")
            href = a.get_attribute("href")
            title = a.get_attribute("title")

            img_el = a.find_element(By.CSS_SELECTOR, "img")
            img = (
                img_el.get_attribute("data-original")
                or img_el.get_attribute("data-src")
                or img_el.get_attribute("src")
            )

            films.append({
                "title": title,
                "url": href,
                "image": img
            })

        except NoSuchElementException:
            continue
        except Exception as e:
            logging.error(f"Film parse error: {e}")

    return films


# ===============================
# ANA SCRAPER
# ===============================

def main():
    driver = start_driver()
    all_films = []
    empty_pages = 0

    logging.info("=== SCRAPING STARTED ===")

    for page in range(1, MAX_PAGES + 1):

        films = scrape_page(driver, page)

        if len(films) == 0:
            logging.warning(f"Page {page} → EMPTY")
            empty_pages += 1

            # 3 boş sayfa üst üste → bitir
            if empty_pages >= 3:
                logging.warning("Too many empty pages → stopping.")
                break
        else:
            empty_pages = 0

        all_films.extend(films)

        # Anti-block
        time.sleep(1)

    driver.quit()

    # ===============================
    # JSON KAYDET
    # ===============================

    Path(OUTPUT_JSON).write_text(
        json.dumps(all_films, indent=2, ensure_ascii=False),
        encoding="utf8"
    )

    summary = {
        "total_films": len(all_films),
        "total_pages_scanned": page,
        "output_file": OUTPUT_JSON
    }

    Path(SUMMARY_JSON).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf8"
    )

    logging.info(f"Saved FULL FILM LIST → {OUTPUT_JSON}")
    logging.info(f"SUMMARY SAVED → {SUMMARY_JSON}")
    logging.info("=== SCRAPING FINISHED ===")


if __name__ == "__main__":
    main()
