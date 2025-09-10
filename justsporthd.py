import re
from httpx import Client

class JustSportHDManager:
    def __init__(self):
        self.httpx = Client(timeout=10, verify=False)
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
        self.CHANNELS = [
            {"name": "Bein Sports 1", "logo": "bein1.png", "path": "bein1.m3u8"},
            {"name": "Bein Sports 2", "logo": "bein2.png", "path": "bein2.m3u8"},
            {"name": "Bein Sports 3", "logo": "bein3.png", "path": "bein3.m3u8"},
            {"name": "Bein Sports 4", "logo": "bein4.png", "path": "bein4.m3u8"},
            {"name": "Bein Sports 5", "logo": "bein5.png", "path": "bein5.m3u8"},
            {"name": "Exxen Spor", "logo": "exxen.png", "path": "exxen.m3u8"},
            {"name": "S Sport", "logo": "ssport.png", "path": "ssport.m3u8"},
            {"name": "S Sport 2", "logo": "s2sport.png", "path": "ssport2.m3u8"},
            {"name": "S Spor Plus", "logo": "ssportplus.png", "path": "ssportplus.m3u8"},
            {"name": "Spor Smart", "logo": "sporsmart.png", "path": "sporsmart.m3u8"},
            {"name": "Tivibu Spor 1", "logo": "tivibuspor.png", "path": "tivibu1.m3u8"},
            {"name": "Tivibu Spor 2", "logo": "tivibuspor2.png", "path": "tivibu2.m3u8"},
            {"name": "Tivibu Spor 3", "logo": "tivibuspor3.png", "path": "tivibu3.m3u8"},
        ]

    def find_working_domain(self, start=40, end=100):
        headers = {"User-Agent": self.USER_AGENT}
        for i in range(start, end + 1):
            url = f"https://justsporthd{i}.xyz/"
            try:
                r = self.httpx.get(url, headers=headers, timeout=5)
                if r.status_code == 200 and "JustSportHD" in r.text:
                    print(f"JustSportHD: Çalışan domain bulundu -> {url}")
                    return r.text, url
            except Exception:
                continue
        print("JustSportHD: Çalışan domain bulunamadı.")
        return None, None

    def find_stream_domain(self, html):
        match = re.search(r'https?://(streamnet[0-9]+\.xyz)', html)
        return f"https://{match.group(1)}" if match else None

    def generate_m3u(self):
        html, referer_url = self.find_working_domain()
        if not html or not referer_url:
            return ""

        stream_base_url = self.find_stream_domain(html)
        if not stream_base_url:
            print("JustSportHD: Yayın domaini (streamnet) bulunamadı.")
            return ""

        print(f"JustSportHD: Yayın domaini bulundu -> {stream_base_url}")

        m3u = ['#EXTM3U x-tvg-url=""\n']
        for channel in self.CHANNELS:
            channel_name = f"{channel['name']} JustSportHD"
            logo_url = f"{referer_url.strip('/')}/channel_logo/{channel['logo']}"
            stream_url = f"{stream_base_url}/?url=https://streamcdn.xyz/hls/{channel['path']}"

            m3u.append(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="JustSportHD Liste",{channel_name}')
            m3u.append(f'#EXTVLCOPT:http-referer={referer_url}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={self.USER_AGENT}')
            m3u.append(stream_url)

        content = "\n".join(m3u)

        try:
            with open("justsporthd.m3u", "w", encoding="utf-8") as f:
                f.write(content if content.strip() else '#EXTM3U\n')
            print(f"✅ justsporthd.m3u dosyası başarıyla oluşturuldu! İçerik uzunluğu: {len(content)}")
        except Exception as e:
            print(f"❌ Dosya yazma hatası: {e}")

        return content

if __name__ == "__main__":
    manager = JustSportHDManager()
    manager.generate_m3u()
