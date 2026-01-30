import re
import httpx

def calistir():
    client = httpx.Client(timeout=10, follow_redirects=True)
    yeni_domain = None
    
    print("Aktif domain taranıyor...")
    for sayi in range(530, 1000):
        url = f"https://monotv{sayi}.com"
        try:
            r = client.head(url)
            if r.status_code < 400:
                yeni_domain = url
                print(f"Bulunan Domain: {yeni_domain}")
                break
        except:
            continue
    
    if yeni_domain:
        m3u_icerik = f"""#EXTM3U
#EXTINF:-1,Zirve TV
#EXTVLCOPT:http-referrer={yeni_domain}/
{yeni_domain}/channel?id=zirve
#EXTINF:-1,Zirve TV (CDN)
https://rei.zirvedesin201.cfd/zirve/mono.m3u8
"""
        with open("mono.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_icerik)
        print("mono.m3u oluşturuldu.")

if __name__ == "__main__":
    calistir()
