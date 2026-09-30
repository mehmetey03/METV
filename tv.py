import requests
import re
import urllib3
import warnings
import concurrent.futures

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

OUTPUT_FILENAME = "mahsun.m3u"



def get_andro_content():
    print("--- Andro Panel Taraması Başlatıldı ---")

    results = []

    base_pattern = "https://mahsunsports{}.xyz"
    headers = HEADERS.copy()

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

    # ---------------------------------------------------------
    # AKTİF DOMAIN BUL
    # ---------------------------------------------------------

    def check_domain(index):
        url = base_pattern.format(index)

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=5,
                verify=False
            )

            if response.status_code == 200:
                return url

        except Exception:
            pass

        return None

    print("Aktif domain aranıyor (10-99)...")

    active_site = None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:

        futures = [
            executor.submit(check_domain, i)
            for i in range(10, 100)
        ]

        for future in concurrent.futures.as_completed(futures):

            result = future.result()

            if result:
                active_site = result
                break

    if not active_site:
        print("Aktif site bulunamadı.")
        return results

    print(f"Bulunan Domain: {active_site}")

    # ---------------------------------------------------------
    # EVENT SAYFASINI AL
    # ---------------------------------------------------------

    event_url = f"{active_site}/event.html?id=androstreamlivebs1"

    try:
        r2 = requests.get(
            event_url,
            headers=headers,
            verify=False,
            timeout=10
        )

        h2_text = r2.text

    except Exception as e:

        print(f"Event sayfası hatası: {e}")
        return results

    # ---------------------------------------------------------
    # BASEURL LİSTESİNİ BUL
    # ---------------------------------------------------------

    baseurl_match = re.search(
        r"baseurls\s*=\s*\[(.*?)\]",
        h2_text,
        re.DOTALL | re.IGNORECASE
    )

    if not baseurl_match:
        print("Sunucu adresleri bulunamadı.")
        return results

    urls_text = (
        baseurl_match.group(1)
        .replace('"', "")
        .replace("'", "")
        .replace("\n", "")
        .replace("\r", "")
    )

    servers = [
        url.strip()
        for url in urls_text.split(",")
        if url.strip().startswith("http")
    ]

    # Aynı server tekrarını temizle
    unique_servers = []

    for server in servers:

        server = server.rstrip("/")

        if server not in unique_servers:
            unique_servers.append(server)

    servers = unique_servers

    print(f"Bulunan sunucu sayısı: {len(servers)}")

    # ---------------------------------------------------------
    # ÇALIŞAN SUNUCULARI TEST ET
    # ---------------------------------------------------------

    active_servers = []

    test_id = "androstreamlivebs1"

    for server in servers:

        server = server.rstrip("/")

        if "checklist" in server:
            test_url = f"{server}/{test_id}.m3u8"
        else:
            test_url = f"{server}/checklist/{test_id}.m3u8"

        test_url = test_url.replace(
            "checklist//",
            "checklist/"
        )

        try:

            temp_response = requests.get(
                test_url,
                headers={
                    "Referer": active_site + "/",
                    "User-Agent": HEADERS["User-Agent"],
                },
                verify=False,
                timeout=5
            )

            if temp_response.status_code == 200:

                print(f"[AKTİF] {server}")

                active_servers.append(server)

            else:

                print(
                    f"[PASİF] {server} "
                    f"HTTP {temp_response.status_code}"
                )

        except Exception:

            print(f"[PASİF] {server}")

            continue

    if not active_servers:

        print("Çalışan yayın sunucusu bulunamadı.")
        return results

    print(
        f"\nToplam çalışan sunucu: "
        f"{len(active_servers)}"
    )

    # ---------------------------------------------------------
    # ÖNEMLİ:
    # HER KANAL SADECE 1 KEZ EKLENECEK
    #
    # Çalışan sunucular sırayla denenir.
    # Bir kanal için çalışan ilk sunucu seçilir.
    # ---------------------------------------------------------

    used_channels = set()

    for cid, cname in channels:

        if cid in used_channels:
            continue

        selected_server = None

        # Her kanal için çalışan sunucuları dene
        for server in active_servers:

            server = server.rstrip("/")

            if "checklist" in server:

                final_url = (
                    f"{server}/{cid}.m3u8"
                )

            else:

                final_url = (
                    f"{server}/checklist/{cid}.m3u8"
                )

            final_url = final_url.replace(
                "checklist//",
                "checklist/"
            )

            try:

                test_response = requests.get(
                    final_url,
                    headers={
                        "Referer": active_site + "/",
                        "User-Agent": HEADERS["User-Agent"],
                    },
                    verify=False,
                    timeout=5
                )

                if test_response.status_code == 200:

                    selected_server = server

                    print(
                        f"[OK] {cname} -> "
                        f"{server}"
                    )

                    break

            except Exception:

                continue

        # Hiçbir sunucuda kanal yoksa ekleme
        if not selected_server:

            print(
                f"[YOK] {cname} "
                f"çalışan sunucuda bulunamadı."
            )

            continue

        # URL oluştur
        if "checklist" in selected_server:

            final_url = (
                f"{selected_server}/{cid}.m3u8"
            )

        else:

            final_url = (
                f"{selected_server}/checklist/{cid}.m3u8"
            )

        final_url = final_url.replace(
            "checklist//",
            "checklist/"
        )

        entry = (
            f'#EXTINF:-1 '
            f'tvg-logo="{STATIC_LOGO}" '
            f'group-title="Spor",'
            f'{cname}\n'
            f'#EXTVLCOPT:http-referrer='
            f'{active_site}/\n'
            f'{final_url}'
        )

        results.append(entry)

        used_channels.add(cid)

    print(
        f"\nBenzersiz kanal sayısı: "
        f"{len(results)}"
    )

    return results


def main():

    print("İşlem Başladı...")

    all_content = ["#EXTM3U"]

    channels = get_andro_content()

    all_content.extend(channels)

    try:

        with open(
            OUTPUT_FILENAME,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "\n".join(all_content)
            )

        print(
            f"\nBaşarılı!"
            f"\n{len(channels)} benzersiz kanal kaydedildi."
            f"\nDosya: {OUTPUT_FILENAME}"
        )

    except IOError as e:

        print(f"\nDosya yazma hatası: {e}")


if __name__ == "__main__":
    main()
