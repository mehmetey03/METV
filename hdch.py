import requests

url = "https://www.hdfilmcehennemi.ws/wp-admin/admin-ajax.php"
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.hdfilmcehennemi.ws/"
}

possible_actions = [
    "load_more", "load_more_movies", "load_more_movies_v2", "load_posts",
    "load_movies", "loadfilms", "film_load", "movie_load", "fetch_movies",
    "ajax_movies", "ajax_load", "home_load", "pagination", "load_pagination",
    "load_more_items", "posts_loadmore"
]

print("Testing possible actions...\n")

for act in possible_actions:
    data = { "action": act, "page": 2 }
    r = requests.post(url, headers=headers, data=data)

    print(f"ACTION TEST: {act} -> HTTP {r.status_code}")

    if r.status_code == 200 and len(r.text.strip()) > 30:
        print("\n🔥 FOUND WORKING ACTION:", act)
        print("Preview:\n", r.text[:200])
        break
