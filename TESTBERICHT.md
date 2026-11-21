# Prüfung 0.1.0

Datum: 21. November 2026. Lokale Windows-Prüfung mit Python 3.13.14.

## Automatisierte Prüfung

`python -m unittest discover -v`

Der letzte Gesamtlauf umfasst **26 Prüfungen**, einschließlich identischer
Spiegelung zu mehreren Brokern.

- Konfigurationsversion und genau drei Brokerplätze; Passwort-Hash,
  ausgeblendete Zugangsdaten und Erhalt gespeicherter MQTT-Passwörter.
- Atomare Speicherung und Begrenzung auf zehn Konfigurationssicherungen.
- Zielvorrang Belegung → Gerät → Standard; stabile USB-Identität und Port-Fallback.
- Zuordnung zweier Stream Decks ohne USB-Seriennummer über libusb-Pfade.
- Drei echte Paho-MQTT-Clients über lokale TCP-Verbindungen zu isolierten
  MQTT-3.1.1-Testgegenstellen. Ereignisse erreichen alle drei Ziele ohne retained.
- Festes Sende-Topic an allen drei Brokern: Topic und Payload sind bytegleich.
- Ausfall einer Gegenstelle beeinträchtigt die anderen zwei nicht.
- Fehlerhafte CA-Datei eines Brokers blockiert die übrigen Verbindungen nicht.
- Zustandsabonnement am ausgewählten Empfangsbroker und Wiederholung der
  Discovery nach Home-Assistant-Birth-Nachricht.
- Retained-Discovery-Löschung für eine entfernte Belegung bei verbundenen Brokern.
- Ordnerimport, normalisierte PNG-Ausgabe und Vermeidung identischer Bibliothekseinträge.
- `.streamDeckIconPack`-Testarchiv in offizieller Verzeichnisstruktur mit Namen,
  Tags, Autor und Lizenztext; gefährliche Archivpfade und aktive/externe SVG-Inhalte
  werden abgelehnt. GIF verwendet das erste Bild.
- Native Stream-Deck-JPEG-Aufbereitung mit Icon, Text und Helligkeit an einem
  Testobjekt; ungültige Tastennummer erzeugt keinen Bildauftrag.
- HTTP-Anmeldung, Zugriffsschutz, Fremdursprungs-Abweisung, Konfigurationsspeicherung,
  Iconupload und Sitzungsbeendigung.
- Getrennte Web-/USB-MQTT-Prozesse: Webprozess beendet, dessen TCP-Port geschlossen,
  Kernprozess schreibt weiterhin Status. Kernprozess neu gestartet, gespeicherte
  Gerätezuordnung bleibt erhalten.

Die MQTT-Gegenstellen sind eigene lokale Protokoll-Testserver, kein bestätigter
Test mit Mosquitto oder einer echten Home-Assistant-Instanz.

## Chrome

Lokale Oberfläche `http://127.0.0.1:8098` mit ausdrücklich künstlichen Beispieldaten:

- Anmeldung und vollständige Darstellung der drei MQTT-Karten.
- Tastenbelegung geändert, gespeichert, nach Neuladen vorhanden.
- Dieselbe Belegung erneut geändert und zweimal gespeichert; anschließend
  Speicherzustand wieder grau/deaktiviert.
- Iconbibliothek mit Vorschaubildern, Namen, Sammlung sowie Lizenz-/ID-Details.
- Keine beobachteten Anwendungs-JavaScriptfehler; Browsererweiterungen meldeten
  eigene, nicht aus dieser Anwendung stammende Fehler.

![MQTT-Konfiguration mit lokalen Beispieldaten](docs/screenshots/mqtt-demo.jpg)

![Iconbibliothek mit eigenen Beispielbildern](docs/screenshots/iconbibliothek-demo.jpg)

## Paket und Installer

- Bash-Syntaxprüfung für Installer und CLI-Starter.
- JavaScript-Syntaxprüfung, Python-Kompilierung und Python-Paketinstallation.
- ZIP-Prüfung mit SHA-256-Dateiliste, LF-Zeilenenden und Linux-Ausführungsrechten.
- Keine lokalen Konfigurationen, Passwörter, venv, Git-Daten oder erworbenen Iconpacks
  im Auslieferungspaket.

## Noch nicht bestätigt

- Ausführung des Installers auf Raspberry Pi OS und tatsächliche ARM-Abhängigkeiten.
- Physische USB-/Stream-Deck-Geräte, Hotplug und Stromversorgung am Pi.
- HA-Geräteauslöser und Anzeigezustände mit der tatsächlichen HA-Installation.
- Alle Varianten realer Elgato-Marketplace-Iconpacks sowie Animationen.

Eine Linux-CI ist im privaten Repository vorgesehen; ihr Ergebnis wird separat
festgehalten und ersetzt keinen Raspberry-Pi-Hardwaretest.
