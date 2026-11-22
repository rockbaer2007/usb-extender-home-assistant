# Gamepad 0.1.34 – lokale Prüfung vom 22.11.2026

## Umfang und Sicherung

Vor der Änderung Quellstand einschließlich vorhandener uncommitteter Änderungen
gesichert: `M:\repos-backups\usb-extender-before-034-20261122-180230.zip`, CRC geprüft.
Einstellungen und Kopplungen des Pi wurden nicht geöffnet oder verändert.
Keine Installation auf .112, keine Veröffentlichung und kein MQTT-Verkehr zu
externen Brokern während dieser Umsetzung.

Das Profil basiert auf der getrennten physischen Messung
[DragonRise 0079:0006](gamepad-0079-0006-20261122.md). Die neue Implementierung
selbst wurde ausschließlich lokal geprüft.

## Ergebnisse

- **230 Python-Tests erfolgreich**, `python -m unittest discover -v`, 99,849 s.
  Enthalten sind sechs neue Gamepad-Prüfungen und die bestehenden T650-, Mobile-,
  Icon-, MQTT-, Speicher- und Sicherheitsprüfungen.
- Endpunkte 0/255 und Mitte 128 ergeben 0/100/50 auf allen vier Achsen. Totzone
  15, Begrenzung außerhalb des Bereichs, identische Werte, Senderatenbegrenzung,
  gepufferter letzter Wert, SYN_DROPPED und Abschalten geprüft. ABS_Z ohne Ausgabe.
- Linux-Eingabeweg mit simuliertem evdev: nur passender USB-Typ + Opt-in,
  ABS_X/ABS_Y/ABS_RX/ABS_RZ, unveränderte BTN_BASE-Press/Release-Verarbeitung.
- Temporäre Konfiguration: Topics nach Speichern/Laden stabil, benutzerdefiniertes
  Topic nach Aus-/Einschalten erhalten; ungültige Profile, Raten, Achsen, Topics und
  doppelte Zahlen-Topics werden zurückgewiesen.
- Drei echte MQTT-Testserver ausschließlich auf 127.0.0.1: identische Zahlenwerte,
  vier HA-Discovery-Sensoren mit eindeutigen IDs am selben Gerät, Discovery am
  zweiten Broker aus. Alle sechs Schulter-/Stick-Klick-Tasten mit Press/Release an
  allen drei Zielen. Keine analoge Ausgabe während Anlernen, Config-Datei unverändert.
  Discovery-Löschung beim Abschalten, Zielauswahl und Offline-Broker geprüft.
- **Elf JavaScript-/DOM-Prüfprogramme erfolgreich**. Neue Gamepad-Prüfung deckt
  Opt-in, vier Achsen, Namen ohne ID-Wechsel, Senderate, Topic, Speichern, Erhalt
  einer vorhandenen Kopplung, Einzelabschaltung und Live-Werte ab. Andere Geräte
  erhalten das spezifische Gamepad-Profil nicht.
- Lokale Webansicht mit Headless Edge bei **1280 und 390 px**: Aktivierung als
  Vorschau, Speichern und Live-Wert 75, keine horizontalen Überläufe oder Browserfehler.
  Desktop-/Mobilbilder visuell geprüft. Touchpad-Optionen werden beim erkannten
  Gamepad nicht angeboten; deren vorhandene Konfiguration bleibt erhalten.
- JavaScript-Syntax und `git diff --check` erfolgreich. Python-Wheel für 0.1.34
  erfolgreich mit isolierter Build-Umgebung erstellt.

## Grenzen

Kein echter Gamepad-/Home-Assistant-Test dieser Version. Die Sensoranmeldungen sind
als MQTT-Discovery-Nachrichten geprüft, nicht durch einen neuen HA-Livetest.
Linux-Installer und systemd wurden in diesem Windows-Lokallauf nicht ausgeführt.
L2/R2 bleiben digitale Tasten. ABS_Z wird ignoriert; keine neue Steuerkreuzfunktion
und keine Zusage für andere Gamepads. Praxisprüfung steht in der Roadmap.

## Paket

`M:\icons\USB-Extender-Home-Assistant-0.1.34-Raspi4.zip` enthält Quellen,
Dokumentation, Tests und Installer. Keine Benutzerkonfiguration, Statusdatei oder
virtuelle Umgebung. CRC, enthaltene SHA256SUMS und Versionsgleichheit werden nach
dem Erstellen lokal geprüft. Externe Prüfsumme: gleichnamige `.zip.sha256`-Datei.
