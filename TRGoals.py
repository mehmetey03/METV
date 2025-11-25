from Kekik.cli import konsol
from httpx     import Client
from parsel    import Selector
import re

class TRGoals:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx       = Client(timeout=10, verify=False)

    # ----------------------------------------------------------------------
    # 1) M3U içindeki referer domaini bul
    # ----------------------------------------------------------------------
    def referer_domainini_al(self):
        referer_deseni = r'#EXTVLCOPT:http-referrer=(https?://[^/]*trgoals[^/]*\.[^\s/]+)'
        with open(self.m3u_dosyasi, "r") as dosya:
            icerik = dosya.read()

        if eslesme := re.search(referer_deseni, icerik):
            return eslesme[1]
        else:
            raise ValueError("M3U dosyasında 'trgoals' içeren referer domain bulunamadı!")

    # ----------------------------------------------------------------------
    # 2) Redirect çözme (true linki bulur)
    # ----------------------------------------------------------------------
    def redirect_gec(self, url: str):
        konsol.log(f"[cyan][~] redirect_gec: {url}")
        try:
            response = self.httpx.get(url, follow_redirects=True)
        except Exception as e:
            raise ValueError(f"Redirect hatası: {e}")

        tum_url_listesi = [str(r.url) for r in response.history] + [str(response.url)]

        for url in tum_url_listesi[::-1]:  
            if "trgoals" in url:
                return url.strip("/")

        raise ValueError("Redirect zincirinde 'trgoals' içeren link bulunamadı!")

    # ----------------------------------------------------------------------
    # 3) 3 farklı kaynak kullanarak yeni domain bul
    # ----------------------------------------------------------------------
    def yeni_domaini_al(self, eldeki_domain):

        kaynaklar = [
            eldeki_domain,                         # 1) M3U içindeki mevcut domain
            "https://trgoalsgiris.xyz/",           # 2) Resmi giriş
            "https://t.co/fJuteAyTF1",             # 3) Twitter kısa link
            "https://trgoals1464.xyz/"             # 4) Senin verdiğin sabit fallback
        ]

        for kaynak in kaynaklar:
            try:
                konsol.log(f"[yellow][~] Domain deneniyor: {kaynak}")
                d = self.redirect_gec(kaynak)
                konsol.log(f"[green][+] Çalışan domain bulundu: {d}")
                return d
            except Exception:
                konsol.log(f"[red]× Kullanılamadı: {kaynak}")

        # Hepsi bozulmuşsa → sıradaki rakamı artır
        try:
            rakam = int(eldeki_domain.split("trgoals")[1].split(".")[0]) + 1
            return f"https://trgoals{rakam}.xyz"
        except:
            return "https://trgoals1464.xyz"

    # ----------------------------------------------------------------------
    # 4) M3U güncelle
    # ----------------------------------------------------------------------
    def m3u_guncelle(self):
        eldeki_domain = self.referer_domainini_al()
        konsol.log(f"[yellow][~] Eski Domain : {eldeki_domain}")

        yeni_domain = self.yeni_domaini_al(eldeki_domain)
        konsol.log(f"[green][+] Yeni Domain : {yeni_domain}")

        test_url = f"{yeni_domain}/channel.html?id=yayin1"

        with open(self.m3u_dosyasi, "r") as dosya:
            m3u_icerik = dosya.read()

        # Eski baseurl bul
        eski_yayin_eslesme = re.search(r'https?:\/\/[^\/]+\.(shop|click|lat)\/?', m3u_icerik)
        if not eski_yayin_eslesme:
            raise ValueError("M3U dosyasında eski yayın URL'si bulunamadı!")

        eski_yayin_url = eski_yayin_eslesme[0]
        konsol.log(f"[yellow][~] Eski Yayın URL : {eski_yayin_url}")

        # Yeni baseurl çek
        response = self.httpx.get(test_url, follow_redirects=True)

        yayin_ara = re.search(r'(?:var|let|const)\s+baseurl\s*=\s*"(https?://[^"]+)"', response.text)

        if not yayin_ara:
            secici = Selector(response.text)
            if secici.xpath("//title/text()").get() == "404 Not Found":
                yeni_yayin_url = eski_yayin_url
            else:
                raise ValueError("Yeni yayın URL bulunamadı!")
        else:
            yeni_yayin_url = yayin_ara[1]

        konsol.log(f"[green][+] Yeni Yayın URL : {yeni_yayin_url}")

        # M3U içerik güncelle
        yeni_m3u = m3u_icerik.replace(eski_yayin_url, yeni_yayin_url)
        yeni_m3u = yeni_m3u.replace(eldeki_domain, yeni_domain)

        with open(self.m3u_dosyasi, "w") as dosya:
            dosya.write(yeni_m3u)

        konsol.log("[green][✓] M3U başarıyla güncellendi.")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    g = TRGoals("1.m3u")
    g.m3u_guncelle()
