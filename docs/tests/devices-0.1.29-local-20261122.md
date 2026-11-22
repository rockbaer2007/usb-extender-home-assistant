# 0.1.29 – lokale Geräte- und Gestenprüfung

Stand: 22. November 2026. Windows, Python 3.13, Node und Chrome headless.
Alle Server/Broker-Prüfungen laufen isoliert auf Loopback mit temporären Daten.
Kein Zugriff auf .112, keine Änderung vorhandener Geräteeinstellungen.

## Sicherung

Vor Änderungen wurde der Quellstand vollständig als ZIP gesichert und auf CRC
geprüft: `M:\repos\_backups\ugso-usb-hub\before-device-gesture-update-20261122-132149.zip`.
Geräteaktionen sichern zusätzlich ihre betroffenen Metadaten vor dem Schreiben.

## Neue Prüfungen

- Alle fünf Schrittintervalle und unveränderter Standard 1. Getrennte Tasten-
  und Gerätezähler, kein Zählen beim Anlernen, übersprungene Zyklen ohne MQTT.
  Lautstärke-Haltewiederholung stoppt beim Loslassen und bei Trennung.
- Serienkennung über USB-Portwechsel, Legacy-Erkennung am bisherigen Port,
  doppelte Seriennummern ohne willkürliche Zuordnung. Manuelle Zuordnung erhält
  Belegungen und Zugangsdaten über erneutes Laden der Konfiguration.
- Bestätigtes Entfernen mit Metadatensicherung; gemeinsame Icons, andere Geräte
  und Mobile-Vertrauen erhalten. Fehler vor und nach Konfigurationsersetzung
  stellen Konfiguration und Schaltzustände vollständig wieder her.
- Zwei echte verschlüsselte lokale Mobile-Verbindungen: Entfernen eines Decks
  schließt nur dessen Sitzung. Widerrufen eines Clients erhält dessen Deckdaten.
- HTTP-Geräteaktion erfordert Anmeldung. Vorhandene globale CSRF-Prüfung bleibt.
- Synthetische Linux-Type-B-Ereignisse: Tippen/Halten, mechanische Klicks ohne
  doppelte virtuelle Aktion, Scrollen in vier Richtungen, Pinch hinein/heraus,
  Dreifingerwischen einschließlich einzeln abgehobener Finger, SYN_DROPPED ohne
  Phantomaktion. Linux-Adapter mit simuliertem evdev: Opt-in und Abziehbereinigung.
- DOM: alphabetische, geschlossene Gerätegruppen; nur eine Gruppe/eine Taste
  offen; Einzelbelegungen in gleicher Gruppe; Schrittfilter speichern;
  Entfernen abbrechen/bestätigen und übrige Daten behalten.
- Chrome: Aufklappen, Schrittfilter und Gerätezuordnung bedienbar; keine
  JavaScript-Fehler; Geräteansicht bei 390 Pixel Breite ohne Seitenüberlauf.

## Grenzen

Ein vollständiger Lauf zeigte einen einmaligen Windows-PermissionError beim
Lesen einer gleichzeitig ersetzten temporären Statusdatei im bestehenden
Mobile-Webtest. Der wiederholte Gesamtlauf bestand mit 186 Tests. Nach der
abschließenden Änderung zur nicht blockierenden Mobile-Trennung bestanden alle
35 Mobile-Tests erneut; die 16 Geräte-/Gestenprüfungen wurden ebenfalls erneut
erfolgreich ausgeführt. Neun Node-/DOM-Prüfungen und der Chrome-Test bestanden.
Python-Wheel, Python-/JavaScript-Syntax, Shell-Syntax und `git diff --check`
erfolgreich. Kein neuer Linux-Installer-Praxistest auf einem Pi.

Kein echter T650-Test: Nutzer hat das Gerät noch nicht geladen und zunächst
lokale Tests gewünscht. Linux-Sysfs-/HID++-Daten und Gestenschwellen müssen auf
der tatsächlichen Hardware geprüft werden. Keine pauschale Zusage für jedes
Touchpad. 0.1.29 nicht auf einem Raspberry Pi installiert oder veröffentlicht.
Der bestandene reale 15-Minuten-Test gehört ausschließlich zu 0.1.28.
