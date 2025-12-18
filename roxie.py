import asyncio
import re
from functools import partial
from urllib.parse import urljoin

import httpx
from selectolax.parser import HTMLParser

# Placeholder utils module
class Cache:
    def __init__(self, filename, exp):
        self.filename = filename
        self.exp = exp
    def load(self):
        return {}
    def write(self, data):
        pass

class Time:
    @staticmethod
    def now():
        import datetime
        return datetime.datetime.now()
    def __init__(self, dt=None):
        import datetime
        self._dt = dt or datetime.datetime.now()

    @staticmethod
    def now():
        import datetime
        return Time(datetime.datetime.now())

    @staticmethod
    def clean(dt):
        # Wrap a datetime in Time, or return as-is if already Time
        if isinstance(dt, Time):
            return dt
        return Time(dt)

    @staticmethod
    def from_str(s, timezone=None):
        import datetime
        # Placeholder: always returns now
        return Time(datetime.datetime.now())

    def delta(self, minutes=0):
        import datetime
        return Time(self._dt + datetime.timedelta(minutes=minutes))

    def timestamp(self):
        return self._dt.timestamp()

class Logger:
    def info(self, msg):
        print(msg)
    def error(self, msg):
        print(msg)

def get_logger(name):
    return Logger()

class Leagues:
    @staticmethod
    def get_tvg_info(sport, event):
        return (None, None)
leagues = Leagues()

class Network:
    @staticmethod
    async def safe_process(handler, url_num, log):
        return await handler()
network = Network()

log = get_logger(__name__)

urls: dict[str, dict[str, str | float]] = {}

CACHE_FILE = Cache("roxie.json", exp=10_800)
HTML_CACHE = Cache("roxie-html.json", exp=19_800)
BASE_URL = "https://roxiestreams.live"
SPORT_ENDPOINTS = {
    "fighting": "Fighting",
    "mlb": "MLB",
    "motorsports": "Racing",
    "nba": "NBA",
    "nfl": "American Football",
    "soccer": "Soccer",
}
TAG = "ROXIE"

async def process_event(
    client: httpx.AsyncClient,
    url: str,
    url_num: int,
) -> str | None:
    try:
        r = await client.get(url)
        r.raise_for_status()
    except Exception as e:
        log.error(f'URL {url_num}) Failed to fetch "{url}": {e}')
        return
    valid_m3u8 = re.compile(
        r"showPlayer\(['\"]clappr['\"],\s*['\"]([^'\"]+?\.m3u8(?:\?[^'\"]*)?)['\"]\)",
        re.IGNORECASE,
    )
    if not (match := valid_m3u8.search(r.text)):
        log.info(f"URL {url_num}) No M3U8 found")
        return
    log.info(f"URL {url_num}) Captured M3U8")
    return match[1]

async def refresh_html_cache(
    client: httpx.AsyncClient,
    url: str,
    sport: str,
    now_ts: float,
) -> dict[str, dict[str, str | float]]:
    try:
        r = await client.get(url)
        r.raise_for_status()
    except Exception as e:
        log.error(f'Failed to fetch "{url}": {e}')
        return {}
    soup = HTMLParser(r.content)
    events = {}
    for row in soup.css("table#eventsTable tbody tr"):
        if not (a_tag := row.css_first("td a")):
            continue
        event = a_tag.text(strip=True)
        if not (href := a_tag.attributes.get("href")):
            continue
        if not (span := row.css_first("span.countdown-timer")):
            continue
        data_start = span.attributes["data-start"].rsplit(":", 1)[0]
        event_dt = Time.from_str(data_start, timezone="PST")
        event_sport = SPORT_ENDPOINTS[sport]
        key = f"[{event_sport}] {event} ({TAG})"
        events[key] = {
            "sport": event_sport,
            "event": event,
            "link": href,
            "event_ts": event_dt.timestamp(),
            "timestamp": now_ts,
        }
    return events

