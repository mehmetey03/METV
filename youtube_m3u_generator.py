#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
import json
import os
from urllib.parse import unquote

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

def get_youtube_page(url):
    """YouTube sayfasını proxy ile çek"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.youtube.com/',
        'Origin': 'https://www.youtube.com'
    }
    
    # Farklı proxy servislerini dene
    proxy_servers = [
        f"https://filmproxy.ecfefcesfces.workers.dev/?{url}",
        f"https://seep.eu.org/{url}",
        f"https://api.codetabs.com/v1/proxy/?quest={url}",
        f"https://api.allorigins.win/raw?url={requests.utils.quote(url)}",
        url  # Son çare olarak direkt erişim
    ]
    
    for proxy_url in proxy_servers:
        try:
            print(f"   🔄 Proxy deneniyor: {proxy_url[:80]}...")
            response = requests.get(proxy_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ Proxy başarılı: {len(response.text)} byte veri alındı")
                return response.text
            else:
                print(f"   ❌ Proxy hatası: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ Proxy hatası: {str(e)[:100]}")
            continue
    
    return None

def extract_hls_url(html):
    """HTML'den HLS URL'sini çıkar"""
    if not html:
        return None
    
    # Birden fazla pattern deneyelim
    patterns = [
        r'"hlsManifestUrl":"(https:[^"]+m3u8[^"]*)"',
        r'"hlsManifestUrl":"(https:[^"]+)"',
        r'hlsManifestUrl["\']?\s*:\s*["\'](https:[^"\']+m3u8[^"\']*)["\']',
        r'"url":"(https:[^"]+m3u8[^"]*)"',
        r'"(?:hls|playlist)_url":"(https:[^"]+m3u8[^"]*)"'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        if matches:
            for match in matches:
                # URL'yi temizle
                hls_url = match.replace('\\u0026', '&').replace('\\/', '/')
                if 'm3u8' in hls_url:
                    print(f"   ✅ Pattern eşleşti: {pattern}")
                    return hls_url
    
    # Debug için HTML'nin bir kısmını kaydet
    debug_html = html[:5000]  # İlk 5000 karakter
    with open('debug_html.txt', 'w', encoding='utf-8') as f:
        f.write(debug_html)
    print("   📄 HTML'nin ilk 5000 karakteri debug_html.txt'ye kaydedildi")
    
    return None

def get_hls_url_direct(youtube_url):
    """Direkt YouTube API'sini kullanarak HLS URL'sini al"""
    try:
        # Video ID'yi çıkar
        video_id = None
        if 'v=' in youtube_url:
            video_id = youtube_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in youtube_url:
            video_id = youtube_url.split('youtu.be/')[1].split('?')[0]
        
        if not video_id:
            return None
        
        # YouTube embed sayfasını dene
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        html = get_youtube_page(embed_url)
        hls_url = extract_hls_url(html)
        
        if hls_url:
            return hls_url
        
        # Ana sayfayı dene
        html = get_youtube_page(youtube_url)
        return extract_hls_url(html)
        
    except Exception as e:
        print(f"   ❌ Direkt yöntem hatası: {e}")
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
    
    # 1. links.txt dosyasını oku
    kanallar = links_dosyasini_oku()
    if not kanallar:
        print("❌ İşlem iptal edildi: Kanallar bulunamadı")
        return
    
    # 2. Her kanal için HLS URL'sini al
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
    
    # 3. M3U dosyasını oluştur
    print("\n" + "=" * 60)
    print("📝 M3U DOSYASI OLUŞTURULUYOR...")
    print("=" * 60)
    
    basarili_sayisi = m3u_dosyasi_olustur(kanallar)
    
    # 4. Sonuçları göster
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
        print("\n⚠️  HİÇBİR KANAL İÇİN HLS URL'Sİ BULUNAMADI!")
        print("🔍 'debug_html.txt' dosyasını inceleyerek sorunu analiz edebiliriz")

if __name__ == "__main__":
    main()
