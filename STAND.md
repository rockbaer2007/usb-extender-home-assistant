# Aktueller Stand

## USB Extender für Home Assistant 0.1.2 in Prüfung

- Ursache des fehlenden Versands im Browser gefunden: Belegung `key:tab`,
  tatsächliche Eingabe `KEY_TAB`. Auf dem Raspi auf `KEY_TAB` geändert und gespeichert;
  die vorige Konfiguration wurde automatisch gesichert.
- Discovery im vorhandenen Brokerplatz **IOB** ausgeschaltet, HA unverändert.
- Nach drei physischen Tab-Tastendrücken zeigte der offene HA-MQTT-Explorer
  genau drei Nachrichten unter `ugso/usbhub/1/event/...`, Payload mit
  `control: KEY_TAB`, `event_type: press`, `value: 1`.
- 0.1.2 normalisiert Tastenkennungen, bietet Discovery ausdrücklich als Aus/HA-Auswahl,
  räumt bekannte eigene Discovery-Ankündigungen auf und zeigt MQTT-Ziele sowie Sendestatus.
- 34 lokale automatisierte Prüfungen erfolgreich. Vollständige Linux-CI und
  Installation des neuen Pakets auf dem Raspi stehen noch aus.

Auf dem Raspi ist noch 0.1.0 mit den Live-Korrekturen aktiv. Der Empfang am
ioBroker-Broker selbst wurde nicht separat beobachtet; sein Brokerplatz ist online.

## USB Extender für Home Assistant 0.1.1

Stand: 21. November 2026. Eigenständiges privates Repository, keine Änderungen
an ATLAS, HA Logic Studio Pro, VFRegist oder bestehenden Home-Assistant-Systemen.

Praxisdiagnose auf dem Raspi: HCT USB Entry Keyboard und weitere USB-Eingabegeräte
werden erkannt; MQTT-Broker 1 ist online. Auf den Eingabekanälen fehlen Leserechte
für das Dienstkonto (`Permission denied`). Der Kernprozess läuft weiter.

Korrektur 0.1.1: Standardgruppe `input` im Installer und in systemd, Prüfung der
realen Leserechte und Dienststatus ohne Abhängigkeit von der PC-Uhr.
Der Live-Nachtest nach der Berechtigungskorrektur ist erfolgreich: HCT-Tastatur
liefert `KEY_LEFTCTRL` mit press/release; der Volumeregler liefert Lautstärke− und
Stumm. MQTT ist weiterhin online. Auf dem Raspi läuft 0.1.0 mit ergänzter Eingabegruppe;
das vollständige Update auf 0.1.1 ist noch einzuspielen.

Zusätzlich wird der beim Live-Test sichtbare evdev-Alias der Stummtaste in 0.1.1
zu `KEY_MUTE` normalisiert, auch für bereits angelegte Alias-Zuordnungen.

28 lokale Prüfungen und die Linux-CI einschließlich frischer Installation,
tatsächlichem Lesetest mit der Gruppe `input` und Dienststart sind erfolgreich:
[CI-Lauf für 9623d8b](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/44892114882).

## Bestätigte Basis 0.1.0

Implementiert: USB-Inventar, freigegebene evdev-Eingaben, Stream-Deck-Adapter,
drei MQTT-Broker, Belegungen, Iconbibliothek, getrennte Weboberfläche, CLI und
Installer einschließlich Abhängigkeitsprüfung und sichtbarer Schrittanzeige.

Lokal wurden 26 automatisierte Prüfungen und Chrome-Prüfungen mit Beispieldaten
durchgeführt. Die Linux-CI einschließlich frischer Installation,
systemd-Dienststart, Webstart/-stopp und Kernprozess-Neustart ist erfolgreich.
Geprüfter Quellcode: `2432764`, [CI-Lauf](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/44889742734).
[Testbericht](TESTBERICHT.md). Das ZIP enthält Quellcode, Installer,
systemd-Dienste, udev-Regeln und Anleitung. Abhängigkeiten werden bei der
Installation aus den Paketquellen geladen.

Der inzwischen erfolgreiche physische Eingabetest ist oben festgehalten.
Offen bleiben das vollständige Update auf 0.1.1 am Raspi und der Test eines
physischen Stream Decks.

Der nächste praktische Schritt steht in [ROADMAP.md](ROADMAP.md).
