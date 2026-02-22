# patron.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_final_url(url):
    r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=10)
    return r.url, r.text

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
            match_info = {
                "home": teams[0].get_text(strip=True),
                "away": teams[1].get_text(strip=True),
                "time": time_tag.get_text(strip=True) if time_tag else "",
                "league": league_tag.get_text(strip=True) if league_tag else ""
            }
            matches.append(match_info)

    return matches

def save_to_txt(matches):
    with open("karsilasmalar4.txt", "w", encoding="utf-8") as f:
        for m in matches:
            line = f"{m['time']} | {m['home']} vs {m['away']} | {m['league']}"
            f.write(line + "\n")

    print("✅ karsilasmalar4.txt oluşturuldu.")

def main():
    final_url, html = get_final_url(START_URL)
    print("Final URL:", final_url)

    matches = parse_matches(html)
    print(f"{len(matches)} maç bulundu.")

    save_to_txt(matches)

if __name__ == "__main__":
    main()
