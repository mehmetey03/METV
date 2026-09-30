import requests
import re
import urllib3
import warnings
import concurrent.futures

# ============================================================
# UYARILARI KAPAT
# ============================================================

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

warnings.filterwarnings("ignore")


# ============================================================
# AYARLAR
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

OUTPUT_FILENAME = "mahsun.m3u"

BASE_PATTERN = "https://mahsunsports{}.xyz"


# ============================================================
# KANALLAR
# ============================================================

channels = [
    ("androstreamlivebiraz1", "TR:beIN Sport 1 HD-Mahsun"),
    ("androstreamlivebs1", "TR:beIN Sport 1 HD-Mahsun"),

    ("androstreamlivebs2", "TR:beIN Sport 2 HD-Mahsun"),
    ("androstreamlivebs3", "TR:beIN Sport 3 HD-Mahsun"),
    ("androstreamlivebs4", "TR:beIN Sport 4 HD-Mahsun"),
    ("androstreamlivebs5", "TR:beIN Sport 5 HD-Mahsun"),

    ("androstreamlivebsm1", "TR:beIN Sport Max 1 HD-Mahsun"),
    ("androstreamlivebsm2", "TR:beIN Sport Max 2 HD-Mahsun"),

    ("androstreamlivess1", "TR:S Sport 1 HD-Mahsun"),
    ("androstreamlivess2", "TR:S Sport 2 HD-Mahsun"),

    ("androstreamlivets", "TR:Tivibu Sport HD-Mahsun"),
    ("androstreamlivets1", "TR:Tivibu Sport 1 HD-Mahsun"),
    ("androstreamlivets2", "TR:Tivibu Sport 2 HD-Mahsun"),
    ("androstreamlivets3", "TR:Tivibu Sport 3 HD-Mahsun"),
    ("androstreamlivets4", "TR:Tivibu Sport 4 HD-Mahsun"),

    ("androstreamlivesm1", "TR:Smart Sport 1 HD-Mahsun"),
    ("androstreamlivesm2", "TR:Smart Sport 2 HD-Mahsun"),

    ("androstreamlivees1", "TR:Euro Sport 1 HD-Mahsun"),
    ("androstreamlivees2", "TR:Euro Sport 2 HD-Mahsun"),

    ("androstreamlivetb", "TR:Tabii HD-Mahsun"),
    ("androstreamlivetb1", "TR:Tabii 1 HD-Mahsun"),
    ("androstreamlivetb2", "TR:Tabii 2 HD-Mahsun"),
    ("androstreamlivetb3", "TR:Tabii 3 HD-Mahsun"),
    ("androstreamlivetb4", "TR:Tabii 4 HD-Mahsun"),
    ("androstreamlivetb5", "TR:Tabii 5 HD-Mahsun"),
    ("androstreamlivetb6", "TR:Tabii 6 HD-Mahsun"),
    ("androstreamlivetb7", "TR:Tabii 7 HD-Mahsun"),
    ("androstreamlivetb8", "TR:Tabii 8 HD-Mahsun"),

    ("androstreamliveexn", "TR:Exxen HD-Mahsun"),
    ("androstreamliveexn1", "TR:Exxen 1 HD-Mahsun"),
    ("androstreamliveexn2", "TR:Exxen 2 HD-Mahsun"),
    ("androstreamliveexn3", "TR:Exxen 3 HD-Mahsun"),
    ("androstreamliveexn4", "TR:Exxen 4 HD-Mahsun"),
    ("androstreamliveexn5", "TR:Exxen 5 HD-Mahsun"),
    ("androstreamliveexn6", "TR:Exxen 6 HD-Mahsun"),
    ("androstreamliveexn7", "TR:Exxen 7 HD-Mahsun"),
    ("androstreamliveexn8", "TR:Exxen 8 HD-Mahsun"),
]


# ============================================================
# KANAL LİSTESİNDEKİ AYNI İSİMLERİ TEMİZLE
# ============================================================

def remove_duplicate_channels(channel_list):

    unique = []
    seen_names = set()

    for cid, cname in channel_list:

        name_key = cname.strip().lower()

        if name_key in seen_names:
            print(
                f"[DUPLICATE KANAL ATLANDI] {cname}"
            )
            continue

        seen_names.add(name_key)

        unique.append(
            (cid, cname)
        )

    return unique


# ============================================================
# AKTİF DOMAIN BUL
# ============================================================

