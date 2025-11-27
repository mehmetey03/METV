import requests

class SalamisTVManager:
    def __init__(self):
        self.referer_url = "https://3salamistv.online/"
        self.ajax_url = "https://3salamistv.online/ajax"
        self.logo_url = "https://i.hizliresim.com/t6e66bt.png"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

        # ✔ DOĞRU STREAM ANAHTARLARI
        self.channels = [
            {"name": "S Spor", "id": "s-sport"},
            {"name": "S Spor 2", "id": "s-sport2"},
            {"name": "Tivibu Spor 1", "id": "t-sport1"},
            {"name": "Tivibu Spor 2", "id": "t-sport2"},
            {"name": "Tivibu Spor 3", "id": "t-sport3"},
            {"name": "Tivibu Spor 4", "id": "t-sport4"},
            {"name": "Spor Smart 1", "id": "spor-smart1"},
            {"name": "Spor Smart 2", "id": "spor-smart2"},
            {"name": "A Spor", "id": "a-spor"},
            {"name": "NBA", "id": "nba"},
            {"name": "Sky F1", "id": "skyf1"},
        ]

    def fetch_stream_url(self, channel_id):
        print(f"\n👉 {channel_id} için stream URL alınıyor...")

        try:
            r = requests.get(
                self.ajax_url,
                params={
                    "method": "channel_stream",
                    "stream": channel_id
                },
                headers={
                    "User-Agent": self.user_agent,
                    "Referer": self.referer_url,
                    "X-Requested-With": "XMLHttpRequest"
                },
                timeout=10
            )

            print(f"🔹 HTTP {r.status_code} – Cevap: {r.text[:200]}")

            data = r.json()
            if data.get("ok") and "stream" in data:
                url = data["stream"].replace("\\/", "/")
                print(f"✔ Stream bulundu: {url}")
                return url

        except Exception as e:
            print(f"❌ HATA ({channel_id}): {e}")

        print(f"❌ Stream bulunamadı ({channel_id})")
        return None

    def generate_m3u(self):
        m3u = ['#EXTM3U\n']

        for ch in self.channels:
            url = self.fetch_stream_url(ch["id"])
            if not url:
                continue

            m3u.append(f'#EXTINF:-1 tvg-logo="{self.logo_url}" group-title="SalamisTV",{ch["name"]}')
            m3u.append(f'#EXTVLCOPT:http-referer={self.referer_url}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={self.user_agent}')
            m3u.append(url)

        content = "\n".join(m3u)

        print("\n🔍 OLUŞAN M3U İÇERİĞİ:")
        print(content)

        try:
            with open("salamistv.m3u", "w", encoding="utf-8") as f:
                f.write(content)
            print("\n✅ salamistv.m3u başarıyla oluşturuldu!")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")


if __name__ == "__main__":
    SalamisTVManager().generate_m3u()