async def get_events(
    client: httpx.AsyncClient,
    sport_urls: dict[str, str],
    cached_keys: set[str],
) -> list[dict[str, str]]:
    now = Time.clean(Time.now())
    if not (events := HTML_CACHE.load()):
        log.info("Refreshing HTML cache")
        tasks = [
            refresh_html_cache(
                client,
                url,
                sport,
                now.timestamp(),
            )
            for sport, url in sport_urls.items()
        ]
        results = await asyncio.gather(*tasks)
        events = {k: v for data in results for k, v in data.items()}
        HTML_CACHE.write(events)
    live = []
    start_ts = now.delta(minutes=-30).timestamp()
    end_ts = now.delta(minutes=30).timestamp()
    for k, v in events.items():
        # Filter out short videos/highlights by keywords in event name
        event_name = v["event"].lower()
        if (
            cached_keys & {k}
            or not start_ts <= v["event_ts"] <= end_ts
            or any(word in event_name for word in ["highlight", "short", "recap", "mini", "replay"])
        ):
            continue
        live.append({**v})
    return live

async def scrape(client: httpx.AsyncClient) -> None:
    cached_urls = CACHE_FILE.load()
    cached_count = len(cached_urls)
    urls.update(cached_urls)
    log.info(f"Loaded {cached_count} event(s) from cache")
    log.info(f'Scraping from "{BASE_URL}"')
    sport_urls = {sport: urljoin(BASE_URL, sport) for sport in SPORT_ENDPOINTS}
    events = await get_events(
        client,
        sport_urls,
        set(cached_urls.keys()),
    )
    log.info(f"Processing {len(events)} new URL(s)")
    if events:
        for i, ev in enumerate(events, start=1):
            handler = partial(
                process_event,
                client=client,
                url=ev["link"],
                url_num=i,
            )
            url = await network.safe_process(
                handler,
                url_num=i,
                log=log,
            )
            if url:
                sport, event, ts = ev["sport"], ev["event"], ev["event_ts"]
                tvg_id, logo = leagues.get_tvg_info(sport, event)
                key = f"[{sport}] {event} ({TAG})"
                entry = {
                    "url": url,
                    "logo": logo,
                    "base": BASE_URL,
                    "timestamp": ts,
                    "id": tvg_id or "Live.Event.us",
                }
                urls[key] = cached_urls[key] = entry
    if new_count := len(cached_urls) - cached_count:
        log.info(f"Collected and cached {new_count} new event(s)")
    else:
        log.info("No new events found")
    CACHE_FILE.write(cached_urls)

    # Also export live streaming events to roxie.json for API/debugging
    import json
    with open("roxie.json", "w", encoding="utf-8") as jf:
        json.dump(urls, jf, ensure_ascii=False, indent=2)

    # Export only working links to M3U playlist
    m3u_lines = ['#EXTM3U']
    for key, entry in cached_urls.items():
        url = entry["url"]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://roxiestreams.live/"
        }
        try:
            resp = await client.get(url, headers=headers, timeout=10)
            if resp.status_code == 200 and (
                "application/vnd.apple.mpegurl" in resp.headers.get("content-type", "") or ".m3u8" in url
            ):
                # Check that the playlist is not empty
                if resp.text.strip():
                    m3u_lines.append(f'#EXTINF:-1 tvg-id="{entry.get("id", "")}" tvg-logo="{entry.get("logo", "")}",{key}')
                    m3u_lines.append(url)
                else:
                    log.info(f"Skipping empty playlist: {url}")
            else:
                log.info(f"Skipping non-working link: {url} (status {resp.status_code})")
        except Exception as e:
            log.info(f"Skipping non-working link: {url} ({e})")
    with open("roxie.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    log.info("Exported working events to roxie.m3u")

if __name__ == "__main__":
    async def main():
        async with httpx.AsyncClient() as client:
            await scrape(client)
    asyncio.run(main())
