from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re

def get_dynamic_content():
    options = Options()
    options.add_argument('--headless')  # Arka planda çalıştır
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://hepbetspor16.cfd")
    
    # Sayfanın yüklenmesi için bekle
    time.sleep(5)
    
    # Sayfa kaynağını al
    html = driver.page_source
    driver.quit()
    
    return html
