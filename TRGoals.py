import re
import time
from parsel import Selector
from httpx import Client, ConnectError, ReadTimeout
from Kekik.cli import konsol


def guvenli_get(client, url, max_retry=5):
    """DNS / timeout hatalarında script kırılmasın diye güvenli GET"""
    for i in range(max_retry):
        try:
            return client.get(url, follow_redirects=True, timeout=10.0)
        except ConnectError:
            konsol.log(f"[yellow][!] DNS çözülemedi, tekrar deneniyor... ({i+1}/{max_retry})")
        except ReadTimeout:
            konsol.log(f"[yellow][!] Timeout, tekrar deneniyor... ({i+1}/{max_retry})")
        except Exception as e:
            konsol.log(f"[red][!] Beklenmeyen hata: {e}")
        time.sleep(2)
    return None


class TRGoals:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx = Client(timeout=10, verify=False)

    # ----------------------------------------------------------------------

    def referer_domainini_al(self):
        """M3U dosyasındaki referer satırından domain oku"""
        referer_deseni = r'#EXTVLCOPT:http-referrer=(https?://[^/]*trgoals[^/]*\.[^\s/]+)'
        with open(self.m3u_dosyasi, "r") as dosya:
            icerik = dosya.read()

        if eslesme := re.search(referer_deseni, icerik):
            return eslesme[1]
        else:
            raise ValueError("M3U dosyasında 'trgoals' içeren referer domain bulunamadı!")

    # ----------------------------------------------------------------------

    def redirect_gec(self, url):
        """Her türlü redirect zincirini çöz, DNS hatasında çökmeden"""
        konsol.log(f"[cyan][~] redirect_gec çağrıldı: {url}")

        response = guvenli_get(self.httpx, url)
        if not response:
            raise ValueError("Redirect çözülemedi (DNS veya Timeout)")

        tum_url_listesi = [str(r.url) for r in response.history] + [str(response.url)]

        for u in reversed(tum_url_listesi):
            if "trgoals" in u:
                return u.rstrip("/")

        raise ValueError("Redirect zincirinde trgoals içeren URL bulunamadı!")

    # ----------------------------------------------------------------------

    def trgoals_domaini_al(self):
        """Ana giriş domainlerini çöz: trgoalsgiris.xyz → bit.ly → t.co → gerçek domain"""
        kaynaklar = [
            "https://trgoalsgiris.xyz/",
            "https://t.co/fJuteAyTF1"
        ]

        for link in kaynaklar:
            try:
                return self.redirect_gec(link)
            except:
                pass

        raise ValueError("Hiçbir giriş domaini çözülemedi!")

    # ----------------------------------------------------------------------

    def yeni_domaini_al(self, mevcut_domain):
        """Mevcut domain çökerse otomatik olarak +1 artır ve yeni domain üret"""
        try:
            return self.redirect_gec(mevcut_domain)
        except:
            konsol.log("[yellow][!] Mevcut domain çözülemedi, giriş domaini deneniyor...")

            try:
                return self.trgoals_domaini_al()
            except:
                konsol.log("[yellow][!] Giriş domainleri de çözülemedi, otomatik +1'e geçiliyor...")

                # trgoals1464.xyz → trgoals1465.xyz gibi
                try:
                    sayi = int(re.search(r"trgoals(\d+)", mevcut_domain).group(1))
                    yeni = f"https://trgoals{sayi+1}.xyz"
                    konsol.log(f"[green][+] Tahmini domain: {yeni}")
                    return yeni
                except:
                    raise ValueError("Yeni domain üretilemedi!")

    # ----------------------------------------------------------------------

    def m3u_guncelle(self):
        konsol.log("[cyan][~] Başlatıldı...")

        eldeki_domain = self.referer_domainini_al()
        konsol.log(f"[yellow][~] Bilinen Domain : {eldeki_domain}")

        yeni_domain = self.yeni_domaini_al(eldeki_domain)
        konsol.log(f"[green][+] Yeni Domain    : {yeni_domain}")

        kontrol_url = f"{yeni_domain}/channel.html?id=yayin1"

        with open(self.m3u_dosyasi, "r") as dosya:
            m3u_icerik = dosya.read()

        # shop / click / lat yayın domainini bul
        eski_yayin = re.search(r'https?:\/\/[^\/]+\.(shop|click|lat)\/?', m3u_icerik)
        if not eski_yayin:
            raise ValueError("M3U dosyasında eski yayın URL'si bulunamadı!")

        eski_yayin_url = eski_yayin[0]
        konsol.log(f"[yellow][~] Eski Yayın URL : {eski_yayin_url}")

        # Yeni yayın URL'si
        response = guvenli_get(self.httpx, kontrol_url)
        if not response:
            konsol.log("[red][!] Yayın sayfası alınamadı, eski yayın kullanılacak.")
            yayin_url = eski_yayin_url
        else:
            yayin_ara = re.search(r'(?:var|let|const)\s+baseurl\s*=\s*"(https?://[^"]+)"', response.text)

            if yayin_ara:
                yayin_url = yayin_ara[1]
            else:
                secici = Selector(response.text)
                if secici.xpath("//title/text()").get() == "404 Not Found":
                    konsol.log("[yellow][!] Yeni domain 404 verdi, eski yayın kullanılacak.")
                    yayin_url = eski_yayin_url
                else:
                    raise ValueError("Base URL bulunamadı!")

        konsol.log(f"[green][+] Yeni Yayın URL : {yayin_url}")

        yeni_m3u = (
            m3u_icerik
            .replace(eski_yayin_url, yayin_url)
            .replace(eldeki_domain, yeni_domain)
        )

        with open(self.m3u_dosyasi, "w") as dosya:
            dosya.write(yeni_m3u)

        konsol.log("[green][✓] M3U başarıyla güncellendi!")


# ----------------------------------------------------------------------

if __name__ == "__main__":
    g = TRGoals("1.m3u")
    g.m3u_guncelle()
