# hdch_playwright.py
import asyncio
import json
from playwright.async_api import async_playwright

# Site URL
BASE_URL = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"

# JSON kaydedilecek dosya
OUTPUT_FILE = "hdceh_embeds.json"

async def fetch_films():
    films = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        page_number = 1
        while True:
            url = f"{BASE_URL}page/{page_number}/"
            print(f"[INFO] Sayfa {page_number}: {url}")
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            # Film containerlerini seç
            film_elements = await page.query_selector_all("div.video-block")
            if not film_elements:
                print("[INFO] Film bulunamadı, tarama durduruluyor.")
                break

            for fe in film_elements:
                title = await fe.query_selector_eval("h3.title a", "el => el.textContent.trim()")
                href  = await fe.query_selector_eval("h3.title a", "el => el.href")
                embed = await fe.query_selector_eval("iframe", "el => el.src").catch(lambda e: None)
                films.append({
                    "title": title,
                    "href": href,
                    "embed_url": embed
                })
            
            page_number += 1

        await browser.close()

    # JSON olarak kaydet
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(films, f, ensure_ascii=False, indent=4)

    print(f"[DONE] Toplam {len(films)} film kaydedildi → {OUTPUT_FILE}")

# Async çalıştır
asyncio.run(fetch_films())
