import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

URL = "https://google-api.global.ssl.fastly.net/fastly/"

session = requests.Session()

HEADERS = {
    "Host": "google-api.global.ssl.fastly.net",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "com.gpiktv.app",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; SM-A505F)",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://gpiktv.app",
    "Referer": "https://gpiktv.app/",
    "Accept-Encoding": "gzip, deflate, br",
}

REQUEST_BODY = {
    "ormoxRoks": "8D9BA85473E0CC1373C85542DE7A516380832C05",
    "qOyOxSzVyL": "66",
    "tICFQdmhzR": ""
}

def fetch_and_save_json():
    logging.info("API isteği başlatılıyor...")

    try:
        # İlk istek: Cookie oluşturulsun diye boş GET → gerçeğe yakın davranış
        try:
            session.get("https://gpiktv.app/", headers=HEADERS, timeout=10)
        except:
            pass

        # Asıl POST isteği
        response = session.post(URL, headers=HEADERS, data=REQUEST_BODY, timeout=15)

        logging.info(f"Durum Kodu: {response.status_code}")
        logging.info("Yanıt önizleme:\n" + response.text[:500])

        # CAPTCHA tespiti
        if "<title>Bot Verification" in response.text or "hcaptcha" in response.text.lower():
            with open("response_raw.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            logging.error("❌ API bot korumasına takıldı! Yanıt response_raw.txt dosyasına kaydedildi.")
            return

        # JSON parse
        try:
            data = response.json()
        except:
            logging.error("❌ JSON olarak ayrıştırılamadı!")
            return

        # JSON kaydet
        filename = "trgoals_data.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logging.info(f"✔ JSON verisi '{filename}' olarak kaydedildi.")

    except Exception as e:
        logging.error(f"Hata: {e}")

if __name__ == "__main__":
    fetch_and_save_json()
