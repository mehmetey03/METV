#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os

def links_dosyasini_oku():
    kanallar = []
    try:
        with open('links.txt', 'r', encoding='utf-8') as f:
            satirlar = f.read().splitlines()
    except FileNotFoundError:
        print("❌ links.txt bulunamadı!")
        return kanallar

    mevcut = {}
    for satir in satirlar:
        satir = satir.strip()
        if not satir:
            if mevcut:
                kanallar.append(mevcut)
                mevcut = {}
            continue
        if satir.startswith('isim='):
            mevcut['isim'] = satir[5:]
        elif satir.startswith('içerik='):
            mevcut['icerik'] = satir[7:]
        elif satir.startswith('logo='):
            mevcut['logo'] = satir[5:]
    if mevcut:
        kanallar.append(mevcut)
    print(f"📊 {len(kanallar)} kanal bulundu")
    return kanallar

def get_hls_with_ytdlp(url):
    try:
        result = subprocess.run(['yt-dlp', '-g', url], capture_output=True, text=True, timeout=30)
        hls_url = result.stdout.strip()
        if hls_url:
            return hls_url
        else:
            return None
    except Exception as e:
        print(f"⚠️ yt-dlp hatası: {e}")
        return None

def m3u_dosyasi_olustur(kanallar):
    m3u_icerik = "#EXTM3U\n"
    basarili = 0
    for kanal in kanallar:
        hls_url = kanal.get('hls_url')
        if hls_url:
            m3u_icerik += f'#EXTINF:-1 tvg-id="{kanal["isim"]}" tvg-name="{kanal["isim"]}" tvg-logo="{kanal["logo"]}" group-title="YouTube",{kanal["isim"]}\n'
            m3u_icerik += f'{hls_url}\n'
            basarili += 1
            print(f"✅ {kanal['isim']} eklendi")
    with open('youtube.m3u', 'w', encoding='utf-8') as f:
        f.write(m3u_icerik)
    print(f"✅ youtube.m3u oluşturuldu ({basarili} kanal)")

def main():
    kanallar = links_dosyasini_oku()
    if not kanallar:
        return

    for kanal in kanallar:
        print(f"\n🎬 Kanal: {kanal['isim']}")
        print(f"   🔗 URL: {kanal['icerik']}")
        kanal['hls_url'] = get_hls_with_ytdlp(kanal['icerik'])
        if kanal['hls_url']:
            print(f"   ✅ HLS URL alındı")
        else:
            print(f"   ❌ HLS URL alınamadı")
    
    m3u_dosyasi_olustur(kanallar)

if __name__ == "__main__":
    main()
