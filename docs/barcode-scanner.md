# Barcode-/QR-Scanner ab 0.1.35

## Einrichtung

Unterstützt werden Scanner, die sich unter Linux als **USB-HID-Tastatur** melden.
Der Scanner decodiert Barcode/QR selbst. Der USB Extender setzt seine Zeichen zu
einem Scan zusammen; eine Bildauswertung ist nicht erforderlich. Serielle Scanner
und herstellerspezifische USB-Protokolle sind noch nicht enthalten.

1. Scanner anschließen und unter **USB / Virtuelle Geräte** für Eingaben freigeben.
2. **Barcode-/QR-Scanner · USB-Tastatur** öffnen und **Als Barcode-/QR-Scanner
   verwenden** einschalten. Standardmäßig ist die Funktion aus.
3. Im Scanner per Herstelleranleitung **USB-Tastaturmodus**, passendes **DE- oder
   US-Layout**, keinen Steuerzeichen-Präfix und vorzugsweise **Enter** als Abschluss
   einstellen. In der Weboberfläche dasselbe Layout und Abschlusszeichen wählen.
4. Geräte-Zielbroker wählen. Für HA beim betreffenden MQTT-Broker Discovery
   einschalten; für ioBroker kann Discovery aus bleiben.
5. Speichern, anschließend scannen. Kein Tasten-Anlernen erforderlich. Der zuletzt
   empfangene Rohtext erscheint im Scanner-Bereich und in den letzten Ereignissen.

Ein leeres Topic wird beim Speichern aus dem Gerätenamen erzeugt, zum Beispiel
`aplic-scanner-scanner/tag_scanned`. Eigene und bereits gespeicherte Topics bleiben
erhalten. Es gelten dieselben Geräte-Zielbroker wie für die bisherigen Eingaben.

## Scan-Grenzen und Zeichen

Enter und Tab schließen einen Scan ab. Wiederholte Abschlusszeichen erzeugen keine
leeren Scans. Bei diesen beiden Betriebsarten verwirft die eingestellte Pause
unvollständige Eingaben einschließlich eines später eintreffenden Rests bis zum
nächsten Abschlusszeichen. Alternativ beendet **Scanpause** einen Scan nach der
eingestellten Zeichenpause (100–3000 ms, Standard 500 ms). Diese Variante benötigt
einen Scanner ohne angehängte Enter-/Tab-Zeichen.

Druckbare DE-/US-Zeichen einschließlich Shift, Caps Lock und deutscher AltGr-Zeichen
werden ausgewertet. Führende Nullen bleiben erhalten, der Code bleibt Text.
Maximal 4096 UTF-8-Bytes je Scan. Unbekannte Tasten, nicht unterstützte
Steuersequenzen und zu lange Scans werden bis zum nächsten Abschluss verworfen;
abgeschnittene Codes werden nicht gesendet. ESC verwirft, Backspace entfernt das
letzte Zeichen. Tastenwiederholungen zählen nicht als zusätzliche Zeichen.

Keine Zusage für beliebige Unicode-Eingabeverfahren, tote Tastenfolgen, GS1-
Steuerzeichen/FNC1 oder STX-/ETX-Rahmung. Den Scanner entsprechend konfigurieren.
Der erkannte Symbologietyp (EAN/QR/etc.) wird im reinen Tastaturmodus nicht automatisch
mitgeliefert. Nach Trennung oder relevanten Einstellungsänderungen wird der
unvollständige Scan verworfen.

## MQTT und native HA-Tags

Jeder vollständige Scan sendet eine MQTT-Nachricht, **reiner Text, nicht retained**.
Auch derselbe Code löst bei jedem Scan erneut aus. Keine spätere Wiedergabe von
Scans an Offline-Broker. Inhalte werden weder geöffnet noch ausgeführt.

Bei eingeschalteter Discovery meldet sich das Gerät über
`homeassistant/tag/ugso_<hub_id>_<device_id>/config` als nativer **MQTT tag scanner**
an. Die Anmeldung enthält `topic` und die bestehende Gerätezuordnung. Beim Abschalten
oder Entfernen wird sie zurückgenommen, nach MQTT-/HA-Neustart erneut abgeglichen.
Das ist ein Tag-Scanner, keine zusätzlich erfundene Sensor-Entität.

**HA-Tag-URLs als Tag-ID senden** ist standardmäßig eingeschaltet. Aus
`https://www.home-assistant.io/tag/werkstattlicht` wird `werkstattlicht`.
Andere Codes bleiben unverändert. Abschalten sendet immer den vollständigen Text.
Die Webvorschau zeigt weiterhin den Rohtext.

In HA unter **Einstellungen → Tags** den erfassten Tag benennen und eine Automation
anlegen, beispielsweise zum Umschalten einer Lampe. Die Aktion wird in HA festgelegt;
ein QR-Code führt nicht von sich aus eine Aktion aus. Das gleiche HA-Tag-QR-Format
lässt sich auch mit der Companion-App verwenden.

Referenzen: [MQTT tag scanner](https://www.home-assistant.io/integrations/tag.mqtt/),
[Tag-Auslöser](https://www.home-assistant.io/triggers/tag/),
[Companion-QR-Tags](https://companion.home-assistant.io/docs/integrations/universal-links/).

## Erhalt bisheriger Einstellungen

Der Scanner-Modus pausiert die normalen Tasten-, Touchpad- und Gamepad-Aktionen
dieses Geräts einschließlich ihrer Discovery-Anmeldungen. Die Belegungen werden
nicht gelöscht und stehen nach Abschalten wieder zur Verfügung. Andere Geräte,
Broker-Zugangsdaten, Icons und Mobile-Kopplungen bleiben erhalten.

Es gibt keinen eigenen dauerhaften Scan-Verlauf. Wie andere Eingaben können die
letzten Scans in der regelmäßig geschriebenen `status.json`-Momentaufnahme stehen;
nach Neustart wird die Ereignisliste neu aufgebaut.

## Prüfstand

Lokal mit synthetischen USB-Tastaturereignissen, drei Loopback-MQTT-Brokern und
Desktop-/Mobil-Webansicht geprüft. Anschließend am echten Aplic-Scanner auf .112
zwei identische Barcodes, Text-QR und HA-Tag-QR an drei Broker übergeben und in HA
.193 als vier getrennte native Ereignisse nachgewiesen. ioBroker-Empfang durch
Nutzerbild bestätigt. Aktuelles Topic dort: `barcodescanner`.

Der gedruckte Test-EAN wird als zwölfstellige UPC-A-
Darstellung ausgegeben. Keine blinde Ergänzung von Nullen im Programm.
Abschlussdienststatus fehlerfrei. Metadatenvergleich mangels ursprünglichem
Sicherungsarchiv nicht möglich; eine HA-Automation wurde nicht ausgeführt.
Version 0.1.35 wird mit Installations-ZIP und SHA256-Prüfsumme veröffentlicht.
[Lokale Tests](tests/scanner-0.1.35-20261122.md) ·
[Praxistest](tests/scanner-live-0.1.35-20261122.md).
