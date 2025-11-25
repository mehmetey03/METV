import re
from httpx import Client
from Kekik.cli import konsol as log  


class MonoTV:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx = Client(
            timeout=8,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"
            }
        )

    def domain_tara(self):
        """
        https://monotv524.com -> https://monotv999.com
        Arasında çalışan ilk domain bulunur.
        """
        log.log("[cyan][~] monotv524 → monotv999 domain taraması başlıyor...")

        for sayi in range(524, 1000):
            url = f"https://monotv{sayi}.com/"

            try:
                r = self.httpx.get(url)
                if r.status_code == 200:
                    log.log(f"[green][+] Çalışan domain bulundu: {url}")
                    return url.rstrip("/")
            except:
                pass

            log.log(f"[gray]× Çalışmıyor: {url}")

        raise ValueError("Hiçbir monotv domaini çalışmıyor!")

    def yayin_urlini_al(self):
        """
        domain.php yerine artık taramayla çalışır domain buluyor.
        """
        return self.domain_tara()

    def m3u_guncelle(self):
        with open(self.m3u_dosyasi, "r", encoding="utf-8") as f:
            m3u_icerik = f.read()

        yeni_yayin_url = self.yayin_urlini_al()

        pattern = re.compile(
            r'(#EXTVLCOPT:http-referrer=(https?://[^/]*monotv[^/]*\.[^\s/]+).+?\n)(https?://[^ \n\r]+)',
            re.IGNORECASE
        )

        eslesmeler = list(pattern.finditer(m3u_icerik))

        if not eslesmeler:
            raise ValueError("Referer'i monotv olan yayınlar bulunamadı!")

        log.log(f"[yellow][~] Toplam {len(eslesmeler)} yayın bulundu, güncellemeye başlıyorum...")

        degisti_mi = False
        yeni_icerik = m3u_icerik

        for eslesme in eslesmeler:
            eski_link = eslesme[3]

            path_kismi = '/' + '/'.join(eski_link.split('/')[3:])
            yeni_link = yeni_yayin_url + path_kismi

            yeni_link = re.sub(r'(?<!:)//+', '/', yeni_link)

            if eski_link != yeni_link:
                log.log(f"[blue]• Güncellendi: {eski_link} → {yeni_link}")
                yeni_icerik = yeni_icerik.replace(eski_link, yeni_link)
                degisti_mi = True
            else:
                log.log(f"[gray]• Zaten güncel: {eski_link}")

        if degisti_mi:
            with open(self.m3u_dosyasi, "w", encoding="utf-8") as f:
                f.write(yeni_icerik)
            log.log(f"[green][✓] M3U dosyası başarıyla güncellendi.")
        else:
            log.log(f"[green][✓] Tüm yayınlar zaten güncel, dosya değişmedi.")


if __name__ == "__main__":
    guncelle = MonoTV("1.m3u")
    guncelle.m3u_guncelle()
