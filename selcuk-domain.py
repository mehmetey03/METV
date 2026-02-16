import requests
import re
import os

def yayin_linki_yakala():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        ana_site = "https://www.selcuksportshd.is/"
        r1 = requests.get(ana_site, headers=headers, timeout=15)
        
        # Giriş linkini (xyz) en basit regex ile bul
        giris_match = re.search(r'https?://[a-zA-Z0-9.-]+\.xyz', r1.text)
        
        if giris_match:
            guncel_giris_adresi = giris_match.group(0)
            r2 = requests.get(guncel_giris_adresi, headers=headers, timeout=15)
            html_content = r2.text
            
            # Senin loglarda çıkan linkleri yakalayan en garanti regex
            # index.php?id= kısmına kadar olanı alır, sonrasındaki pislikleri (#, &, ") atar
            player_match = re.search(r'(https://[a-zA-Z0-9.-]+\.click/index\.php\?id=)[^#&"\'\s]+', html_content)
            
            if player_match:
                # Sadece kök linki ve id kısmını alıyoruz
                final_player_link = player_match.group(1)
                
                with open("Slck-player.txt", "w", encoding="utf-8") as f:
                    f.write(final_player_link)
                print(f"BAŞARILI: {final_player_link}")
            else:
                print("FAIL: Player linki loglarda vardı ama ayıklanamadı.")
        else:
            print("FAIL: Giriş linki (.xyz) ana sayfada bulunamadı.")
            
    except Exception as e:
        print(f"HATA: {e}")

if __name__ == "__main__":
    yayin_linki_yakala()
    
