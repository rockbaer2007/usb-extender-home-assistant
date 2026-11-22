# Scanner 0.1.35 – lokale Prüfung vom 22.11.2026

## Sicherung und Umfang

Quellen einschließlich aller bisherigen lokalen Änderungen vor Beginn gesichert:
`M:\repos-backups\usb-extender-before-035-20261122-185054.zip` (CRC geprüft).
Keine Verbindung zum Pi, zu ioBroker oder zu einem HA-System hergestellt.
Einstellungen und Mobile-Kopplungen dort bleiben unverändert. Nichts veröffentlicht.

## Lokale Nachweise

- **238 Python-Tests erfolgreich**, vollständiger Lauf 102,196 s. Darunter acht
  neue Scanner-Prüfungen sowie alle bisherigen Gamepad-, T650-, Mobile-, Speicher-,
  Icon- und MQTT-Prüfungen. Nach Ergänzung der Prüfung für verspätete Scan-Reste
  erneut **26 gezielte Scanner-/Gamepad-/Touchpad-/MQTT-Prüfungen erfolgreich**.
- Decoder: druckbare DE/US-Zeichen, Shift, AltGr, Caps Lock, führende Nullen,
  URLs, zweimal derselbe Code, Enter, Tab, Pausenabschluss und Tastenwiederholungen.
- Unvollständige Scans werden verworfen; im Enter-/Tab-Modus bleibt auch ein
  verspäteter Rest bis zum Abschluss ungültig. Unbekannte Tasten, Ctrl-Sequenzen,
  Überlänge, ESC, Backspace, Konfigurationswechsel und SYN_DROPPED behandelt.
- Simulierter Linux-evdev-Pfad: Scannerzeichen werden zusammengefasst, keine
  Einzel-Tastenaktionen. Trennung entfernt Puffer; Rückkehr in normalen Modus
  stellt die unveränderten Tasten-IDs wieder bereit.
- Konfigurations-Rundlauf: eigenes Topic nach Aus-/Einschalten erhalten, automatische
  Topics, Validierung von Optionen, Erhalt vorhandener Belegungen, anderer Geräte
  und Passwort-Hash. Scanner-Modus braucht kein Tasten-Anlernen.
- Drei MQTT-Testserver **ausschließlich auf 127.0.0.1**: Decoder → Core → Broker,
  gleiche Scans zweimal als getrennte, nicht-retained Textnachrichten, führende
  Nullen und HA-Tag-ID aus URL. Identische Inhalte an drei Zielen.
- Native `homeassistant/tag/.../config`-Anmeldung mit Topic und Gerätezuordnung;
  Discovery an Broker 2 aus. Abschalten entfernt die Anmeldung, erneuter Abgleich
  verwendet denselben Discovery-Pfad. Zielauswahl und Offline-Broker geprüft.
  Keine Ausführung von QR-Inhalten oder vorhandenen Einzel-Tastenbelegungen.
- **Zwölf JavaScript-/DOM-Prüfprogramme erfolgreich**, darunter neue Scanner-
  Bedienprüfung: Opt-in, Layout/Abschluss/Pause/Topic, Speichern, Erhalt einer
  Kopplung und bestehender Belegung, Abschalten und sichere Rohtextanzeige ohne HTML.
- Headless Edge lokal bei **1280 und 390 px**: Vorschau, Speichern, letzter Scan,
  keine horizontalen Überläufe oder Browserfehler. Screenshots visuell geprüft.
- JavaScript-Syntax, `git diff --check` und isolierter Python-Wheel-Build erfolgreich.

## Grenzen und Paket

Discovery-Nachrichten sind gegen die dokumentierte MQTT-Tag-Struktur geprüft;
kein echter HA-Automationslauf. Der spätere [Aplic-Praxistest auf dem Pi](scanner-live-0.1.35-20261122.md)
bestätigt vier echte Scans und native HA-Tag-Ereignisse separat.
Serielle Protokolle, allgemeine Unicode-Eingabeverfahren, GS1-Steuerzeichen und
STX/ETX sind nicht enthalten. Linux-Installer/systemd nicht unter Windows ausgeführt.

ZIP: `M:\icons\USB-Extender-Home-Assistant-0.1.35-Raspi4.zip` mit Quellen,
Installer, Tests und Dokumentation, ohne Benutzerkonfiguration oder virtuelle
Umgebung. CRC, interne SHA256SUMS, externe Prüfsumme und Versionsgleichheit werden
nach Erstellung geprüft; Prüfsumme neben dem ZIP als `.zip.sha256`.
