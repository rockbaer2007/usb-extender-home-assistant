# Experimenteller Mobile-Server – Befunde und Implementierungsgrenze

## Aktuelle Untersuchung: Abbruch mit 0.1.27 (22. November 2026)

Am echten SM-T580 auf .112 meldet das Journal um 11:24:08 einen vom Server
veranlassten Heartbeat-Timeout. Zuvor funktionierte Start/Vor/Zurück mit 8×8,
144×144-Bildern und zwei Seiten (192 Bilder, drei Context-Pakete, 149/149
Ping/Pong). Der erfolgreiche Durchlauf schließt einen späteren Abbruch nicht aus.
„Channel was closed“ in Android erklärt dessen Ursache nicht näher.

0.1.28 begrenzt Bildarbeit je Empfangsschleife auf maximal vier Bilder und ein
weiches Budget von 25 ms. Ein bereits begonnener Socket-Sendevorgang kann länger
dauern. Zwischen Bildpaketen werden Heartbeat und eingehende Nachrichten wieder
bedient. Ausstehende Bilder bleiben erhalten und werden durch neuere ersetzt;
identische Bilder werden weiterhin nicht erneut übertragen. Der Timeout bleibt
bei 20 Sekunden. Das Trennungsprotokoll enthält zusätzliche Zähler und die letzte
empfangene Nachrichtenart, jedoch keine Inhalte oder Schlüssel.

Langsame Übertragung und wiederholte 8×8-Seitenwechsel sind lokal geprüft.
Anschließend wurde der reale [15-Minuten-Test am SM-T580](tests/mobile-0.1.28-15min-20261122.md)
mit Navigation und rund 14 Minuten Leerlauf bestanden: 16 Messpunkte verbunden,
Ping/Pong 56/56 → 232/232, keine neue Trennung oder Heartbeat-Timeout im Journal.
Dies belegt diesen Zeitraum, nicht die Ursache aller früheren Tablet-Fehler.
Keine Veränderung der Hersteller-App oder Kaufstufe.

Stand 21. November 2026. Unabhängige Implementierung für Interoperabilität;
keine Elgato-Programmdateien, APKs, nativen Bibliotheken oder kopierten
Herstellerimplementierungen werden im Projekt/ZIP verteilt.

## Statische Referenzen

- Windows Stream Deck 7.6.1.23033, EXE SHA-256
  `d9487481d42e5c8d13254c813d5c80158fb58d77c37e8c89036549f3aae38618`.
  Eingebetteter, erfolgreich geparster Protobuf-Deskriptor: Dateibereich
  `0x15a4b00` bis exklusiv `0x15a5c21`, Paket `vsd2`, 36 Nachrichtentypen.
- Android Stream Deck Mobile 2.1.2, Paket `com.corsair.android.streamdeck`.
  XAPK SHA-256 `fcc9b376f9c1bf14f33a051952284105a355c348036256c408adb9344134bf7a`.
  Basis-APK SHA-256 `ac8dff96e76217777c382bb65d568104857778bb6d004e0a178c9d215c0ab067`.
  Enthält die Protokollbeschreibung `messages.proto` und die native Kryptobibliothek.
- REA hat die Archive inventarisiert und in eigene temporäre Verzeichnisse extrahiert.
  Archivbefund `ev_0b485dcd7c8e1b2f23091086e73fc3681ef72b30899f3490ac8e92829800a156`.
  Android-JADX war nicht eingerichtet, native ARM-Analyse im Windows-REA-Profil
  nicht verfügbar. Daher ergänzende, lokale Baksmali-Auswertung mit vorhandenen
  Bibliotheken und Capstone-Disassemblierung, keine Ausführung der Herstellerdateien.

## Beobachteter Vertrag

- QR-Auswertung in `LN3/m;->g` und `LP3/g;->c`: Host `streamdeck.elgato.com`,
  Parameter `w` als nichtleere Serverkennung und `av2` als lokale Adresse/Port.
  Die App speichert den statischen Endpunkt und versucht danach dessen Verbindung.
  Der gefundene Fallback-Port für VSD2 ist 28198. Das ist kein Nachweis, dass die
  gesamte App ohne eigene Online-Dienste auskommt.
- `ClientMessage.hello` ist Feld 1, `ServerMessage.hello` Feld 10. Öffentliche
  Schlüssel stehen in `HelloFromClient.publicKey` (1) und
  `HelloFromServer.publicKey` (5).
- Die Android-Hülle sendet Hello als unverschlüsselte Protobuf-Nachricht und
  verwendet nach dem Server-Hello einen gemeinsamen Schlüssel für weitere Pakete.
