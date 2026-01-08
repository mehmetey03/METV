import re
import sys
import os
import json
import base64
import binascii
import urllib.parse
import requests
import random
import time

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# API Configuration
API_ENDPOINT = "https://ppv.to/api/streams"
TIMEOUT = 20

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SESSION = requests.Session()
SESSION.headers.update(BASE_HEADERS)

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
SESSION.mount("https://", adapter)
SESSION.mount("http://", adapter)


def fetch_streams_data():
    print(f"Fetching API: {API_ENDPOINT}...")
    try:
        resp = SESSION.get(API_ENDPOINT, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"API Fetch failed: {e}")
        if os.path.exists("ppv_api.json"):
            print("Falling back to local 'ppv_api.json' file.")
            with open("ppv_api.json", "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise e


def extract_m3u8_flexible(text):
    r"""
    Robust extractor that handles:
    1. Plain text URLs
    2. JSON escaped slashes (https:\/\/...)
    3. Base64 encoded strings containing URLs
    """
    if not text:
        return None

    # 1. Clean JSON escaped slashes
    clean_text = text.replace(r"\/", "/")

    # Regex for standard http(s) .m3u8
    # We allow query parameters e.g. .m3u8?token=...
    url_pattern = r'(https?://[^\s"\'<>]+?\.m3u8(?:[\?&][^\s"\'<>]*)?)'

    # Try finding in plain text first
    match = re.search(url_pattern, clean_text)
    if match:
        return match.group(1)

    # 2. Try finding Base64 encoded URLs
    # Look for long strings that might be base64
    base64_candidates = re.findall(r'"([a-zA-Z0-9+/=]{20,})"', clean_text)

    for candidate in base64_candidates:
        try:
            decoded_bytes = base64.b64decode(candidate)
            decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
            # Check if the decoded string contains an m3u8 link
            if ".m3u8" in decoded_str:
                b64_match = re.search(url_pattern, decoded_str)
                if b64_match:
                    return b64_match.group(1)
        except (binascii.Error, UnicodeDecodeError):
            continue

    return None


def origin_of(url):
    try:
        u = urllib.parse.urlparse(url)
        return f"{u.scheme}://{u.netloc}"
    except Exception:
        return None


def fetch_html(url, referer=None):
    headers = {}
    if referer:
        headers["Referer"] = referer
        # Important: Some embeds check Sec-Fetch headers
        headers["Sec-Fetch-Dest"] = "iframe"
        headers["Sec-Fetch-Mode"] = "navigate"
        headers["Sec-Fetch-Site"] = "cross-site"

    try:
        # Add a randomized delay to be polite and avoid rate limits
        delay = random.uniform(2.5, 5.0)
        time.sleep(delay) 
        
        print(f"Fetching {url} (wait: {delay:.2f}s)...")
        resp = SESSION.get(url, headers=headers, timeout=TIMEOUT)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        
        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 429:
            print(f"Rate limited (429) on {url}, waiting 30s before continuing...")
            time.sleep(30)
            return ""
        elif resp.status_code == 403:
            # Just log and continue to next stream - don't stop the script
            print(f"403 Forbidden on {url}. Skipping this stream...")
            return ""
            
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        # Silently fail on network errors during scraping to keep moving
        pass
    return ""


def get_m3u8_for_stream(stream):
    # Try scraping from embed pages to get the correct stream URL
    iframe_url = stream.get("iframe")
    targets = []

    if iframe_url:
        targets.append(iframe_url)

    # Additional fallback based on uri_name
    uri_name = stream.get("uri_name")
    if uri_name:
        targets.append(f"https://ppv.to/live/{uri_name}")

    # Deduplicate
    targets = list(dict.fromkeys(targets))

    for url in targets:
        # We assume the referer is the main site
        html = fetch_html(url, referer="https://ppv.to/")
        m3u8 = extract_m3u8_flexible(html)
        if m3u8:
            # Success - return the scraped URL and the page we got it from
            return m3u8, url

    # Could not find m3u8 URL
    return None, None


def generate_m3u_playlist(streams_data):
    out = ["#EXTM3U"]

    # Handle case where API returns empty or malformed data
    categories = streams_data.get("streams", [])
    if not categories:
        print("Warning: No 'streams' key found in API response.")
        return ""

    total_found = 0

    for category in categories:
        group = category.get("category", "Unknown")
        matches = category.get("streams", [])
        print(f"Processing Category: {group} ({len(matches)} streams)")

        for s in matches:
            name = s.get("name") or "Untitled"
            poster = s.get("poster") or ""

            m3u8_url, ref_page = get_m3u8_for_stream(s)

            if not m3u8_url:
                # Skip if we couldn't find a link
                continue

            total_found += 1
            ref_used = ref_page or "https://ppv.to/"

            out.append(f'#EXTINF:-1 tvg-logo="{poster}" group-title="{group.upper()}",{name}')
            out.append(f"#EXTVLCOPT:http-origin={origin_of(ref_used)}")
            out.append(f"#EXTVLCOPT:http-referrer={ref_used}")
            out.append(f"#EXTVLCOPT:http-user-agent={BASE_HEADERS['User-Agent']}")
            out.append(m3u8_url)

    print(f"\nTotal streams extracted: {total_found}")
    return "\n".join(out) + "\n"


def main():
    try:
        data = fetch_streams_data()
        playlist = generate_m3u_playlist(data)
        if playlist:
            with open("ppv.m3u8", "w", encoding="utf-8") as f:
                f.write(playlist)
            print("Success: M3U playlist generated: ppv.m3u8")
        else:
            print("Failed: No streams were extracted.")
    except Exception as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
