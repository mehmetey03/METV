<?php
// 1. Github txt dosyasından hedef URL al
$sourceUrl = "https://raw.githubusercontent.com/mehmetey03/METV2/refs/heads/main/selcuk.txt";
$ch = curl_init($sourceUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0');
$targetUrl = curl_exec($ch);
curl_close($ch);

if (!$targetUrl) die("Veri alınamadı.");

// 2. Hedef HTML'i çek
$ch = curl_init(trim($targetUrl));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
$html = curl_exec($ch);
curl_close($ch);
if (!$html) die("HTML içeriği alınamadı.");

// 3. DOM parse
$doc = new DOMDocument();
libxml_use_internal_errors(true);
@$doc->loadHTML($html);
libxml_clear_errors();
$xpath = new DOMXPath($doc);
$channels = $xpath->query("//div[contains(@class, 'channel-list')]//a[@data-url]");

// 4. M3U formatı hazırla
$m3u = "#EXTM3U\n";

foreach ($channels as $a) {
    $id = $a->getAttribute("data-id");       // örn: selcukbeinsports1
    $name = $a->textContent;                 // kanal adı
    $logo = $a->getAttribute("data-logo");   // kanal logosu
    $url = $a->getAttribute("data-url");     // m3u8 link

    $m3u .= "#EXTINF:-1 tvg-id=\"$id\" tvg-name=\"$name\" tvg-logo=\"$logo\" group-title=\"Spor\",$name\n";
    $m3u .= "#EXTVLCOPT:http-referrer=https://www.sporcafe6.xyz/\n";
    $m3u .= "$url\n";
}

// 5. Dosyaya yaz
file_put_contents("selcuk.m3u", $m3u);
echo "M3U dosyası oluşturuldu: selcuk.m3u\n";
?>
