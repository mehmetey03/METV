#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os

def links_dosyasini_oku():
    """links.txt dosyasını oku ve kanal listesini döndür"""
    kanallar = []
    
    try:
        with open('links.txt', 'r', encoding='utf-8') as dosya:
            icerik = dosya.read()
            print("✅ links.txt dosyası okundu")
    except FileNotFoundError:
        print("❌ links.txt dosyası bulunamadı!")
        return kanallar
    
    satirlar = icerik.split('\n')
    mevcut_kanal = {}
    
    for satir in satirlar:
        satir = satir.strip()
        if not satir:
            if mevcut_kanal:
                kanallar.append(mevcut_kanal)
                mevcut_kanal = {}
            continue
        
        if satir.startswith('isim='):
            mevcut_kanal['isim'] = satir[5:]
        elif satir.startswith('içerik='):
            mevcut_kanal['icerik'] = satir[7:]
        elif satir.startswith('logo='):
            mevcut_kanal['logo'] = satir[5:]
    
    if mevcut_kanal:
        kanallar.append(mevcut_kanal)
    
    print(f"📊 {len(kanallar)} kanal bulundu")
    return kanallar

def get_hls_url_direct(youtube_url):
    """yt-dlp kullanarak HLS URL'sini al"""
    try:
        result = subprocess.run(
            ['yt-dlp', '-g', youtube_url],
            capture_output=True,
            text=True,
            timeout=30
        )
        hls_url = result.stdout.strip()
        if hls_url:
            return hls_url
        return None
    except Exception as e:
        print(f"   ❌ HLS URL alınamadı: {e}")
        return None

def m3u_dosyasi_olustur(kanallar):
    """M3U dosyasını oluştur"""
    m3u_icerik = "#EXTM3U\n"
    basarili_kanallar = 0
    
    for kanal in kanallar:
        if 'hls_url' in kanal and kanal['hls_url']:
            m3u_icerik += f'#EXTINF:-1 tvg-id="{kanal["isim"]}" tvg-name="{kanal["isim"]}" tvg-logo="{kanal["logo"]}" group-title="YouTube",{kanal["isim"]}\n'
            m3u_icerik += f'{kanal["hls_url"]}\n'
            basarili_kanallar += 1
            print(f"   ✅ {kanal['isim']} - HLS URL eklendi")
    
    try:
        with open('youtube.m3u', 'w', encoding='utf-8') as dosya:
            dosya.write(m3u_icerik)
        print(f"✅ youtube.m3u dosyası oluşturuldu ({basarili_kanallar} kanal)")
        return basarili_kanallar
    except Exception as e:
        print(f"❌ M3U dosyası yazılamadı: {e}")
        return 0

def main():
    print("=" * 60)
    print("🚀 YENİ YOUTUBE M3U GENERATOR - BAŞLIYOR")
    print("=" * 60)
    
    kanallar = links_dosyasini_oku()
    if not kanallar:
        print("❌ İşlem iptal edildi: Kanallar bulunamadı")
        return
    
    print("\n" + "=" * 60)
    print("📡 HLS URL'LERİ ALINIYOR...")
    print("=" * 60)
    
    for kanal in kanallar:
        print(f"\n🎬 KANAL: {kanal['isim']}")
        print(f"   🔗 URL: {kanal['icerik']}")
        
        hls_url = get_hls_url_direct(kanal['icerik'])
        
        if hls_url:
            kanal['hls_url'] = hls_url
            print(f"   ✅ BAŞARILI - HLS URL: {hls_url[:100]}...")
        else:
            print(f"   ❌ BAŞARISIZ - HLS URL bulunamadı")
    
    print("\n" + "=" * 60)
    print("📝 M3U DOSYASI OLUŞTURULUYOR...")
    print("=" * 60)
    
    basarili_sayisi = m3u_dosyasi_olustur(kanallar)
    
    print("\n" + "=" * 60)
    print("🎉 SONUÇLAR")
    print("=" * 60)
    print(f"📊 Toplam Kanal: {len(kanallar)}")
    print(f"✅ Başarılı: {basarili_sayisi}")
    print(f"❌ Başarısız: {len(kanallar) - basarili_sayisi}")
    
    if basarili_sayisi > 0:
        print("\n🎉 YOUTUBE.M3U DOSYASI BAŞARIYLA OLUŞTURULDU!")
        print("📁 'youtube.m3u' dosyasını kontrol edin")
    else:
        print("\n⚠️ HİÇBİR KANAL İÇİN HLS URL'Sİ BULUNAMADI!")

if __name__ == "__main__":
    main()