- Native Bibliothek `libvsd2-android.so`, SHA-256
  `e232e2e2888ee3c69050a2dfee7c8adaf3447edeaf4381e0e3ca828fc7618f68`:
  JNI encrypt bei ELF-Adresse `0x4e60`, decrypt bei `0x5010`, fingerprint bei
  `0x51c8`. Encrypt reserviert Nutzdatenlänge plus 40 Bytes; 24 zufällige Bytes am
  Paketanfang, danach `crypto_box_easy_afternm` mit 16 Bytes Authentifizierungscode.
  Decrypt nimmt den Nonce aus den ersten 24 Bytes und den Rest als Chiffretext.
- Schlüsselberechnung über `crypto_box_beforenm`. Prüfabdruck: BLAKE2b mit
  32-Byte-Ausgabe über den öffentlichen Client-Schlüssel, erste sechs Hexzeichen.
- `Authenticate` wird erst nach ausdrücklicher lokaler Freigabe mit `Ok`
  beantwortet. Nach erfolgreicher Anmeldung folgt die Liste der virtuellen Geräte.
  Ab 0.1.8 ist die manuelle Prüfanfrage schon nach Hello sichtbar. Wird sie vor
  Authenticate bestätigt, kann der Server die verschlüsselte Geräteliste senden;
  Ok folgt ausschließlich auf eine tatsächlich eintreffende Authenticate-Anfrage.
- Virtuelle Geräte öffnen, `Context` und `Icon` übertragen. Android kündigt
  unterstützte Bildformate an; der Server verwendet bevorzugt LZ4 ohne zusätzlichen
  Größenheader mit BGRA-Pixeln (ab 0.1.13 korrigiert) und expliziten
  Abmessungen/Zeilenbytes, alternativ PNG.
- `ClientMessage.keyPress` (20) enthält `index` (1) und `pressed` (2). Die
  bestehenden MQTT-/Anlern-/Gestenpfade übernehmen diese Eingaben.
- Ab 0.1.9 haben gültige `KeypadConfig.layoutCrop` und spätere
  `UpdateKeypadConfig.layoutCrop` Vorrang für die Editoransicht. Neue Vorgabe ist
  5 Spalten/3 Zeilen. Änderungen einer Servervorgabe erzwingen kein Android-Raster
  und starten den Listener nicht neu; aktive Verbindungen und Decks bleiben offen.

## Android-Pro-Status (statisch geprüft, 0.1.10)

Ergänzende lokale Baksmali-Auswertung derselben Basis-APK; REA-JADX weiterhin
nicht konfiguriert. Das ist statische Analyse, keine beobachtete App-Ausführung.

- `A3/r.l(CustomerInfo)` liest RevenueCat-Entitlements `getActive()` und den
  Eintrag `Full Access`. `A3/r.q` vergleicht den abgeleiteten Status mit
  `AppSettings.getIsProUser()` und aktualisiert ihn über `updateIsProUser`.
- `C3/l` ist laut Konstruktor mit `faceplateManager` und `purchaseService`
  verbunden. `e(C3/b)` lässt ohne Pro nur `C3/b$h` zu; dessen Kennung ist
  `elgato`. Zusätzliche Faceplate-Designs hängen somit am Android-Kaufstatus.
- `T3/a` reicht den Pro-Status in die Android-Geräteeinstellungen weiter.
  `D3/e` baut Rasteroptionen dagegen aus `KnownHost.Device`-Spalten/Zeilen.
  Daraus allein lässt sich die beobachtete 3×5/5×5-Abweichung nicht erklären.
- Unsere Icon-/MQTT-Übertragung setzt keinen Pro-Status und ändert keine APK.
  Vollständiger Funktionsumfang aller Kaufstufen wurde nicht rekonstruiert.

Icon-Wiederholungen: Gleiche `UpdateKeypadConfig.iconSize` erzeugen ab 0.1.10
keinen Refresh. Ein Sitzungscache unterdrückt identische Bildpakete; echte
Änderungen, neue Decköffnung und Größen-/Rasterwechsel übertragen nötige Bilder.

## Abgrenzung

Ab 0.1.14 persistiert das Serverregister die zuletzt bekannte Mobile-Geometrie.
Die dort eingeführte Übersteuerung `devices[id].mobile_layout` ist ab 0.1.15
wieder entfernt: Altwerte bleiben als inaktive Daten erhalten, allein die
Android-Meldung bestimmt das Raster. Offline bleiben Ansicht und Entwürfe erhalten;
ein natives Rasterupdate ersetzt bei Textentwürfen nur das Tastenraster.

## Receive-Timeout und Keepalive (0.1.15)

Nutzeraufnahme zeigt empfangenen Close 1001 `receive timeout`, 24 Bilder/1 Context.
Statisch in derselben APK: `M3/t$a.invokeSuspend` wartet unter Timeout aus
`M3/f.d()` auf das nächste WebSocket-Frame; der Standardwert im dritten
Konstruktorparameter von `M3/f` ist 10 Sekunden. `M3/t.g` beantwortet ein Ping-
Frame mit neuem Pong und leerem Bytearray, ohne das Ping-Payload zurückzukopieren.
Unser früherer 15-Sekunden-Ping war zu spät und seine Zufallsnutzdaten passten
nicht zu diesem nicht spiegelnden Pong.

