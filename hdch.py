import asyncio, json
from playwright.async_api import async_playwright, TimeoutError

BASE_URL = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"
OUTPUT_FILE = "hdceh_embeds.json"
MAX_PAGES = 50

async def fetch_films():
    embeds = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for page_no in range(1, MAX_PAGES+1):
            url = f"{BASE_URL}page/{page_no}/"
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except TimeoutError:
                print(f"[WARN] Timeout {url}")
                continue

            # sayfa 404 veya "Sayfa Bulunamadı" ise dur
            content = await page.content()
            if "Sayfa Bulunamadı" in content or "404" in content:
                print(f"[STOP] Sayfa {page_no} yok, scraping durdu.")
                break

            # film linklerini bul
            film_links = await page.query_selector_all("div.post-container a")
            for film in film_links:
                title = await film.get_attribute("title")
                href = await film.get_attribute("href")
                if not href or not title:
                    continue

                try:
                    await page.goto(href, wait_until="networkidle", timeout=30000)
                except TimeoutError:
                    print(f"[WARN] Timeout film {title}")
                    continue

                # iframe/video embed URL
                embed_url = await page.eval_on_selector(
                    "div.video-player iframe, div.video-player video",
                    "el => el.src"
                )
                if embed_url:
                    embeds.append({"title": title, "embed": embed_url})
                    print(f"[OK] {title}")

        await browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(embeds, f, ensure_ascii=False, indent=2)
    print(f"[DONE] Toplam {len(embeds)} film kaydedildi → {OUTPUT_FILE}")

asyncio.run(fetch_films())