def find_active_domain():

    print("Aktif domain aranıyor (10-99)...")

    def check_domain(index):

        url = BASE_PATTERN.format(index)

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=5,
                verify=False,
                allow_redirects=True
            )

            if response.status_code == 200:

                return url

        except Exception:

            pass

        return None

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=20
    ) as executor:

        futures = [
            executor.submit(
                check_domain,
                i
            )
            for i in range(10, 100)
        ]

        for future in concurrent.futures.as_completed(
            futures
        ):

            result = future.result()

            if result:

                return result

    return None


# ============================================================
# EVENT SAYFASINDAN SERVERLARI AL
# ============================================================

def get_servers(active_site):

    event_url = (
        f"{active_site}"
        f"/event.html?id=androstreamlivebs1"
    )

    print(
        f"Event sayfası alınıyor: "
        f"{event_url}"
    )

    try:

        response = requests.get(
            event_url,
            headers=HEADERS,
            verify=False,
            timeout=10
        )

        response.raise_for_status()

        html = response.text

    except Exception as e:

        print(
            f"Event sayfası hatası: {e}"
        )

        return []

    # --------------------------------------------------------
    # baseurls = [...]
    # --------------------------------------------------------

    match = re.search(
        r"baseurls\s*=\s*\[(.*?)\]",
        html,
        re.DOTALL | re.IGNORECASE
    )

    if not match:

        print(
            "Sunucu adresleri bulunamadı."
        )

        return []

    urls_text = match.group(1)

    # Tırnakları temizle
    urls_text = (
        urls_text
        .replace('"', "")
        .replace("'", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace(" ", "")
    )

    raw_servers = urls_text.split(",")

    servers = []

    for server in raw_servers:

        server = server.strip()

        if not server:
            continue

        if not server.startswith("http"):
            continue

        server = server.rstrip("/")

        if server not in servers:

            servers.append(server)

    return servers


# ============================================================
# SERVER'IN ÇALIŞIP ÇALIŞMADIĞINI KONTROL ET
# ============================================================

def build_stream_url(server, channel_id):

    server = server.rstrip("/")

    if "checklist" in server.lower():

        url = (
            f"{server}/"
            f"{channel_id}.m3u8"
        )

    else:

        url = (
            f"{server}/checklist/"
            f"{channel_id}.m3u8"
        )

    url = url.replace(
        "checklist//",
        "checklist/"
    )

    return url


# ============================================================
# SERVER TEST
# ============================================================

def test_server(server, active_site):

    test_id = "androstreamlivebs1"

    test_url = build_stream_url(
        server,
        test_id
    )

    test_headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Referer": active_site + "/",
        "Accept": "*/*",
    }

    try:

        response = requests.get(
            test_url,
            headers=test_headers,
            verify=False,
            timeout=7,
            allow_redirects=True
        )

        if response.status_code == 200:

            return server

    except Exception:

        pass

    return None


# ============================================================
# AKTİF SERVERLARI BUL
# ============================================================

def find_active_servers(
    servers,
    active_site
):

    active_servers = []

    print(
        f"Sunucu sayısı: "
        f"{len(servers)}"
    )

    # --------------------------------------------------------
    # Server kontrollerini paralel yap
    # --------------------------------------------------------

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=10
    ) as executor:

        future_map = {
            executor.submit(
                test_server,
                server,
                active_site
            ): server
            for server in servers
        }

        for future in concurrent.futures.as_completed(
            future_map
        ):

            server = future_map[future]

            try:

                result = future.result()

            except Exception:

                result = None

            if result:

                print(
                    f"[AKTİF] {result}"
                )

                active_servers.append(
                    result
                )

            else:

                print(
                    f"[PASİF] {server}"
                )

    # --------------------------------------------------------
    # Aynı server tekrarını kaldır
    # --------------------------------------------------------

    unique_active_servers = []

    for server in active_servers:

        if server not in unique_active_servers:

            unique_active_servers.append(
                server
            )

    return unique_active_servers


# ============================================================
# TEK KANAL İÇİN ÇALIŞAN SERVER BUL
# ============================================================

def find_working_channel_url(
    channel_id,
    active_servers,
    active_site
):

    for server in active_servers:

        stream_url = build_stream_url(
            server,
            channel_id
        )

        headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Referer": active_site + "/",
            "Accept": "*/*",
        }

        try:

            response = requests.get(
                stream_url,
                headers=headers,
                verify=False,
                timeout=6,
                allow_redirects=True
            )

            if response.status_code == 200:

                return stream_url

        except Exception:

            continue

    return None


