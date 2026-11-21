# Aktueller Stand

## USB Extender für Home Assistant 0.1.0

Stand: 21. November 2026. Eigenständiges privates Repository, keine Änderungen
an ATLAS, HA Logic Studio Pro, VFRegist oder bestehenden Home-Assistant-Systemen.

Implementiert: USB-Inventar, freigegebene evdev-Eingaben, Stream-Deck-Adapter,
drei MQTT-Broker, Belegungen, Iconbibliothek, getrennte Weboberfläche, CLI und
Installer einschließlich Abhängigkeitsprüfung und sichtbarer Schrittanzeige.

Lokal wurden automatisierte Prüfungen und Chrome-Prüfungen mit Beispieldaten
durchgeführt. [Testbericht](TESTBERICHT.md). Das ZIP enthält Quellcode, Installer,
systemd-Dienste, udev-Regeln und Anleitung. Abhängigkeiten werden bei der
Installation aus den Paketquellen geladen.

Noch kein Test auf einem physischen Raspi 4 und noch kein USB-Gerätetest.
Docker ist auf diesem PC nicht gestartet; WSL kann hier nicht verwendet werden.
Linux-/ARM-Installation und die konkrete Hardware bleiben zu bestätigen.

Der nächste praktische Schritt steht in [ROADMAP.md](ROADMAP.md).
