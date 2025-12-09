import asyncio
import json
import base64
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://www.hdfilmcehennemi.ws/category/film-izle-2/"

async def dc_hello(encoded: str):
    # dc_hello base64 çözümü (siteye özel)
    decoded_once = base64.b64decode(encoded).decode('utf-8')
    reversed_str = decoded_once[::-1]
    decoded_twice = base64.b64decode(reversed_str).decode('utf-8')
    # +, boşluk veya | sonrası link
    if "+" in decoded_twice:
        return decoded_twice.split("+")[-1].strip()
    elif " " in decoded_twice:
        return decoded_twice.split(" ")[-1].strip()
    elif "|" in decoded_twice:
        return decoded_twice.split("|")[-1].strip()
    return decoded_twice.strip()

async def fetch_embed_links(page, url):
    await page.goto(url)
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    scripts = soup.find_all("script")
    embeds = []

    for s in scripts:
        if "dc_hello" in s.text:
            text = s.text
            if 'dc_hello("' in text:
                encoded = text.split('dc_hello("')[1].split('");')[0]
                link = await dc_hello(encoded)
                if link.startswith("http"):
                    embeds.append(link)
    return embeds

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        films = []

        # İlk sayfa kontrolü
        await page.goto(BASE_URL)
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")

        # Filmlerin linklerini al
        film_links = [a['href'] for a in soup.select("a") if "film" in a.get("href", "")]

        for link in film_links:
            embeds = await fetch_embed_links(page, link)
            films.append({"url": link, "embeds": embeds})

        await browser.close()

        # JSON olarak kaydet
        with open("hdceh_embeds.json", "w", encoding="utf-8") as f:
            json.dump(films, f, ensure_ascii=False, indent=4)

        print(f"[DONE] Toplam {len(films)} film kaydedildi → hdceh_embeds.json")

# Çalıştır
asyncio.run(main())
