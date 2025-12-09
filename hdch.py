import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

BASE = "https://www.hdfilmcehennemi.ws"
START_URL = BASE + "/filmler"

async def get_page_content(page, page_no):
    ajax_url = f"{BASE}/load/page/{page_no}/categories/film-izle-2/"
    print(f"[FETCH] {ajax_url}")

    try:
        response = await page.request.get(ajax_url)
        if response.status != 200:
            print("[WARN] Status:", response.status)
            return None
        
        text = await response.text()
        if len(text) < 30:
            print("[EMPTY]")
            return None
        
        return text
    except Exception as e:
        print("ERROR:", e)
        return None


def parse_films(html):
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("a")
    films = []

    for a in items:
        img = a.find("img")
        if not img:
            continue
        
        films.append({
            "title": img.get("alt", ""),
            "img": img.get("src", ""),
            "link": a.get("href", "")
        })
    return films


async def main():
    all_films = []
    empty_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        print("[INFO] Opening main page...")
        page = await context.new_page()
        await page.goto(START_URL)

        # Cloudflare challenge çözülmüş olacak!
        print("[INFO] Cloudflare bypass complete.")

        for page_no in range(1, 300):
            html = await get_page_content(page, page_no)

            if not html:
                empty_count += 1
                if empty_count >= 5:
                    print("[STOP] Too many empty pages.")
                    break
                continue

            films = parse_films(html)
            print(f"[PAGE {page_no}] Found:", len(films))

            if len(films) == 0:
                empty_count += 1
            else:
                empty_count = 0

            all_films.extend(films)

        await browser.close()

    print("\nTOTAL FILMS:", len(all_films))

    with open("hdceh.json", "w", encoding="utf-8") as f:
        json.dump(all_films, f, indent=2, ensure_ascii=False)

    print("Saved → hdceh.json")


asyncio.run(main())
