# Aplic 305045: Praxistest vom 22.11.2026

## Sicherung und Ausgangslage

- .112 zeigt USB Extender 0.1.35 und aktiven USB-/MQTT-Dienst. Diese Version war
  bereits vom Nutzer installiert; keine erneute Installation durch den Agenten.
- Vom Nutzer im offenen SSH-Terminal ausgeführte Sicherung erfolgreich gelesen:
  `/var/backups/scanner-before-test-035-20261122-192104.tar.gz`.
  Inhalt und Hashes geprüft: config.json, switches.json, mobile-identity.json,
  mobile-trust.json und mobile-devices.json. Vorherigen Dienstzustand wiederhergestellt.
- Aplic als „2D Barcode Scanner“, USB 1eab:0003, gespeicherte Geräte-ID
  `1eab-0003-9731ccf58cc2`. Scanner-Modus aktiv, DE, Enter, 500 ms, Topic
  `barcode-scan`, HA-Tag-URL-Auswertung aktiv. Alle drei Geräte-Zielbroker gesetzt.
- Durch den Agenten keine Scanner-/Broker-Einstellungen oder Kopplungen geändert.

## Bereits nachgewiesen

- Gerät in HA .193 per MQTT-Discovery vorhanden:
  `a53a704e783a1bb129aa64934cdc27e0`, Name „2D Barcode Scanner“.
- Im Ereignisprotokoll von .112 genau ein sichtbarer Scan vom **19:27:39 MEZ**,
  mit „3× an MQTT übergeben“ und erfolgreicher Übergabe an HA, IOB und Testserver,
  jeweils Topic `barcode-scan`.
- In HA .193 passendes natives `tag_scanned`-Ereignis um
  `2026-11-22T18:27:39.570369+00:00`, Tag-ID
  `usbextender-test-035-20261122` und obige Geräte-ID. Damit HA-Tag-Pfad und
  Gerätezuordnung real nachgewiesen; keine Automation oder Entität geschaltet.

## Hardware und Grenzen der bisherigen Aufnahme

- Im Chat als USB-Tastatureingaben eingegangene Steuerzeichenfolgen sind keine
  weiteren Nachweise für Empfang am Raspi oder per MQTT.
- Im Chat beobachteter Barcode `012345678905` weicht um eine führende Null vom
  gedruckten EAN-Testwert `0012345678905` ab. Ursache noch nicht abschließend
  nachgewiesen; keine automatische Ergänzung oder Softwareänderung vorgenommen.
- Bei der anschließenden .112-Prüfung Scanner offline, gespeicherte Einträge
  weiterhin vorhanden. Nutzer zum erneuten Test an der bisherigen USB-Buchse
  aufgefordert; HA-Listener für neue `tag_scanned`-Ereignisse gestartet.

## Vier neue Scans auf .112 und HA .193 bestätigt

- Nutzer hat den Scanner wieder an .112 angeschlossen und die vier Testscans
  bestätigt. Aktiver Eintrag nun `1eab-0003-338427d7a8b4`, Gerätefreigabe und
  Scanner-Modus an, DE/Enter/500 ms, Topic **`barcodescanner`**, alle drei Ziele an.
  Den Topicnamen hat der Nutzer ausdrücklich bestätigt. Alter Eintrag 9731ccf58cc2
  mit Topic `barcode-scan` bleibt offline gespeichert.
- Frisch geladene Webansicht bestätigt den gespeicherten Stand. Keine Änderung der
  Scanner-Konfiguration durch den Agenten: Der Versuch einer vorhandenen
  Gerätezuordnung wurde von der UI wegen einer als ungespeichert markierten
  Zielauswahl abgewiesen, nichts übernommen/gespeichert. Den lokalen Entwurf
  verworfen und die neu geladene, gespeicherte Sitzung beibehalten.

| Zeit (MEZ) | Physischer Code | In HA empfangene Tag-ID |
| --- | --- | --- |
| 20:15:45.086 | Barcode, erster Scan | `012345678905` |
| 20:15:47.973 | Barcode, Wiederholung | `012345678905` |
| 20:15:50.346 | Text-QR | `USBEXT-QR-035-TEST` |
| 20:15:52.157 | HA-Tag-QR | `usbextender-test-035-20261122` |

- Alle vier in .112 als BARCODE_SCAN protokolliert, jeweils drei erfolgreiche
  MQTT-Übergaben auf `barcodescanner`. In HA vier getrennte native `tag_scanned`-
  Ereignisse mit Geräte-ID `7508d44ffa66e98f8bdeaafed29ed27b` gelesen.
- Damit Wiederholung identischer Codes, QR-Text, URL-zu-Tag-ID und native Discovery
  mit realem Aplic-Scanner nachgewiesen. Keine HA-Aktion ausgeführt. Temporären
  HA-Listener nach dem Ablesen beendet.
- Nutzer-Screenshot bestätigt aktuellen Empfang auch in ioBroker unter
  `barcodescanner`; älterer Datenpunkt `barcode-scan` ebenfalls noch vorhanden.
- Gedruckter Test-EAN mit zusätzlicher führender Null und die empfangene zwölfstellige
  Ausgabe passen zur UPC-A/EAN-13-Darstellung. Keine pauschale Ergänzung von Nullen
  im Programm. Hintergrund: [GS1 General Specifications](https://ref.gs1.org/standards/genspecs/),
  Abschnitt UPC-A: Darstellung mit impliziter führender Null als 13 Stellen möglich.

## Abschlussprüfung und Einschränkung

- Abschließenden reinen Prüfblock durch Nutzer ausgeführt und Terminalausgabe
  gelesen: **Version 0.1.35, Status aktuell, Fehler `{}`; USB-/MQTT- und Webdienst
  active/running, jeweils NRestarts=0**.
- Begleitmanifest und ursprüngliches Sicherungsarchiv fehlen am gespeicherten
  Pfad. Der direkte Archivvergleich meldet
  `SICHERUNGSARCHIV NICHT MEHR VORHANDEN`. Daher kein abschließender Hashnachweis
  für unveränderte Metadaten möglich. Die vor Beginn erfolgreich geprüfte Sicherung
  ist durch die damalige Terminalausgabe belegt; ihr späterer Verbleib ist ungeklärt.
- Keine Server-Einstellungen oder Kopplungen durch den Agenten geändert.
  Gespeicherte Einträge in der Webansicht weiter vorhanden. Das ist kein Ersatz
  für den nicht mehr möglichen binären Vorher-/Nachher-Vergleich.

## Verbleibende Punkte

- Bei verfügbarer Original-Sicherung kann der Metadatenvergleich nachgeholt werden.
- Der Prüfablauf selbst änderte keinen Softwarestand. Anschließend wurde die
  Veröffentlichung von 0.1.35 mit ZIP und mehrsprachiger Dokumentation beauftragt.
