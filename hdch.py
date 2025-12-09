#!/usr/bin/env python3
"""
scrape.py
HDFilmCehennemi — flexible scraper (pages -> films.json)

Usage:
  python scrape.py --pages 1-3 --out films.json --embeds
  python scrape.py --start 1 --end 10 --workers 8

Notes:
 - Be polite with site: increase sleep if you get blocked.
 - If Cloudflare blocks, consider running via a headless browser or using a proxy.
"""
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
import argparse
import logging
from urllib.parse import urljoin, urlparse

# -----------------------
# CONFIG
# -----------------------
BASE_DOMAIN = "https://www.hdfilmcehennemi.ws"
DEFAULT_OUTFILE = "films.json"
DEFAULT_WORKERS = 6
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"

# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("scraper")

# -----------------------
# HTTP session with retries
# -----------------------
def create_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    })
    retries = Retry(total=3, backoff_factor=0.6,
                    status_forcelist=(429, 500, 502, 503, 504),
                    allowed_methods=frozenset(["GET", "POST"]))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

SESSION = create_session()

# -----------------------
# Utilities
# -----------------------
def safe_text(node):
    return node.get_text(strip=True) if node else ""

def absolutize(url):
    return urljoin(BASE_DOMAIN, url)

# Flexible selectors for list pages (tries many options)
LIST_SELECTORS = [
    # new site patterns
    "div.posters-4-col a.poster",
    "div.posters-4-col a",
    "div.featured-articles a",
    "a.poster",
    "div.poster a",
    "div.ml-item a",
    "div.movie-item a",
    "article a"
]

def extract_from_list_html(html):
    soup = BeautifulSoup(html, "html.parser")
    anchors = []
    for sel in LIST_SELECTORS:
        found = soup.select(sel)
        if found:
            # prefer the first non-empty selector
            anchors = found
            break

    # Fallback: any <a href="/..."> with title attribute
    if not anchors:
        anchors = soup.select("a[title][href]")

    results = []
    seen = set()
    for a in anchors:
        href = a.get("href") or ""
        if not href:
            continue
        url = absolutize(href)
        if url in seen:
            continue
        seen.add(url)

        # Title: try title attr, then inner text, then child .poster__title
        title = a.get("title") or ""
        if not title:
            # find descendant with title-like classes
            t = a.select_one(".poster__title, .title, .film-title, h2, h3")
            title = safe_text(t)
        title = title.strip()

        # image
        img = a.select_one("img")
        image = ""
        if img:
            image = img.get("data-src") or img.get("data-original") or img.get("src") or ""

        # year
        year = ""
        # look for a nearby span with 4-digit
        span_year = a.select_one("span") or a.select_one(".poster-meta span")
        if span_year:
            txt = span_year.get_text(strip=True)
            import re
            m = re.search(r"(19|20)\d{2}", txt)
            if m:
                year = m.group(0)

        # imdb
        imdb = ""
        imdb_node = a.select_one(".imdb, span.imdb, .rating")
        if imdb_node:
            import re
            m = re.search(r"(\d\.\d)", imdb_node.get_text())
            if m:
                imdb = m.group(1)

        # token - try data-token attr or numeric in href
        token = a.get("data-token") or ""
        if not token:
            import re
            m = re.search(r"/(\d{3,8})/?$", urlparse(url).path)
            if m:
                token = m.group(1)

        # detect type (dizi vs film)
        type_ = "film"
        if "/dizi/" in url or "/serie" in url:
            type_ = "dizi"

        results.append({
            "url": url,
            "title": title,
            "image": image,
            "year": year,
            "imdb": imdb,
            "token": token,
            "type": type_
        })
    return results

# Extract pagination total pages
def extract_total_pages(html):
    import re
    m = re.search(r'data-pages="(\d+)"', html)
    if m:
        return int(m.group(1))
    # fallback: find last pagination number
    soup = BeautifulSoup(html, "html.parser")
    nums = []
    for a in soup.select(".pagination-container a, .pagination a, .page-number"):
        text = a.get_text(strip=True)
        try:
            nums.append(int(text))
        except:
            pass
    return max(nums) if nums else 1

