import requests

class SalamisTVManager:
    def __init__(self):
        self.referer_url = "https://3salamistv.online/"
        self.ajax_url = "https://3salamistv.online/ajax"
        self.logo_url = "https://i.hizliresim.com/t6e66bt.png"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

        self.channels = [
            {"name": "BEIN Sport 1", "id": "701"}, {"name": "BEIN Sport 2", "id": "702"},
            {"name": "BEIN Sport 3", "id": "703"}, {"name": "BEIN Sport 4", "id": "704"},
            {"name": "S Spor", "id": "705"}, {"name": "S Spor 2", "id": "730"},
            {"name": "Tivibu Spor 1", "id": "706"}, {"name": "Tivibu Spor 2", "id": "711"},
            {"name": "Tivibu Spor 3", "id": "712"}, {"name": "Tivibu Spor 4", "id": "713"},
            {"name": "Spor Smart 1", "id": "707"}, {"name": "Spor Smart 2", "id": "708"},
            {"name": "A Spor", "id": "709"}, {"name": "NBA", "id": "nba"},
            {"name": "SKYF1", "id": "skyf1"},
        ]

    def fetch_stream_url(self, channel_id):
        """
        Ajax üzerinden gerçek stream URL’sini alır.
        Örnek JSON:
        {"ok":true,"stream":"https:\/\/savatv16.com\/705\/mono.m3u8"}
        """

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

            data = r.json()
            if data.get("ok") and "stream" in data:
                return data["stream"].replace("\\/", "/")

        except Exception as e:
            print(f"Stream çekme hatası ({channel_id}): {e}")

        return None

    def generate_m3u(self):
        m3u = ['#EXTM3U x-tvg-url=""\n']

        for ch in self.channels:
            real_stream_url = self.fetch_stream_url(ch["id"])

            if not real_stream_url:
                print(f"❌ {ch['name']} için stream bulunamadı!")
                continue

            m3u.append(f'#EXTINF:-1 tvg-id="spor" tvg-logo="{self.logo_url}" group-title="SalamisTV",{ch["name"]}')
            m3u.append(f'#EXTVLCOPT:http-referer={self.referer_url}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={self.user_agent}')
            m3u.append(real_stream_url)

            print(f"✔ {ch['name']} stream eklendi → {real_stream_url}")

        content = "\n".join(m3u)

        try:
            with open("salamistv1.m3u", "w", encoding="utf-8") as f:
                f.write(content)
            print("\n✅ salamistv1.m3u başarıyla oluşturuldu!")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")

        return content


if __name__ == "__main__":
    manager = SalamisTVManager()
    manager.generate_m3u()
