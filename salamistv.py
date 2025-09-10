class SalamisTVManager:
    def __init__(self):
        self.referer_url = "https://salamistv15.online/"
        self.base_stream_url = "https://macarenatv4.com"
        self.logo_url = "https://i.hizliresim.com/b6xqz10.jpg"
        self.channels = [
            {"name": "BEIN Sport 1", "id": "701"}, {"name": "BEIN Sport 2", "id": "702"},
            {"name": "BEIN Sport 3", "id": "703"}, {"name": "BEIN Sport 4", "id": "704"},
            {"name": "S Spor", "id": "705"}, {"name": "S Spor 2", "id": "730"},
            {"name": "Tivibu Spor 1", "id": "706"}, {"name": "Tivibu Spor 2", "id": "711"},
            {"name": "Tivibu Spor 3", "id": "712"}, {"name": "Tivibu Spor 4", "id": "713"},
            {"name": "Spor Smart 1", "id": "707"}, {"name": "Spor Smart 2", "id": "708"},
            {"name": "A Spor", "id": "709"}, {"name": "NBA", "id": "nba"}, {"name": "SKYF1", "id": "skyf1"},
        ]

    def generate_m3u(self):
        m3u = ['#EXTM3U x-tvg-url=""\n']
        for channel in self.channels:
            stream_url = f"{self.base_stream_url}/{channel['id']}/mono.m3u8"
            m3u.append(f'#EXTINF:-1 tvg-id="spor" tvg-logo="{self.logo_url}" group-title="SalamisTV",{channel["name"]}')
            m3u.append(f'#EXTVLCOPT:http-referer={self.referer_url}')
            m3u.append(stream_url)

        content = "\n".join(m3u)

        try:
            with open("salamistv.m3u", "w", encoding="utf-8") as f:
                f.write(content if content.strip() else '#EXTM3U\n')
            print(f"✅ salamistv.m3u başarıyla oluşturuldu! İçerik uzunluğu: {len(content)}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")

        return content


if __name__ == "__main__":
    manager = SalamisTVManager()
    manager.generate_m3u()
