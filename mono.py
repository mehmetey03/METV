import re
from httpx import Client
from Kekik.cli import konsol as log  

class MonoTV:
    def __init__(self, m3u_dosyasi):
        self.m3u_dosyasi = m3u_dosyasi
        self.httpx = Client(
            timeout=10,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
        )

    def domain_tara(self):
        """
        monotv{sayi}.com yapısını tarayarak aktif olanı bulur.
        """
        log.log("[cyan][~] Aktif MonoTV domaini aranıyor (524-999)...")

        # Hız kazanmak için range'i güncelleyebilirsin (örn: 530'dan başlatmak)
        for sayi in range(530, 1000):
            url = f"https://monotv{sayi}.com"
            try:
                # Sadece başlık kontrolü yaparak hızlanıyoruz
                r = self.httpx.head(url)
                if r.status_code < 400:
                    log.log(f"[green][+] Aktif domain bulundu: {url}")
                    return url
            except Exception:
                continue
            
            # log.log(f"[gray]× Deneniyor: {url}") # Çok fazla log kalabalığı yapmaması için kapattım

        raise ValueError("Uygun bir domain bulunamadı!")

    def m3u_guncelle(self):
        try:
            with open(self.m3u_dosyasi, "r", encoding="utf-8") as f:
                m3u_icerik = f.read()
        except FileNotFoundError:
            log.log(f"[red][!] {self.m3u_dosyasi} dosyası bulunamadı!")
            return

        yeni_domain = self.domain_tara()

        # Regex: monotv domainli linkleri yakalar
        # Örn: https://monotv524.com/channel?id=zirve -> https://monotv530.com/channel?id=zirve
        pattern = r"https?://[^/]*monotv\d*\.com"
        
        # Kaç tane eşleşme olduğunu sayalım
        eslesmeler = re.findall(pattern, m3u_icerik)
        
        if not eslesmeler:
            log.log("[yellow][!] Dosyada güncellenecek monotv linki bulunamadı.")
            return

        log.log(f"[yellow][~] {len(eslesmeler)} adet link güncelleniyor...")

        # Tüm eski domainleri yeni bulunanla değiştiriyoruz
        yeni_icerik = re.sub(pattern, yeni_domain, m3u_icerik)

        if yeni_icerik != m3u_icerik:
            with open(self.m3u_dosyasi, "w", encoding="utf-8") as f:
                f.write(yeni_icerik)
            log.log(f"[green][✓] M3U dosyası başarıyla güncellendi: {yeni_domain}")
        else:
            log.log("[green][✓] Dosya zaten güncel.")

if __name__ == "__main__":
    # Dosya adını kontrol et
    islem = MonoTV("mono.m3u")
    islem.m3u_guncelle()