# ============================================================
# ANA KANAL TARAMASI
# ============================================================

def get_andro_content():

    print(
        "\n--- Andro Panel Taraması Başlatıldı ---"
    )

    results = []

    # --------------------------------------------------------
    # Kanal isimlerindeki duplicate kayıtları temizle
    # --------------------------------------------------------

    clean_channels = remove_duplicate_channels(
        channels
    )

    print(
        f"Tanımlı kanal sayısı: "
        f"{len(channels)}"
    )

    print(
        f"Benzersiz kanal sayısı: "
        f"{len(clean_channels)}"
    )

    # --------------------------------------------------------
    # Aktif domain
    # --------------------------------------------------------

    active_site = find_active_domain()

    if not active_site:

        print(
            "\nAktif site bulunamadı."
        )

        return results

    print(
        f"\nBulunan Domain: "
        f"{active_site}"
    )

    # --------------------------------------------------------
    # Server listesini al
    # --------------------------------------------------------

    servers = get_servers(
        active_site
    )

    if not servers:

        print(
            "Hiçbir sunucu bulunamadı."
        )

        return results

    print(
        f"Bulunan sunucu sayısı: "
        f"{len(servers)}"
    )

    # --------------------------------------------------------
    # Aktif serverları test et
    # --------------------------------------------------------

    active_servers = find_active_servers(
        servers,
        active_site
    )

    if not active_servers:

        print(
            "\nÇalışan sunucu bulunamadı."
        )

        return results

    print(
        f"\nToplam çalışan sunucu: "
        f"{len(active_servers)}"
    )

    # --------------------------------------------------------
    # HER KANALI SADECE 1 KEZ EKLE
    # --------------------------------------------------------

    added_names = set()

    for channel_id, channel_name in clean_channels:

        name_key = channel_name.strip().lower()

        # Ekstra güvenlik
        if name_key in added_names:

            print(
                f"[ATLANDI] Duplicate: "
                f"{channel_name}"
            )

            continue

        print(
            f"\nKontrol ediliyor: "
            f"{channel_name}"
        )

        # ----------------------------------------------------
        # Çalışan server bul
        # ----------------------------------------------------

        final_url = find_working_channel_url(
            channel_id,
            active_servers,
            active_site
        )

        if not final_url:

            print(
                f"[YOK] "
                f"{channel_name}"
            )

            continue

        # ----------------------------------------------------
        # LOGO YOK
        # tvg-logo YOK
        # ----------------------------------------------------

        entry = (
            f'#EXTINF:-1 '
            f'group-title="Spor",'
            f'{channel_name}\n'
            f'#EXTVLCOPT:http-referrer='
            f'{active_site}/\n'
            f'{final_url}'
        )

        results.append(
            entry
        )

        added_names.add(
            name_key
        )

        print(
            f"[OK] {channel_name}"
        )

        print(
            f"     {final_url}"
        )

    return results


# ============================================================
# M3U OLUŞTUR
# ============================================================

def main():

    print(
        "========================================"
    )

    print(
        "        MAHSUN M3U GÜNCELLEYİCİ"
    )

    print(
        "========================================"
    )

    print(
        "\nİşlem Başladı..."
    )

    channels_result = get_andro_content()

    # --------------------------------------------------------
    # M3U başlığı
    # --------------------------------------------------------

    all_content = [
        "#EXTM3U"
    ]

    all_content.extend(
        channels_result
    )

    # --------------------------------------------------------
    # Dosyaya yaz
    # --------------------------------------------------------

    try:

        with open(
            OUTPUT_FILENAME,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "\n".join(
                    all_content
                )
            )

        print(
            "\n========================================"
        )

        print(
            "BAŞARILI"
        )

        print(
            f"Kanal sayısı: "
            f"{len(channels_result)}"
        )

        print(
            f"Dosya: "
            f"{OUTPUT_FILENAME}"
        )

        print(
            "Logo: YOK"
        )

        print(
            "Duplicate: TEMİZLENDİ"
        )

        print(
            "========================================"
        )

    except IOError as e:

        print(
            f"\nDosya yazma hatası: {e}"
        )


# ============================================================
# BAŞLAT
# ============================================================

if __name__ == "__main__":

    main()
