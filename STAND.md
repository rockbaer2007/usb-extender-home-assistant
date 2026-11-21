# Aktueller Stand

## USB Extender für Home Assistant 0.1.1 in Prüfung

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

Noch kein Test auf einem physischen Raspi 4 und noch kein USB-Gerätetest.
Docker ist auf diesem PC nicht gestartet; WSL kann hier nicht verwendet werden.
Die ARM-Installation auf Raspberry Pi OS und die konkrete Hardware bleiben zu bestätigen.

Der nächste praktische Schritt steht in [ROADMAP.md](ROADMAP.md).