# -----------------------
# Film detail extraction (fetch embed / json-ld / iframe)
# -----------------------
def extract_detail_from_page(html, base_url):
    """
    returns dict with embed_url and extra fields if found
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "embed_url": "",
        "description": "",
        "actors": [],
        "directors": [],
        "genres": []
    }

    # 1) try <script type="application/ld+json">
    for s in soup.select("script[type='application/ld+json']"):
        try:
            data = json.loads(s.string or "{}")
            # sometimes it's a list
            if isinstance(data, dict):
                if not result["description"]:
                    result["description"] = data.get("description", "") or result["description"]
                # actors
                actors = data.get("actor") or data.get("actors")
                if isinstance(actors, list):
                    for a in actors:
                        name = a.get("name") if isinstance(a, dict) else a
                        if name:
                            result["actors"].append(name)
                # genres
                genres = data.get("genre") or data.get("genres")
                if genres:
                    if isinstance(genres, list):
                        result["genres"].extend(genres)
                    else:
                        result["genres"].append(genres)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if not result["description"]:
                            result["description"] = item.get("description", "")
        except Exception:
            continue

    # 2) find iframe embed (rapidrame / embed)
    iframe = soup.find("iframe")
    if iframe and iframe.get("src"):
        src = iframe["src"]
        if "embed" in src or "rapidrame" in src or "player" in src:
            result["embed_url"] = src

    # 3) data-iframe / data-player attributes
    for el in soup.find_all(attrs={"data-iframe": True}):
        if not result["embed_url"]:
            result["embed_url"] = el["data-iframe"]
    for el in soup.find_all(attrs={"data-player": True}):
        if not result["embed_url"]:
            result["embed_url"] = el["data-player"]

    # 4) rapidrame links in page
    import re
    m = re.search(r"(https?:\/\/[^\"']+rapidrame[^\"']+)", html)
    if m and not result["embed_url"]:
        result["embed_url"] = m.group(1)

    # description fallback
    if not result["description"]:
        p = soup.select_one(".description, .film-desc, .entry-content p")
        if p:
            result["description"] = p.get_text(strip=True)

    return result

# fetch film detail (with session)
def fetch_film_detail(session, film):
    url = film["url"]
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            log.warning("Detail fetch failed %s -> %s", url, r.status_code)
            return {**film, "embed_url": ""}
        details = extract_detail_from_page(r.text, url)
        return {**film, **details}
    except Exception as e:
        log.exception("Error fetching detail %s", url)
        return {**film, "embed_url": ""}

# -----------------------
# Main scraping flow
# -----------------------
def scrape_pages(start, end, out_file, workers=DEFAULT_WORKERS, get_embeds=False, sleep_between=0.8):
    session = SESSION
    all_films = []

    # get first page to detect total pages if end is None
    first_url = BASE_DOMAIN if start == 1 else f"{BASE_DOMAIN}/page/{start}/"
    log.info("Fetching first page: %s", first_url)
    r = session.get(first_url, timeout=20)
    if r.status_code != 200:
        log.error("First page fetch failed: %s", r.status_code)
        return False

    total_pages = extract_total_pages(r.text)
    log.info("Detected total pages: %s", total_pages)

    # clamp end
    if end is None:
        end = total_pages
    end = min(end, total_pages)

    page_range = range(start, end + 1)
    log.info("Scraping pages %d..%d", start, end)

    for page in page_range:
        list_url = BASE_DOMAIN if page == 1 else f"{BASE_DOMAIN}/page/{page}/"
        try:
            log.info("GET %s", list_url)
            resp = session.get(list_url, timeout=20)
            if resp.status_code != 200:
                log.warning("Page %s returned %s", page, resp.status_code)
                time.sleep(sleep_between)
                continue
            films = extract_from_list_html(resp.text)
            log.info("Found %d items on page %d", len(films), page)

            # attach page/position
            for idx, f in enumerate(films):
                f["page"] = page
                f["position"] = idx + 1
            all_films.extend(films)

            time.sleep(sleep_between)
        except Exception as e:
            log.exception("Error fetching page %s", page)
            time.sleep(sleep_between * 2)
            continue

    # optionally fetch embeds/details in parallel
    if get_embeds and all_films:
        log.info("Fetching film detail pages (workers=%d)", workers)
        results = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = { ex.submit(fetch_film_detail, session, film): film for film in all_films }
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)
        all_films = results

    # write to file
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(all_films),
        "films": all_films
    }
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    log.info("Saved %d films to %s", len(all_films), out_file)
    return True

# -----------------------
# CLI
# -----------------------
def parse_pages_arg(pages_arg):
    # support formats: "1-5", "3", "1,3,5", None
    if not pages_arg:
        return None, None
    if "-" in pages_arg:
        a,b = pages_arg.split("-",1)
        return int(a), int(b)
    if "," in pages_arg:
        parts = [int(x.strip()) for x in pages_arg.split(",") if x.strip().isdigit()]
        if parts:
            return min(parts), max(parts)
    val = int(pages_arg)
    return val, val

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HDFilmCehennemi scraper (Python)")
    parser.add_argument("--pages", help="pages range e.g. 1-3 or single '1' or '1,3,5'")
    parser.add_argument("--start", type=int, help="start page")
    parser.add_argument("--end", type=int, help="end page")
    parser.add_argument("--out", default=DEFAULT_OUTFILE, help="output json file")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="parallel workers for details")
    parser.add_argument("--embeds", action="store_true", help="fetch film detail embed urls")
    parser.add_argument("--sleep", type=float, default=0.8, help="sleep between page requests")
    args = parser.parse_args()

    if args.pages:
        s,e = parse_pages_arg(args.pages)
    else:
        s = args.start if args.start else 1
        e = args.end if args.end else None

    ok = scrape_pages(start=s, end=e, out_file=args.out, workers=args.workers, get_embeds=args.embeds, sleep_between=args.sleep)
    if not ok:
        log.error("Scrape failed")
        exit(2)
    log.info("Done")