Jetzt wird alle fünf Sekunden ein leerer Ping gesendet; das leere Pong wird
passend bestätigt. Nicht auf eine Antwort blockieren, keinen zweiten gleichnamigen
Ping senden solange einer offen ist; nach 20 Sekunden ohne Antwort schließen.
Kein Context/Icon für Keepalive. Eigene Ping/Pong-Zähler machen das sichtbar.
Echter lokaler WebSocket mit unabhängigem 10-Sekunden-Frame-Empfangswächter bleibt
16,2 Sekunden ohne Datenframes verbunden, bekommt drei leere Pings und kann danach
weiter Tasten senden. Dieser Stand betraf 0.1.15; der spätere reale
15-Minuten-Test mit 0.1.28 ist oben verlinkt.

APK-Metadaten `Messages.ClientMessage`: AssignShortcut=31 (ProfileID=1,
ShortcutID=2, Index=3), RemoveShortcut=32 (RequestID=1, ShortcutID=2),
TriggerShortcut=33 (DeviceID=1, ShortcutID=2). Diese optionalen Befehle werden
jetzt ohne Sitzungstrennung abgewiesen/ignoriert, nicht ausgeführt. Auch lesbare
unbekannte Erweiterungsfelder eines bereits autorisierten Clients lösen keinen
Abbruch aus; Kryptoprüfung, Ratenlimit und Protobuf-Validierung bleiben erhalten.
Die letzten acht Trennungen werden ohne Schlüsselmaterial diagnostisch erfasst.
Dieser frühere Trennpfad ist belegt, seine Beteiligung am Nutzerproblem noch nicht.

Ab 0.1.13 wird der LZ4-Rohpuffer in BGRA übertragen. Nutzer meldete Rot/Blau-Tausch;
statisch `ImageDecompressor.createBitmap`: LZ4 dekodieren, ARGB_8888-Bitmap erzeugen,
Pixel direkt aus Buffer kopieren. Python-Gegenstelle dekodiert den übertragenen
BGRA-Puffer zurück nach RGBA und prüft die erwarteten Farben.
Identische serialisierte Context-Metadaten werden nicht erneut gesendet. Bei
expliziter Navigation wird weiterhin geantwortet. Der Bildcache vergleicht Pixel-
hash/Größe/Format, veraltete Größen werden verworfen. Sitzungszähler erfassen
erfolgreich gesendete Bilder und Contexts; dies ist noch kein Beleg, dass Android
nicht mehr blinkt. Eine Android-Praxisbestätigung steht aus.

Ab 0.1.12 ist HelloFromServer.version vom Produktrelease getrennt. Eigene
Produktversion 0.1.x war hier falsch: Nutzer sah Androids Mindestversion 6.3.
In derselben APK enthalten `N3/i.<init>` und `N3/m$d.<init>` die Zeichenfolge
`6.3` bzw. `minVersionString`. `M3/m` übernimmt HelloFromServer.getVersion()
in die Servermetadaten. Jetzt wird die explizite Desktop-Protokollkompatibilität
6.3.0 gemeldet, nicht ein vermeintliches Extender-Produktrelease 6.3. Die tatsäch-
liche Produktversion bleibt in UI/CLI und der ergänzenden osVersion-Kennung.
Keine APK-Modifikation und keine Änderung des Kaufstatus. Die Version benennt
die Protokollkompatibilität, nicht Unterstützung aller Desktopfunktionen.

Dies ist ein begrenzter VSD2-Server, kein Nachbau der Windows-Desktopanwendung.
Eine Seite, konfigurierbares Raster bis 64 Tasten, keine serverseitige Pro-Stufe.
Client-Pro-Freischaltungen werden weder gesetzt noch vorgetäuscht. Seiten-
wechsel antworten mit der einzigen verfügbaren Seite; Shortcuts und Android-
Löschanforderungen sind nicht umgesetzt. Kein Bonjour-/Elgato-Cloud-Discovery.
IPv4/Hostnamen als QR-Endpunkt; keine IPv6-Endpunktkodierung.

Die automatisierten Tests verwenden echtes lokales WebSocket/MQTT und PyNaCl Box
als unabhängige Kryptogegenstelle. LZ4-Bilddaten werden dekomprimiert und geprüft.
Das belegt die lokale Implementierung. Der Nutzer bestätigt inzwischen
Kopplung/Decköffnung und die Anzeige eines importierten Icons auf dem SM-T580.
Rasterabgleich, ruhige Bildanzeige nach der Korrektur und vollständige MQTT-
Bedienung bleiben praktische Prüfungen auf dem realen Pi/Android-Gerät.
