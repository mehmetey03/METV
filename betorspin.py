import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://maqrizi.com/domain.php"
# Maçların çekildiği gerçek JSON veri kaynağı
MATCH_API = "https://maqrizi.com/betorspin/matches.json" 
TARGET_SITE = "https://63betorspintv.live/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Referer": TARGET_SITE
}

# 34 Kanallık Tam Sabit Liste
SABIT_KANALLAR = {
    "beIN Sports 1": "yayinzirve.m3u8", "beIN Sports 2": "yayinb2.m3u8", "beIN Sports 3": "yayinb3.m3u8",
    "beIN Sports 4": "yayinb4.m3u8", "beIN Sports 5": "yayinb5.m3u8", "beIN Sports Haber": "yayinbeinh.m3u8",
    "S Sport 1": "yayinss.m3u8", "S Sport 2": "yayinss2.m3u8",
    "Tivibu Spor 1": "yayint1.m3u8", "Tivibu Spor 2": "yayint2.m3u8", "Tivibu Spor 3": "yayint3.m3u8", "Tivibu Spor 4": "yayint4.m3u8",
    "Exxen Spor 1": "yayinex1.m3u8", "Exxen Spor 2": "yayinex2.m3u8", "Exxen Spor 3": "yayinex3.m3u8", "Exxen Spor 4": "yayinex4.m3u8",
    "Smart Spor 1": "yayinsmarts.m3u8", "Smart Spor 2": "yayinsmarts2.m3u8",
    "TRT Spor": "yayintrtspor.m3u8", "TRT Spor Yıldız": "yayintrtspor2.m3u8",
    "TV 8.5": "yayintv85.m3u8", "A Spor": "yayinasp.m3u8", "Eurosport 1": "yayineuro1.m3u8", "Eurosport 2": "yayineuro2.m3u8",
    "NBA TV": "yayinnba.m3u8", "FB TV": "yayinfb.m3u8", "GS TV": "yayingstve.m3u8", "BJK TV": "yayinbjk.m3u8"
}

def main():
    m3u_content = ["#EXTM3U"]
    
    try:
        # 1. Sunucu Adresini Al
        print("📡 Sunucu adresi doğrulanıyor...")
        resp = requests.get(API_URL, headers=HEADERS, timeout=10).json()
        base_url = resp.get("baseurl")
        if not base_url: 
            print("❌ Sunucu adresi alınamadı!")
            return

        # 2. Canlı Maçları Çek (JSON tabanlı deneme)
        print("⚽ Canlı maçlar listeleniyor...")
        match_count = 0
        try:
            # Sitenin veriyi çektiği endpoint'i simüle ediyoruz
            m_resp = requests.get(MATCH_API, headers=HEADERS, timeout=5)
            if m_resp.status_code == 200:
                matches = m_resp.json()
                for m in matches:
                    name = f"{m.get('time')} | {m.get('home')} - {m.get('away')}"
                    cid = m.get('id')
                    m3u_content.append(f'#EXTINF:-1 group-title="⚽ CANLI MAÇLAR",{name}')
                    m3u_content.append(f"{base_url}{cid}.m3u8")
                    match_count += 1
        except:
            print("⚠️ Canlı maç servisine şu an ulaşılamıyor, sadece kanallar eklenecek.")

        # 3. Sabit Kanalları Ekle (Düzeltilmiş ve Tam Liste)
        print(f"📺 {len(SABIT_KANALLAR)} Sabit kanal ekleniyor...")
        for name, file in SABIT_KANALLAR.items():
            m3u_content.append(f'#EXTINF:-1 group-title="📺 SPOR KANALLARI",{name}')
            # Bazı linkler direkt .m3u8 içerebilir, kontrol et
            final_link = f"{base_url}{file}" if not file.startswith("http") else file
            m3u_content.append(final_link)

        # 4. Dosyayı Yazdır
        with open("betorspin.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_content))
        
        print(f"✅ Başarılı! Toplam {match_count + len(SABIT_KANALLAR)} içerik kaydedildi.")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    main()
