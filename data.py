import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

URL = "https://google-api.global.ssl.fastly.net/fastly/"

HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/79.0',
    'X-Requested-With': 'com.gpiktv.app',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

REQUEST_BODY = {
    'ormoxRoks': '8D9BA85473E0CC1373C85542DE7A516380832C05',
    'qOyOxSzVyL': '66',
    'tICFQdmhzR': ''
}

def fetch_and_save_json():
    logging.info("API isteği başlatılıyor...")

    try:
        response = requests.post(URL, headers=HEADERS, data=REQUEST_BODY, timeout=15)
        logging.info(f"Durum Kodu: {response.status_code}")

        # Yanıtı debug için kaydedelim
        raw_preview = response.text[:500]
        logging.info(f"Yanıt (ilk 500 karakter):\n{raw_preview}")

        # JSON olmayan yanıtı kaydet
        if not response.text.strip().startswith('{'):
            with open("response_raw.txt", "w", encoding="utf-8") as f:
                f.write(response.text)
            logging.error("Yanıt JSON formatında değil! --> response_raw.txt'e kaydedildi.")
            return

        try:
            data = response.json()
            logging.info("JSON başarıyla ayrıştırıldı.")
        except json.JSONDecodeError:
            logging.error("Yanıt JSON olarak ayrıştırılamadı!")
            return

        filename = "trgoals_data.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        logging.info(f"JSON verisi '{filename}' dosyasına kaydedildi.")

    except requests.exceptions.RequestException as e:
        logging.error(f"İstek sırasında hata oluştu: {e}")

if __name__ == "__main__":
    fetch_and_save_json()
