# patron.py

import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def extract_js_redirect(html):
    match = re.search(r'window\.location\.href\s*=\s*"([^"]+)"', html)
    if match:
        return match.group(1)
    return None

def get_real_page():
    r = requests.get(START_URL, headers=HEADERS, timeout=10)
    html = r.text

    redirect_url = extract_js_redirect(html)

    if redirect_url:
        print("JS Redirect bulundu:", redirect_url)
        r2 = requests.get(redirect_url, headers=HEADERS, timeout=10)
        return redirect_url, r2.text
    else:
        return START_URL, html

def parse_matches(html):
    soup = BeautifulSoup(html, "html.parser")
    matches = []

    container = soup.find("div", id="matchList")
    if not container:
        return matches

    for item in container.find_all("div", class_="channel-item"):
        time_tag = item.find("span", class_="match-time")
        league_tag = item.find("span", class_="league-text")
        teams = item.find_all("span", class_="team-name")

        if len(teams) == 2:
            matches.append({
                "home": teams[0].get_text(strip=True),
                "away": teams[1].get_text(strip=True),
                "time": time_tag.get_text(strip=True) if time_tag else "",
                "league": league_tag.get_text(strip=True) if league_tag else ""
            })

    return matches

def save_to_txt(matches):
    with open("karsilasmalar4.txt", "w", encoding="utf-8") as f:
        for m in matches:
            line = f"{m['time']} | {m['home']} vs {m['away']} | {m['league']}"
            f.write(line + "\n")

    print("✅ karsilasmalar4.txt oluşturuldu.")

def main():
    final_url, html = get_real_page()
    print("Gerçek URL:", final_url)

    matches = parse_matches(html)
    print(f"{len(matches)} maç bulundu.")

    save_to_txt(matches)

if __name__ == "__main__":
    main()
