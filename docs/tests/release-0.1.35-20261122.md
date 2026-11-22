# Freigabeprüfung 0.1.35 – 22. November 2026

- Vollständige lokale Python-Suite: **238 Tests erfolgreich**, 100,405 Sekunden.
- **12 Node-/DOM-Prüfprogramme erfolgreich**: Tastenliste, Archiv, Geräte,
  Flächenregler, Gamepad, Scanner, Stream Deck, Seiten, Mobile und Iconauswahl.
- Die Python-Suite enthält echte lokale MQTT-Loopback-Tests; temporäre
  Konfigurationen und synthetische Eingaben ersetzen keine weiteren Hardwaretests.
- Scanner-Praxisnachweis: [Aplic 305045](scanner-live-0.1.35-20261122.md).
  Vier physische Scans, native HA-Tag-Ereignisse, drei MQTT-Ziele und bestätigter
  ioBroker-Empfang. Abschlussstatus beider Dienste ohne Fehler oder Neustarts.
- Vorhandene Einschränkungen des Metadatenvergleichs bleiben im Praxisbericht
  ausdrücklich dokumentiert. Keine zusätzlichen Änderungen auf dem Raspberry Pi
  für die Veröffentlichung.
- Installations-ZIP: CRC, interne SHA256-Dateiliste, externe SHA256-Prüfsumme und
  Versionsangaben werden vor dem Hochladen geprüft. Keine lokalen Einstellungen,
  Zugangsdaten, virtuelle Umgebung oder Git-Verzeichnisse im Paket.
- Linux-Installerprüfung erfolgt zusätzlich im vorhandenen GitHub-CI-Workflow.
  Auf diesem Windows-PC wird kein Linux/systemd-Dienst installiert.
