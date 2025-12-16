import os
from datetime import datetime

# ---------------- NexaTVManager ----------------
class NexaTVManager:
    def __init__(self):
        self.proxy_prefix = "https://api.codetabs.com/v1/proxy/?quest="
        self.base_stream_url = "https://andro.okan11gote12sokan.cfd/checklist/"
        self.logo_url = "https://i.hizliresim.com/8xzjgqv.jpg"
        self.group_title = "NexaTV"
        self.channels = [
            {"name": "TR:beIN Sport 1 HD", "path": "androstreamlivebs1.m3u8"},
            {"name": "TR:beIN Sport 2 HD", "path": "androstreamlivebs2.m3u8"},
            {"name": "TR:beIN Sport 3 HD", "path": "androstreamlivebs3.m3u8"},
            {"name": "TR:beIN Sport 4 HD", "path": "androstreamlivebs4.m3u8"},
            {"name": "TR:beIN Sport 5 HD", "path": "androstreamlivebs5.m3u8"},
            {"name": "TR:beIN Sport Max 1 HD", "path": "androstreamlivebsm1.m3u8"},
            {"name": "TR:beIN Sport Max 2 HD", "path": "androstreamlivebsm2.m3u8"},
            {"name": "TR:S Sport 1 HD", "path": "androstreamlivess1.m3u8"},
            {"name": "TR:S Sport 2 HD", "path": "androstreamlivess2.m3u8"},
            {"name": "TR:Tivibu Sport HD", "path": "androstreamlivets.m3u8"},
            {"name": "TR:Tivibu Sport 1 HD", "path": "androstreamlivets1.m3u8"},
            {"name": "TR:Tivibu Sport 2 HD", "path": "androstreamlivets2.m3u8"},
            {"name": "TR:Tivibu Sport 3 HD", "path": "androstreamlivets3.m3u8"},
            {"name": "TR:Tivibu Sport 4 HD", "path": "androstreamlivets4.m3u8"},
            {"name": "TR:Smart Sport 1 HD", "path": "androstreamlivesm1.m3u8"},
            {"name": "TR:Smart Sport 2 HD", "path": "androstreamlivesm2.m3u8"},
            {"name": "TR:Euro Sport 1 HD", "path": "androstreamlivees1.m3u8"},
            {"name": "TR:Euro Sport 2 HD", "path": "androstreamlivees2.m3u8"},
            {"name": "TR:Tabii HD", "path": "androstreamlivetb.m3u8"},
            {"name": "TR:Tabii 1 HD", "path": "androstreamlivetb1.m3u8"},
            {"name": "TR:Tabii 2 HD", "path": "androstreamlivetb2.m3u8"},
            {"name": "TR:Tabii 3 HD", "path": "androstreamlivetb3.m3u8"},
            {"name": "TR:Tabii 4 HD", "path": "androstreamlivetb4.m3u8"},
            {"name": "TR:Tabii 5 HD", "path": "androstreamlivetb5.m3u8"},
            {"name": "TR:Tabii 6 HD", "path": "androstreamlivetb6.m3u8"},
            {"name": "TR:Tabii 7 HD", "path": "androstreamlivetb7.m3u8"},
            {"name": "TR:Tabii 8 HD", "path": "androstreamlivetb8.m3u8"},
            {"name": "TR:Exxen HD", "path": "androstreamliveexn.m3u8"},
            {"name": "TR:Exxen 1 HD", "path": "androstreamliveexn1.m3u8"},
            {"name": "TR:Exxen 2 HD", "path": "androstreamliveexn2.m3u8"},
            {"name": "TR:Exxen 3 HD", "path": "androstreamliveexn3.m3u8"},
            {"name": "TR:Exxen 4 HD", "path": "androstreamliveexn4.m3u8"},
            {"name": "TR:Exxen 5 HD", "path": "androstreamliveexn5.m3u8"},
            {"name": "TR:Exxen 6 HD", "path": "androstreamliveexn6.m3u8"},
            {"name": "TR:Exxen 7 HD", "path": "androstreamliveexn7.m3u8"},
        ]

    def calistir(self):
        """NexaTV kanallarından oluşan M3U içeriğini döndürür."""
        m3u = ["#EXTM3U"]
        for channel in self.channels:
            real_url = f"{self.base_stream_url}{channel['path']}"
            stream_url = f"{self.proxy_prefix}{real_url}"
            m3u.append(
                f'#EXTINF:-1 tvg-id="sport.tr" tvg-name="{channel["name"]}" '
                f'tvg-logo="{self.logo_url}" group-title="{self.group_title}",{channel["name"]}'
            )
            m3u.append(stream_url)
        content = "\n".join(m3u)
        print(f"NexaTV içerik uzunluğu: {len(content)} karakter")
        return content


# ---------------- Ana Çalıştırma ----------------
def gorevi_calistir():
    print(f"--- NexaTV Görevi Başlatıldı ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ---")
    manager = NexaTVManager()
    m3u_content = manager.calistir()
    file_name = "NexaTV.m3u"

    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(m3u_content + f"\n\n# Generated: {datetime.utcnow().isoformat()}")
        print(f"✅ M3U dosyası oluşturuldu: {file_name}")
    except Exception as e:
        print(f"❌ Dosya yazılamadı: {e}")

    print("--- Görev Tamamlandı ---")


if __name__ == "__main__":
    gorevi_calistir()



