# Aktueller Stand

## 0.1.38 – Verweis auf USB Extender Cards

- Eigenständiges gemeinsames Kartenpaket umgesetzt und im Systembereich verlinkt.
  Separate HA-Installation; keine Dashboardänderung durch den Pi-Installer.
- Vor Änderung gesichert: `M:\repos-backups\usb-extender-before-038-20261123-150356.zip`.
  Vorherige Geräte-/MQTT-Einstellungen, Icons und Kopplungen erhalten.
- Enthält MQTT-Systemsteuerung 0.1.37. Linux-CI erfolgreich: 250 Python-Tests,
  14 Node-/DOM-Prüfprogramme, Installation und echter unprivilegierter Socketzugriff
  mit Start/Stop, enable/disable, ungültiger Befehlsablehnung und Zustandswiederherstellung.
  [CI-Nachweis](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/45189963469).
  Kein Update auf dem echten Raspberry Pi; dessen Praxistest bleibt offen.

## 0.1.37 – lokale MQTT-Systemsteuerung, noch nicht veröffentlicht

- Web Start/Stop, Autostart enable/disable und Backup per freigegebenem Broker.
  Vier getrennte Rückmeldungen, fünf native HA-Discovery-Entitäten, HTTP-Prüfung.
- Sicherung vorher: `M:\repos-backups\usb-extender-before-037-20261123-143230.zip`,
  CRC geprüft. Bestehende Einstellungen und Kopplungen werden nicht migriert/gelöscht.
- Gemeinsames Kartenpaket in ROADMAP und als geplanter Hinweis im Systembereich.
- Lokale Regression: 250 Python-Tests, 14 Node-/DOM-Prüfprogramme, zusätzlicher
  MQTT-/HTTP-/Backup-Test gegen zwei Loopback-Broker. Desktop/Mobil ohne Überlauf.
- Echter Linux/systemd- und Raspi-Test steht aus; entsprechender CI-Smoke-Test ist
  vorbereitet. Kein Update auf .112 und keine Veröffentlichung dieser Version.

## 0.1.36 – USB-Laufwerke, System und Hidden

- Neue USB-Speicher ohne voreingestellte Haken; Bestandszuordnungen erhalten.
- Gegenseitig ausschließende Anzeigeoptionen, kompakte Zusammenfassung, jederzeit
  aufklappbar. Speicherung einschließlich Offline-Kennung; keine Laufwerksoperation.
- Quellstand vorher unter `M:\repos-backups\usb-extender-before-036-20261123-135834.zip`
  gesichert und CRC geprüft. Tests verwenden temporäre Konfigurationen und lokale
  USB-/Web-Simulationen; keine Änderung oder Installation auf dem Raspberry Pi.

## 0.1.35 – Barcode-/QR-Scanner, öffentliches Testrelease

- Release-Prüfung: 238 Python-Tests und zwölf Node-/DOM-Prüfprogramme erfolgreich.
  [Freigabeprüfung](docs/tests/release-0.1.35-20261122.md).

- Praxistest: Am 22.11.2026 um 20:15:45–52 MEZ Barcode zweimal, Text-QR und
  HA-QR auf .112 gescannt; alle vier auf Topic `barcodescanner` an drei Broker
  übergeben und in HA .193 als getrennte `tag_scanned`-Ereignisse nachgewiesen.
  ioBroker-Empfang durch Nutzerbild bestätigt. Abschluss: beide Dienste laufen,
  NRestarts jeweils 0, keine gemeldeten Fehler. Metadatenvergleich nicht möglich:
  ursprünglich geprüfte Sicherung später am Pfad nicht mehr vorhanden.
  [Praxistest](docs/tests/scanner-live-0.1.35-20261122.md).

- USB-HID-Tastaturscanner mit DE/US, Scanabschluss Enter/Tab/Pause, Text-MQTT und
  nativer HA-Tag-Discovery. Optional ID aus HA-QR-URL. Pro Gerät Opt-in, eigenes
  Topic und Geräte-Zielbroker. Wiederholte gleiche Scans lösen erneut aus.
- Bestehende Tastenbelegungen pausieren im Scanner-Modus und werden nicht gelöscht.
  Einstellungen, Passwörter, andere Geräte und Mobile-Kopplungen bleiben erhalten.
- Sicherung vor Änderungen:
  `M:\repos-backups\usb-extender-before-035-20261122-185054.zip` (CRC geprüft).
- Umsetzung zunächst ausschließlich lokal, anschließend oben genannter Praxistest.
  Veröffentlichung mit ZIP, Prüfsumme und mehrsprachiger Dokumentation. [Einrichtung](docs/barcode-scanner.md) ·
  [Prüfbericht](docs/tests/scanner-0.1.35-20261122.md).

## 0.1.34 – Gamepad-Unterstützung, lokal und unveröffentlicht

- DragonRise 0079:0006: ABS_X/ABS_Y (links), ABS_RX/ABS_RZ (rechts), je 0–100
  und Mitte 50, Totzone aus dem Gerät. ABS_Z wird ignoriert. Stickausgabe zunächst
  aus; nach Aktivierung vier getrennte Topics/Sensoren und Senderate 1–30/s je Achse.
- Schultertasten und Stick-Klicks bleiben normale Tasten, Linux-IDs unverändert.
  Verständliche Namen beim neuen Anlernen; vorhandene Belegungen erhalten.
- Vor Änderungen vollständige lokale Quellsicherung:
  `M:\repos-backups\usb-extender-before-034-20261122-180230.zip` (CRC geprüft).
- Änderungen ausschließlich lokal; keine Installation, Veröffentlichung oder
  Änderung an Einstellungen/Kopplungen auf dem Pi.
- Prüfnachweis: [0.1.34](docs/tests/gamepad-0.1.34-20261122.md).

## Gamepad-Prüfung auf .112 (ohne MQTT)

- Geführter Einzeltest abgeschlossen:
  `/home/pi/install/Gamepad-Einzeltest/gamepad-test-20261122-175330/bericht.json`.
  Linker Stick Hauptachsen ABS_X/ABS_Y, rechter Stick ABS_RX/ABS_RZ (je 0–255,
  Ruhe 128). ABS_Z reagiert bei mehreren Bewegungen mit, keine eigene sichere
  Triggerzuordnung. L1=BTN_BASE, R1=BTN_BASE2, L2=BTN_TOP2, R2=BTN_PINKIE;
  Stick-Klick links=BTN_BASE5, rechts=BTN_BASE6. Schultertrigger liefern Tasten,
  keine analogen Druckwerte in diesem Test. Einstellungen unverändert,
  Dienstlaufzustand wiederhergestellt, Prüfwerkzeug ohne MQTT. Nichts veröffentlicht.

- DragonRise Inc. Generic USB Joystick, USB-ID 0079:0006. Aufnahme unter
  `/home/pi/install/Gamepad-Pruefung/gamepad-test-20261122-174236/`.
- Digital 788, Analog 3052 Ereignisse. Je zwölf Tasten angeboten, davon zehn mit
  Drücken/Loslassen erfasst; BTN_BASE3/BTN_BASE4 in beiden Phasen nicht betätigt.
- Digital beobachtet: ABS_X, ABS_Y, ABS_Z je 0–255. Analog zusätzlich ABS_RX,
  ABS_RZ je 0–255 und ABS_HAT0X/Y je −1/0/+1. Zwischenstufenzahl des Digitalmodus
  aus der Zusammenfassung nicht nachgewiesen. Physische Stick-/Schulterzuordnung
  anschließend im geführten Einzeltest ergänzt (siehe oben).
- completed/meaningful_phases/settings_unchanged/service_restored jeweils true,
  mqtt_in_probe false. Dienst nach Test wiederhergestellt, keine Einstellungen
  verändert oder Gamepad-MQTT-Anbindung erstellt. Nichts veröffentlicht.
- Details: [Prüfbericht](docs/tests/gamepad-0079-0006-20261122.md).

## 0.1.33 – fünf Regler, lokal und unveröffentlicht

- Nach Nutzerinstallation am 22.11.2026 im Browser bestätigt: .112 zeigt 0.1.33,
  gespeicherten Flächenmodus, fünf aktivierte Regler, X/Y und IOB-Ziel aktiv.
  In ioBroker .116:8081 alle fünf Werte unter mqtt.0.t650-touchpad.fader-N.value
  vorhanden: 98, 98, 85, 3, 8; identisch zu den zuletzt auf .112 angezeigten Werten.
  Keine Änderung von MQTT-/Geräteeinstellungen während dieser Prüfung.
  HA-Reglerprüfung, kontrollierter Streifenwechsel/Lock und Update-Prüfsummen offen.

- Vollständiger Arbeitsstand inklusive uncommitteter 0.1.32-Dateien vor Änderungen
  gesichert: `M:\repos-backups\usb-extender-before-033-20261122-170440.zip`, CRC geprüft.
- Umschaltung acht Richtungen / fünf senkrechte Regler. Auswahl des Reglers beim
  Aufsetzen, fest bis Abheben. Eigene Topics und HA-Sensoren; X/Y unabhängig.
- Richtungsbelegungen bleiben erhalten und pausieren im Flächenmodus, einschließlich
  ihrer Discovery-Anmeldungen und MQTT-Aktionen. Rückschalten erhält ihre IDs/Topics.
- Webansicht: Regler türkis, Richtungen goldfarben, Pausiertes grau; letzte Werte,
  Füllstände und letzter Trigger. Keine zusätzliche Netzwerkabfrage oder Bildübertragung.
- Lokale Prüfungen und Grenzen: [Prüfbericht](docs/tests/faders-0.1.33-20261122.md).
- Gesamtlauf: 217 Python-Tests in 100,549 s erfolgreich, zehn Node-/DOM-Prüfungen,
  JavaScript-Syntax und Wheel-Build erfolgreich. Desktop/Mobil 1280/390 px geprüft.
- Während der lokalen Implementierung keine Remoteänderung; Nutzer hat anschließend
  0.1.33 auf .112 installiert. Kein Push/Release und keine Doku-Veröffentlichung.

## 0.1.32 – lokaler, unveröffentlichter Teststand

- Screenshot auf .112 zeigt Web 0.1.32, aktiven Dienst und 3/3 MQTT-Broker.
- Hardwareaufnahme `t650-results-20261122-164242/report.json` mit älterem Prüfskript:
  alle acht Richtungen erkannt, 128 Slide-Aktionen und 163 X/Y-Paare, keine Tipps in
  den acht Slide-Phasen. Separater Tipptest neun Tipps. Drei Broker je 600 identische
  Nachrichten; reine X/Y-Zahlen. Einstellungen laut Skript unverändert. UP_RIGHT
  enthält zusätzlich eine UP-Aktion. Rate-Phase ohne Ereignisse, daher nicht bewertet.
- Ergänzende Auswertung auf .112 bestanden:
  `values-replay-20261122-164727.json` verwendet dieselben echten Rohdaten. Alle acht
  Richtungswerte, 147 X/Y-Paare, kein Tipp. Drei Loopback-Broker je 441 identische
  reine Zahlennachrichten, exakt passend zu den erzeugten Ereignissen. Zehn Sensoren
  an jedem Discovery-Broker, null am Broker ohne Discovery. Fünf Metadaten-Dateien
  während des Replays unverändert.
- Anschließender Live-Test auf .193 am 22.11.2026 um 16:51–16:52 bestätigt:
  acht Richtungswerte auf .112 eingeschaltet und gespeichert (automatische Sicherung
  der vorherigen Konfiguration durch save_config). Discovery legt alle acht Sensoren
  am bestehenden T650-Gerät an; X/Y waren bereits vorhanden. Nach vom Nutzer
  ausgeführten acht Bewegungen alle zehn Sensoren numerisch, mit neuen Einträgen
  in der HA-Aktivität. Letzte Werte: DOWN 2, DOWN_LEFT 7, DOWN_RIGHT 95, LEFT 2,
  RIGHT 92, UP 98, UP_LEFT 12, UP_RIGHT 95, X 2, Y 88.
- Acht Richtungswerte bleiben eingeschaltet. Vorhandene X/Y-Topics T650-X/T650-Y
  und Zielauswahl erhalten. Vollständiger Installations-Prüfsummenvergleich sowie
  neuer HA-Neustart-/Abschalttest weiterhin nicht belegt. Nichts veröffentlicht.
- `tools/install_032_checked.sh`: vollständige aktive Sicherung, Paketprüfsummen,
  Update und Vergleich der fünf Metadaten-Dateien sowie Dienststartprüfung.

- Vorherige Quelle 99d5d9f gesichert in
  `M:\repos-backups\usb-extender-before-032-20261122-160545.zip`.
- Acht unabhängig aktivierbare Richtungswerte mit eigenen MQTT-Topics sowie
  HA-Discovery für diese Werte und X/Y. Neue Richtungswerte standardmäßig aus.
- Bestehende Richtungsaktionen, X/Y-Topics, Einstellungen und Kopplungen erhalten.
- Lokale Tests mit temporären Einstellungen und drei Loopback-Brokern; Oberfläche
  bei 1280 und 390 px ohne Seitenfehler/Überlaufen geprüft. Wheel erfolgreich gebaut.
- Abschließender Gesamtlauf: 210 Python-Tests erfolgreich (96,420 s), dazu alle
  neun Node-/DOM-Prüfungen und `git diff --check` erfolgreich.
- Details und Prüfgrenzen: [Testbericht](docs/tests/slide-values-0.1.32-20261122.md).
- Keine Installation auf .112, kein Push, kein GitHub-Release und kein Doku-Deployment.

## Release 0.1.31

- Bündelt 0.1.29–0.1.31 mit ZIP/Prüfsumme, Changelog und README DE/EN.
- Freigabeprüfung: 204 lokale Python-Tests, neun Node-/DOM-Prüfungen und
  Installer-Umask-Regression bestanden; Linux-CI prüft zusätzlich den Installer.
- T650-Hardwareprüfung und korrigierte Installation auf Raspberry Pi 4 bestätigt;
  Grenzen von Live-Prüfung und Replay bleiben im Prüfbericht dokumentiert.
- Dokumentation DE/EN/FR wird aus einer Quelle auf beiden Domains veröffentlicht.

## 0.1.31: diagonale Slides und T650-Praxisprüfung

- Installation auf .112 jetzt abgeschlossen und Terminalausgabe geprüft:
  CLI und laufender Status 0.1.31, USB-/MQTT und Web active/running,
  beide NRestarts=0. Mobile aktiv, Fehlerliste leer. Alle fünf SHA256-Prüfungen
  für config, switches, Mobile-Identität, Vertrauen und Geräte unverändert.
  Installer-Sicherung: `/var/backups/ugso-usbhub-20261122-153636.tar.gz`.
  Dienststart 15:38:13, Webstart 15:38:16 laut Pi-Journal.
- Installation auf .112 beauftragt. Erster Versuch scheitert vor Umschaltung
  in Schritt 6 mit Permission denied beim Dienstbenutzer. Ursache: von meinem
  Prüfblock vererbte umask 077; Python-Umgebung dadurch nur für root zugänglich.
  Installer auf Programm-Umask 022 und private Archiv-Umask 077 korrigiert.
  Lokaler Shell-Regressionstest bestanden; erneute Installation danach erfolgreich.
- Vollständige isolierte T650-Messung am 22.11.2026 auf .112 abgeschlossen und
  Terminalausgabe gelesen. Alle acht erwarteten Richtungen erkannt, kein Tipp
  in Slide-Phasen; separater Tipptest 4 Tipps ohne X/Y. Drei Loopback-Broker
  erhielten jeweils 752 identische Nachrichten; Metadatenvergleich unverändert.
- Live Empfindlichkeit 5, Senderate maximal 10/s; andere Empfindlichkeiten und Raten mit
  denselben realen Aufnahmen im Replay geprüft. Zwei benachbarte Richtungsaktionen
  sowie ein anfängliches Halten mitprotokolliert; keine exklusive Richtungsprüfung.
  Grenzen und Messwerte im [Hardware-Prüfbericht](docs/tests/t650-0.1.31-20261122.md).
  Zur Messzeit lief der installierte Dienst .30; inzwischen auf .31 aktualisiert.
  Veröffentlichung anschließend gesondert vom Nutzer beauftragt.

- Erster realer RIGHT-Durchlauf: 14 Slides, 17 X/Y-Paare, kein Tipp; minimale
  Live-Abstände 0,100007 s. LEFT hing vor Messbeginn wegen nicht konsumiertem
  evdev-Generator beim Pufferleeren. Nur das Messwerkzeug korrigiert und mit
  18 betroffenen Tests geprüft; danach alle Phasen und den Endbericht ausgewertet.

- Quellsicherung: `M:\repos\_backups\ugso-usb-hub\before-diagonal-slide-20261122-144443.zip`.
- Acht Ein-Finger-Richtungen lokal umgesetzt, 199 Python-Tests bestanden.
  Geführtes Messwerkzeug zusätzlich lokal auf Replay, Ausschluss des K400 und
  Dienstwiederherstellung bei Fehlern geprüft (16 Slide-/Werkzeugtests grün).
- .112 vor der Installation im integrierten SSH-Terminal: 0.1.30, echtes T650 unter
  `/dev/input/event13` mit eindeutiger HID++-Kennung, Type-B-Slot-/X/Y-/Trackingdaten
  vorhanden, Achsenbereiche X 0–2832, Y 0–2364. K400/T400 nicht Teil der Messung.
- Erste Sicherung aller alten Releases wegen konservativer Platzprüfung
  abgebrochen; keine Installation. Freier Platz 1,8 GB. Aktives Programm 57 MB,
  komplette Nutzdaten 253 MB. Nutzer bestätigt aktive Sicherung; gzip-/tar-
  Prüfung vor dem späteren Teststart erfolgreich durchlaufen.
- Hardware-Bewegungs-/MQTT-Test im oben beschriebenen Umfang abgeschlossen.
  Geführte Prüfung mit Loopback-Brokern und temporärer Konfiguration, frühere
  Dienste werden wiederhergestellt. Kein Push und keine Veröffentlichung.
- Abschließender Gesamtlauf einschließlich Messwerkzeug: 202 Python-Tests grün.
  Relevante DOM-/Chrome-Prüfungen und Wheel erfolgreich. Die vorbereitete aktive
  Sicherung ist auch als `tools/backup_active.sh` im Paket enthalten.
  [Abgeschlossener Hardware-Prüfbericht](docs/tests/t650-0.1.31-20261122.md).

## 0.1.30: Ein-Finger-Slide (lokal)

- Quellstand vor Änderungen gesichert und ZIP-CRC geprüft:
  `M:\repos\_backups\ugso-usb-hub\before-one-finger-slide-20261122-142013.zip`.
- Vier anlernbare Richtungen, Empfindlichkeit 1–10, Obergrenze 1–30 Aktionen bzw.
  X/Y-Paare pro Sekunde. Nach erkannter Bewegung kein Tipp beim Abheben.
- Optionale X/Y-Zahlenwerte 0–100 mit gespeicherten Topics an Geräte-Zielbroker.
  Standard aus, kein JSON/Retain, kein Nachsenden an getrennte Broker.
- Lokale Prüfungen und Paketabschluss siehe
  [Prüfbericht](docs/tests/slide-0.1.30-local-20261122.md).
  T650-Hardwaretest noch offen. .112 und vorhandene Einstellungen unverändert.
  Keine Veröffentlichung und kein Push.
- 197 Python-Tests, danach 27 betroffene Tests erneut grün; neun Node-/DOM-
  Prüfungen und lokaler Chrome-Test erfolgreich. Drei echte lokale MQTT-Broker
  bestätigen Richtungen und Zahlenwerte; Routing und Offline-Fall geprüft.

## 0.1.29: lokaler Gerätestand

- Vollständige Quellsicherung vor Änderungen:
  `M:\repos\_backups\ugso-usb-hub\before-device-gesture-update-20261122-132149.zip`.
- Schrittfilter 1–5 für Lautstärke/Helligkeit/Tastaturlicht, Gerätegruppen mit
  Einzel-Aufklappfunktion, Serien-/HID++-Erkennung und manuelle Offline-Zuordnung.
- Geräteverwaltung sichert Metadaten vor Entfernen/Zuordnen/Widerrufen.
  Icons bleiben erhalten; Mobile-Vertrauen und Deck-Entfernung sind getrennt.
- Experimenteller Type-B-Multitouch-Auswerter für T650 und ähnliche Touchpads,
  ausdrücklich einschaltbar. Lokale synthetische Ereignisse, keine MQTT-Rohdaten.
- Nutzer: T650 noch nicht bereit, zunächst lokal testen. .112 unverändert,
  kein Push und keine Veröffentlichung. Der reale .28-Test gilt nicht für .29.
- 186 Python-Tests im wiederholten Gesamtlauf bestanden. Anschließend 35 Mobile-
  Tests nach der letzten Trennungsänderung erneut grün, ebenso 16 Geräte-/Gesten-
  Tests. Neun Node-/DOM-Prüfungen plus Chrome auf Desktop/schmalem Fenster grün.
  Wheel und Syntaxprüfungen erfolgreich. Ein einmaliger Windows-Lesekonflikt
  im ersten Gesamtlauf ist im [lokalen Prüfbericht](docs/tests/devices-0.1.29-local-20261122.md)
  dokumentiert. Metadaten-Rücksetzung und Erhalt übriger Daten lokal geprüft.

## Veröffentlichung 0.1.28

- Öffentliches Testrelease mit ZIP/Prüfsumme, Changelog und README DE/EN.
- Enthält die bisher lokalen Zwischenstände 0.1.23–0.1.27 und die begrenzte
  Mobile-Bildübertragung aus 0.1.28. Einstellungen/Topics und Kopplungen erhalten.
- 168 lokale Python-Tests bestanden, DOM-Prüfungen und Paketbau erfolgreich.
- Reale 15-Minuten-Prüfung am SM-T580 bestanden; Messwerte und Grenzen unten.
- Externe Doku in DE/EN/FR um Seiten, Navigation, Iconauswahl und Test ergänzt.

## 0.1.28: 15-Minuten-Praxistest bestanden

- SM-T580 auf .112 vom 22.11.2026, 11:39:17 bis 11:54:17 laut Pi-Uhr,
  volle 900 Sekunden mit monotonem Timer und 16 Messpunkten begleitet.
- Anfangs Vor/Zurück, danach 14 Minuten unveränderte Bild-/Context-Zähler
  (1228/19). Tablet in allen Messpunkten verbunden; Ping/Pong 56/56 → 232/232.
  Statusalter stets 0 bis 1,9 Sekunden.
- Abschließendes Journal des gesamten Zeitraums direkt aus dem integrierten
  SSH-Terminal gelesen: kein Heartbeat-Timeout, keine Trennung, kein Neustart.
  Ein zusätzlicher `connection open`-Eintrag um 11:48:38 ohne Gerätezuordnung;
  Tablet-Zähler bleiben durchgehend steigend, keine Rücksetzung.
- [Vollständiger Testbericht](docs/tests/mobile-0.1.28-15min-20261122.md).
  Der begrenzte Praxistest ist bestanden, die ursprüngliche Ursache damit nicht
  rückwirkend bewiesen. Keine Änderungen auf .112, nichts veröffentlicht.

- Aktualisierung des Praxisstands am 22. November: Nutzer meldet 0.1.28
  installiert. Im integrierten SSH-Terminal gibt `sudo ugso-usbhub --version`
  tatsächlich 0.1.28 aus. Mehrfaches Vor-/Zurückblättern bislang ohne Abbruch
  vom Nutzer bestätigt. Journal seit dem aktuellen Dienststart aus dem
  integrierten Terminal gelesen: Start am 22.11.2026 um 11:34:24, Verbindung
  geöffnet um 11:34:29 (PID 61379). Bis zur vorliegenden Ausgabe keine weiteren
  Einträge, keine Trennung und kein Heartbeat-Timeout. Aussage gilt für diesen
  Beobachtungszeitraum; der anschließende 15-Minuten-Test ist oben dokumentiert.

- Ausgangsfehler mit 0.1.27: Trotz zunächst erfolgreichem Vor/Zurück-Test meldet der Nutzer erneut
  Verbindungsverlust und Android-Fehler „Channel was closed“. Journaldaten
  aus seiner SSH-Sitzung bestätigen 11:24:08, SM-T580, Server schließt mit
  `Mobile heartbeat timeout; no close frame received`. Ursache bleibt offen.
- Vollständige Programmdatensicherung auf .112 vom Nutzer erstellt:
  `/var/lib/ugso-usbhub/exports/usb-extender-backup-20261122-111223.tar.gz`.
- Lokale Quellsicherung vor der Änderung:
  `M:\repos\_backups\ugso-usb-hub\before-mobile-fair-send-20261122-112932.zip`.
- Mobile-Sendeschleife verarbeitet maximal vier Bilder bzw. 25 ms Arbeit je
  Durchlauf (ein bereits laufender Socket-Sendevorgang kann länger dauern).
  Empfang und Heartbeat erhalten zwischen den Paketen wieder einen Durchlauf.
  Noch ausstehende Bilder bleiben gespeichert, neuere Bilder haben Vorrang.
- Trennungsprotokoll um Ping/Pong, letzte Nachrichtenart/Alter und Anzahl
  ausstehender Bilder ergänzt. Keine Nutzdaten oder Schlüssel protokolliert.
- Lokal langsame Übertragung simuliert sowie 8×8 mit exakt key:7/key:128 und
  sechs Seitenwechseln geprüft. Praxisbehebung noch nicht bestätigt.
- Gesamtlauf: 168 Python-Tests erfolgreich (91,077 s), fünf betroffene DOM-
  Prüfungen erfolgreich und Wheel 0.1.28 gebaut. Erster Gesamtlauf hatte einen
  Windows-Dateizugriffsfehler beim gleichzeitigen Lesen der Statusdatei;
  betroffener Test einzeln und wiederholter Gesamtlauf bestanden anschließend.
- Test-ZIP: `M:\icons\USB-Extender-Home-Assistant-0.1.28-Raspi4.zip`.
- Paket vom Nutzer auf .112 installiert; keine Veröffentlichung. Einstellungen,
  MQTT-Topics und Kopplungen durch die lokale Codeänderung nicht verändert.

## Vorheriger Teiltest mit 0.1.27 (durch erneuten Abbruch überholt)

- Am 22. November auf ausdrücklichen Nutzerauftrag in der Oberfläche von .112
  geprüft: 0.1.27, letzte Trennung SM-T580 mit `Mobile heartbeat timeout;
  no close frame received`, 64 Bilder / 1 Metadatenpaket. Letzte Eingaben:
  key:7 Navigation, danach key:128 Navigation. Keine Gerätefehler angezeigt.
- Die nachfolgend vom Nutzer ausgegebenen Journaldaten unterscheiden die
  ursprünglichen Abbrüche um 10:51 (kein Close-Frame) vom späteren Timeout
  um 10:53 in einer neuen Sitzung. Der Timeout allein erklärt den Fehler nicht.
- Nutzer führt SSH-Befehle im integrierten Terminal aus; dessen Ausgabe wurde
  direkt gelesen. Sicherung erfolgreich erstellt:
  `/var/lib/ugso-usbhub/exports/usb-extender-backup-20261122-111223.tar.gz`.
- Nach dem vom Nutzer vorgenommenen Dienstneustart erneuter Vor-/Zurück-Test
  mit 0.1.27: Tablet SM-T580, 8×8, 144×144-Bilder, zwei Seiten [0,1].
  Navigation key:7 = Vor, key:128 = Zurück. Status danach: Seite 1/2,
  eine autorisierte Sitzung mit geöffnetem Deck, 192 Bilder / 3 Context-Pakete,
  149 Ping / 149 Pong, keine Trennungen, keine Gerätefehler und keine
  Journaleinträge in den letzten zwei Minuten. Dieser Durchlauf ist erfolgreich.
- Ursprünglichen Fehler nicht als behoben markieren: Ursache ungeklärt,
  derzeit nicht reproduzierbar. Kein Laufzeitpatch oder neues Update auf .112,
  Einstellungen und Kopplungen erhalten; nichts veröffentlicht.

- Nutzer meldet Abbruch beim Zurückblättern; Vor funktioniert.
- Sicherung: `M:\repos\_backups\ugso-usb-hub\before-back-navigation-20261122-105703.zip`.
- Verschlüsselten Zwei-Geräte-Test um drei Wechsel zurück auf Seite 1 und
  wieder vor erweitert: erfolgreich, Verbindung bleibt erhalten, kein MQTT.
- Zusätzlich lokaler verschlüsselter 8×8-Test mit genau key:7/key:128,
  sechs Vor-/Zurück-Wechseln, erfolgreich. Keine spekulative Laufzeitänderung.

## 0.1.27 – 22. November 2026: Gehe zu (nur lokal)

- Vorher gesichert: `M:\repos\_backups\ugso-usb-hub\before-goto-page-20261122-102833.zip`.
- Gestaltung → Tastenfunktion: Vor, Zurück, Home und Gehe zu mit Zielseitenauswahl.
  Nach Speichern navigieren die Tasten direkt am Gerät, ohne MQTT-Ausgabe.
- Gelöschte Sprungziele führen zu Seite 1; nachfolgende Ziele werden nachgeführt.
- 61 Python-Tests (Seiten, Gestaltung, Mobile) und beide betroffenen DOM-Prüfungen
  erfolgreich. Speichern/Neuladen, Geräteisolation und Zielvalidierung geprüft.
- Einstellungen erhalten, keine Veröffentlichung und kein Zugriff auf .112.
  Praxistest der neuen Sprungtaste am Tablet bleibt offen.

## 0.1.26 – 22. November 2026: Deck-Seiten und kompakter Editor (nur lokal)

Sicherung vor Beginn einschließlich unveröffentlichter 0.1.25:
`M:\repos\_backups\ugso-usb-hub\before-deck-pages-20261122-094654.zip`.

- Nutzer bestätigt Kopplung und Betrieb von Handy und Tablet mit dem vorherigen
  Stand. Die neuen Seitenfunktionen sind noch nicht auf diesen echten Geräten geprüft.
- Ansicht und Menü heißen „USB / Virtuelle Geräte“. Jeder Deck-Editor bietet
  bis zu acht Seiten, Neue Seite, Löschen nach Rückfrage und geschützte Seite 1.
- Fortlaufende sichtbare Tastennummern (z. B. 1–15, 16–30). Automatische Namen
  werden entsprechend aktualisiert; selbst benannte Tasten bleiben erhalten.
- Stabile interne Seitenslots: Löschen einer mittleren Seite ändert die IDs und
  Topics verbleibender Seiten nicht. Eigene Gestaltung und Belegungen je Seite.
- Navigationstypen Vor/Zurück/Home statt MQTT, optionaler Zähler wie 2/3 auf den
  Tasten. Grenzen ohne Umlauf; Home auf Seite 1. Editorbuttons wechseln nur die
  Vorschau. Nach Dienstneustart beginnt das Gerät auf Seite 1.
- Seitenwechsel beenden gehaltene Tasten und offene Klickfolgen. Späte Releases
  werden nicht als Aktionen auf der neuen Seite ausgeführt. Rückmeldungen bleiben
  der passenden Seite zugeordnet. Trennen/erneutes Verbinden löst keine Sperre aus.
- Native Mobile-Seitenbefehle und Kontextmetadaten ergänzt. Lokal mit zwei
  verschlüsselten Testclients geprüft: unabhängige Seiten, passende Bildübertragung,
  keine neue Verbindung und keine MQTT-Aktion für Navigation.
- Farbfelder 64×28 mit Hexwert; weitere Gestaltungsfelder kompakter. Suche und
  Icon-Miniaturcache sowie Material-Vault-Deduplizierung bleiben enthalten.
- 164 Python-Tests, acht Node-/DOM-Prüfläufe und Chrome erfolgreich. HTTP-Speichern,
  Wiederladen, Seitenlöschung und übrige IDs/Topics geprüft. GUI-Test mit 15/16
  Tasten, zwei simulierten Geräten sowie schmaler Ansicht. Bestehende Seite 1 und
  ursprüngliches MQTT-Topic unverändert. Python-Wheel gebaut.
- README DE/EN und Roadmap aktualisiert. Neues lokales ZIP unter M:\icons.
  Nichts veröffentlicht oder gepusht; keine Änderungen/Tests auf .112.

## 0.1.25 – Nachtrag: Material-Vault-Dubletten (nur lokal)

Sicherung vor der Korrektur:
`M:\repos\_backups\ugso-usb-hub\before-icon-dedup-20261121-214959.zip`.

- Die vom Nutzer genannten Originalarchive Material Vault Black/White vollständig
  lokal geprüft. Je 6.862 Dateien, aber nur 5.576 unterschiedliche Dateiinhalte.
  Die mehrfach markierten Kacheln hatten dieselbe inhaltsbasierte Icon-ID.
- Der Such-/Auswahlkatalog fasst gleiche IDs je Paket zusammen; auch die
  Bibliotheksanzeige zeigt nur eine Kachel. Zusätzliche Dateinamen/Tags bleiben
  als Aliase suchbar und im Tooltip sichtbar. Lizenzhinweise bleiben erhalten.
- Originaldateien und Importprotokoll/Dateizuordnungen im Rohindex bleiben erhalten.
  Kein Umschreiben gespeicherter IDs oder Geräteeinstellungen und kein Neuimport nötig.
  Echte Stilvarianten und verschiedene Pakete werden nicht zusammengelegt.
- Realtest: beide vollständigen Archive importiert, insgesamt 13.724 Quelldateien
  und 11.152 Katalogicons. Je 1.286 alternative Dateieinträge zusammengefasst.
  Vorhandene Konfigurationsdatei blieb bytegleich; vorhandene Home-ID blieb gültig.
- Chrome mit echten Paketmetadaten und 48px-Miniaturen: Suchwort home liefert je
  Farbe 19 eindeutige Kacheln, statt 21 Dateieinträgen. Genau eine Kachel derselben
  ID markiert. Suche nach alternativem Dateinamen und Übernahme derselben ID geprüft.
- 153 Python-Tests und sieben Node-/DOM-Prüfläufe erfolgreich. .112 unverändert,
  Farbsets unverändert; nichts veröffentlicht. Lokales ZIP 0.1.25 unter M:\icons.

## Tagesabschluss – 21. November 2026

Arbeitsstand: 0.1.24, ausschließlich lokal. Quellcode, lokale Git-Historie,
Programm-ZIP einschließlich SHA256, die 147 Farb-ZIPs und ausgewählte Prüfberichte
werden als Tagesabschluss unter `M:\repos\_backups\ugso-usb-hub\` gesichert.

Fortsetzung: zuerst den Stand hier und die Roadmap lesen. Kein Import oder Update
auf .112 ohne neuen Auftrag. Die Farbsets sollen später nach Freigabe als
Open-Source-Downloads angeboten werden. Aktuell nichts veröffentlichen/pushen.
Alle lokalen Testserver wurden beendet; vorhandene Benutzereinstellungen bleiben erhalten.

Programm: `M:\icons\USB-Extender-Home-Assistant-0.1.24-Raspi4.zip`.
Farbsets: `M:\icons\HA-MDI-Favoriten-0.1.23\Pakete\`.
Vorschau: `M:\icons\Iconauswahl-0.1.24.png`.

## 0.1.24 – Grafische Iconauswahl und Miniaturcache (nur lokal)

Sicherung einschließlich der noch unveröffentlichten 0.1.23:
`M:\repos\_backups\ugso-usb-hub\before-visual-icon-picker-20261121-213459.zip`.

- Iconbuttons öffnen ein kompaktes Fenster mit Paketen, Suche und 48×48-Raster.
  Gemeinsame Auswahl für normal, gedrückt, Hintergrund und MQTT-Rückmeldung.
- Keine tausenden Selectoptionen beim Formularaufbau; Index einmal je geladener
  Bibliothek. Pro geöffnetem Paket höchstens 96 Kacheln mit Seitenwechsel.
- Lazy-Laden nur sichtbarer/naher Miniaturen. Separater atomarer PNG-Cache unter
  `icons/.cache/thumbnails/`, kein Vollbild-/Animationscache für die Auswahl.
  Authentifizierte Thumbnailroute mit privatem Browsercache; API weiter no-store.
- Kompakter Katalog überträgt wiederholte Paketlizenztexte einmal; alte API bleibt
  kompatibel. Lokaler Vergleich für 40 echte Favoriten: 583.391 auf 37.739 Bytes
  (93,5 % weniger), ohne Änderung der gespeicherten Lizenzangaben.
- Lokaler Chrome-Einzelvergleich mit 6.862 synthetischen Iconmetadaten:
  Editoraufbau 93,7 auf 6,5 ms; Selectoptionen 27.466 auf 14. PC-Werte, kein Pi-Test.
- 152 Python-Tests und sieben Node-/DOM-Prüfläufe bestanden. Miniaturgröße,
  erstes Animationsbild, Cache-Wiederverwendung/Parallelzugriff, Fehlerwiederholung,
  private HTTP-Header und Kataloginvalidierung geprüft.
- Chrome: echte 48px-PNGs, 56 Browsercache-Treffer, Pakete, Abbrechen ohne Änderung,
  gedrücktes Icon speichern/neuladen, Escape und schmale Ansicht erfolgreich.
- Ein bestehender MQTT-Test prüfte den asynchronen Plus-Reset zu früh. Er wartet
  nun auf dessen Empfang; keine MQTT-Funktionsänderung. Gesamtsuite danach grün.
- Nur lokal getestet. .112 und Benutzereinstellungen unverändert; nichts veröffentlicht.

## 0.1.23 – MDI-Favoriten und CSS-Farbsets (nur lokal)

Sicherung vor Beginn:
`M:\repos\_backups\ugso-usb-hub\before-mdi-favorites-20261121-211710.zip`.

- 20 Ein-/Aus-Paare aus MDI 7.4.47 für übliche HA-Entitäten; 147 gelieferte
  CSS-Farben als Hintergrund, kontrastierende schwarze/weiße Symbole, 48×48 SVG.
- 147 Farb-ZIPs / 5.880 Icons und entpackte Ordner unter
  `M:\icons\HA-MDI-Favoriten-0.1.23`, mit Vorschau, Prüfsummen und Paketlizenzen.
- Quellen unverändert abgelegt, erzeugte SVGs ohne Stylesheet: CSS-Füllung wird
  als statisches SVG-Attribut übernommen. Keine Lockerung der SVG-Importprüfung.
- Optionales mitgeliefertes SteelBlue-Paket (40 Icons) per Button in Iconbibliothek.
  Kein automatischer Import; erneutes Hinzufügen erhält IDs und bestehende Zuordnungen.
- 143 Python-Tests und sechs Node-/DOM-Prüfläufe erfolgreich. Alle Farbarchive,
  SVG-Validierung, Ein-/Aus-Metadaten und Lizenztexte geprüft. Helle/dunkle Varianten
  gerendert und visuell kontrolliert. Python-Wheel enthält das unveränderte Archiv.
- Lokaler Chrome-Test: Favoriten-Button, 40 Vorschauen, echtes rotes Farb-ZIP,
  Wiederimport, Neuladen und schmale Ansicht; bestehende Konfiguration unverändert.
- Kein Zugriff/Import/Update auf .112. Nutzer möchte die Sets später als
  Open-Source-Downloads bereitstellen; noch nichts veröffentlicht oder gepusht.

Die gemeldete Rückkehr zur Anmeldung beim früheren großen Import ist als Ursache
nicht abschließend geklärt. Der Code begrenzt Sitzungen auf eine Stunde; nach
Einspielen von 0.1.22 meldete der Nutzer wieder funktionierenden Import. Der
vollständige Abschluss der 6.862 Icons wurde noch nicht ausdrücklich bestätigt.

## Veröffentlichung 0.1.22 – 21. November 2026

Nutzerfreigabe zur Veröffentlichung von Quellcode, ZIP, Changelog, README und
DE-/EN-/FR-Dokumentation. Enthält die lokalen Fortschritte seit dem öffentlichen
Stand 0.1.5. 134 Python-Tests, DOM-Abläufe und lokale Chrome-Prüfungen erfolgreich.
Benchmarkwerte sind PC-Einzelmessungen, keine Pi-Messungen. Reale Mobile-/Hardware-
Praxistests bleiben in der Roadmap offen. Kein Update des laufenden Imports auf .112.
Die folgenden Abschnitte protokollieren die zuvor unveröffentlichten Arbeitsschritte.

## 0.1.22 – Batchimport und Vorschauen bei Bedarf

Sicherung: `M:\repos\_backups\ugso-usb-hub\before-lazy-import-20261121-202419.zip`.
Ein Index-Commit pro Paket/Pi-Ordner. Browserordner als ein lokal erzeugtes ZIP,
mit Paketmetadaten und UTF-8-Dateinamen. Originale bleiben mit Namen erhalten;
Bild- und Animationscache entsteht bei erster Verwendung. Alte Cachedateien und
vorhandene IDs mit Originalzuordnung bleiben kompatibel. Alte Einstellungen unverändert.
Indexcommitfehler, Cachefehler/Wiederholung, parallele Vorschauanfragen und mehrere
Paketordner lokal geprüft; SVG-Rendering und verschlüsselter Mobile-Pfad erhalten.
Windows-Einzelvergleich: Itsyhome 240 = 4,262 → 0,395 s; synthetische 6.800 PNGs =
458,323 → 10,464 s. Indexschreibvorgänge jeweils 240/6800 → 1, Vorabrendern → 0.
Der neue 6800er-Import braucht direkt danach 3.604.281 statt 9.443.441 Bytes,
bevor Icons tatsächlich angezeigt werden. Messungen auf dem PC, nicht auf dem Pi.
Laufender Nutzerimport mit ca. 6800 Icons auf .112 unangetastet; kein Rollout,
keine Veröffentlichung. Update erst nach Abschluss dieses Imports.

## 0.1.21 – Lesbarer Paketname und Importfortschritt

Sicherung: `M:\repos\_backups\ugso-usb-hub\before-package-progress-20261121-194855.zip`.
Installierte Fluent-manifest.json nur lesend geprüft: Name „Fluent UI System Icons (Filled)“.
Beim Browser-Ordnerupload bisher übergangene Metadaten werden jetzt gelesen,
Paketordner und Originalnamen unverändert beibehalten. Wiederimport kann den
Anzeigenamen aktualisieren; vorhandene IDs und Tastenzuordnungen bleiben erhalten.
Ladebalken zeigt beim Archivimport echte Zähler über authentifizierten Statusabruf.
Während Übertragung/Paketprüfung unbestimmter Balken, keine erfundenen Prozentwerte.
Lokaler Chrome-Upload Itsyhome: 240 importiert; echte Zwischenstände 20,41,61,
81,97,115,128,142,157,175,192,209,223,235 beobachtet. Nur lokale Testdaten,
kein Eingriff auf .112 und keine Veröffentlichung.

## 0.1.20 – Itsyhome-Import

Vorher gesichert: `M:\repos\_backups\ugso-usb-hub\before-itsyhome-import-20261121-192431.zip`.
Bereitgestelltes Itsyhome-1.2-mac.streamDeckPlugin in isolierter Testablage:
vorher 0 Icons, Ursache Ordner imgs/ außerhalb des bisherigen Importfilters.
Nach Korrektur 240/240 PNGs in 14 Unterordnern, keine ausgelassenen Bilder,
Originalnamen und Ordner erhalten, keine JS-Dateien übernommen oder ausgeführt.
Vorhandene Einstellungen unverändert; keine Änderungen auf .112 und keine Veröffentlichung.

## 0.1.19 – Paketlizenz und kompakte Kacheln

Sicherung: `M:\repos\_backups\ugso-usb-hub\before-compact-package-license-20261121-192230.zip`.
Lizenzhinweis neben dem Paketnamen; vollständige Texte einmal im Paket aufklappbar,
identische Texte zusammengefasst. Verschiedene Hinweise bleiben erhalten, auch bei
gefilterter Iconsuche. Keine Lizenzdetails in einzelnen Kacheln. Kacheln 52×52,
Bildfläche 48×48. Animationsinformationen nur im Popup. Vorhandene Dateien,
Iconzuordnungen und Einstellungen unverändert; lokal geprüft, keine Veröffentlichung.

## 0.1.18 – Pakete, Animationen und Speicheranzeige

Vorher gesichert: `M:\repos\_backups\ugso-usb-hub\before-animated-library-20261121-190050.zip`.
Originale in icons/IconPacks mit Paketordner/Unterordner/Dateiname erhalten.
Cache getrennt, ältere Dateien/IDs weiter lesbar. Bibliothek zunächst geschlossen,
Suche, Hover mit Name/Paket, Miniaturen 48×48. GIF/WebP normal und gedrückt animiert,
maximal 120 Frames und 10 Bilder/s; statische Icons bleiben ohne Änderung ruhig.
Paketentfernung sichert vorher und schützt verwendete IDs. Speicheranzeige nutzt
das Dateisystem des Datenordners, nicht die Windows-PC-Platte bei einer Pi-Installation.
Lokale Python-/DOM-/Chrome-Prüfungen mit dem bereitgestellten HA-Plugin-ZIP sowie
verschlüsselter Mobile-Protokollprüfung erfolgreich. Reales Tablet/Pi noch offen.
Vom Nutzer gelöschte Icons auf .112 nicht wiederhergestellt; keine dortigen Änderungen,
keine Veröffentlichung.

## 0.1.17 – Kompakte Tastenliste

Sicherung: `M:\repos\_backups\ugso-usb-hub\before-key-accordion-20261121-182606.zip`.
Tasten zunächst zugeklappt, nur Gerätename/Key/Name sichtbar. Höchstens eine
Tastengruppe offen; bisherige Topics und Optionen bleiben erhalten.
Speicherhinweis plus Speichern/Abbrechen direkt im Eintrag. Speichern nutzt den
bestehenden Konfigurationsablauf; Abbrechen setzt nur diese Taste zurück.
DOM- und Chrome-Prüfungen: exklusive Öffnung, Umbenennen, selektives Abbrechen,
Speichern/Neuladen sowie schmale Ansicht ohne Seitenüberlauf erfolgreich.
Öffnen/Schließen ist reiner Browserzustand und ändert keine MQTT-Konfiguration.
Namensänderungen aktualisieren die Zeile sofort. Keine Änderung auf .112,
keine Veröffentlichung. Installation und Praxisprüfung bleiben beim Nutzer.

## 0.1.16 – Eigene Gestaltung während des Drückens

Sicherung: `M:\repos\_backups\ugso-usb-hub\before-pressed-artwork-20261121-182131.zip`.
Optionales zweites Icon sowie Text- und Hintergrundfarbe pro Taste. USB- und
Mobile-Deck verwenden denselben Renderer. Loslassen stellt die normale Anzeige
einschließlich vorheriger MQTT-Anzeigewerte wieder her. Wiederholte Press-Meldungen
schalten nicht erneut um. Vorschau ohne MQTT-Aktion. Lokale Persistenz-, Rendering-,
Ereignis- und DOM-Prüfungen sowie Chrome mit Speichern/Neuladen erfolgreich.
Echter Tablet-Test offen. Nutzer meldet vorherigen Ausfall als Browserproblem.
Keine Einstellungen auf .112 geändert und nichts veröffentlicht.

## 0.1.15 – Android-Raster und rechtzeitiger Keepalive

Sicherung: `M:\backups\usb-extender\before-android-grid-heartbeat-20261121-173815.zip`.
Nutzer korrigiert Rasterhoheit und zeigt Trennungsgrund „received 1001 ... receive
timeout“, 24 Bilder/1 Context. APK: M3/t$a startet Empfang unter Timeout aus M3/f.d;
M3/t.g antwortet auf Ping mit leerem Pong. Unser 15-Sekunden-Ping war zu spät
und verwendete zufällige Nutzdaten. Jetzt leere Pings alle fünf Sekunden,
Pong-Überwachung getrennt von Bildern. Produktivbestätigung auf .112 noch offen.

mobile_layout wird nicht mehr angewandt; alte Einstellung bleibt als inaktiver
Wert erhalten. Kein Rastereingriff mehr im Editor oder Mobile-Server-Formular.
App meldet Raster, Server/Editor übernehmen es ohne Trennung. Offline-Geometrie
bleibt erhalten; Rasterwechsel bei Textentwurf ersetzt nur das Tastenraster.

## 0.1.14 – dauerhafter Offline-Editor und X/Y-Raster

Sicherung: `M:\backups\usb-extender\before-persistent-streamdeck-20261121-170237.zip`.
Nutzer bestätigt Farben korrekt, meldet weiter Nachladen/verschwindenden Tab.
Definite UI-Ursache: Tab an Live-Inventar gebunden, Statuswechsel erneuerte Formular
und setzte Auswahl zurück. Jetzt dauerhafter Tab mit getrennt aktualisiertem
Online/Offline-Hinweis; Geometrie bleibt gespeichert und Entwürfe unangetastet.
Wiederkehrendes Mobile-Deck löst keine erneute Navigation mehr aus.

Optionalbefehle führten bisher zur Sitzungstrennung. Nun kein Verbindungsabbruch
für Shortcuts/lesbare unbekannte Erweiterungsnachrichten eines autorisierten Clients;
keine Shortcut-Ausführung hinzugefügt. Malforme/unauthentifizierte Nachrichten
werden weiter abgewiesen. Letzte Trennungen mit Grund sichtbar, keine Geheimnisse.
Ob diese Nachrichten den konkreten Android-Abbruch auslösten, ist unbestätigt.

X/Y-Schritte je Mobile-Deck 1–8, persistiert und ohne Listenerneustart übernommen.
Editor-/Serverraster kann Androids natives sichtbares Raster nicht erzwingen.
102 Python-Tests, fünf Node-Prüfungen und lokaler Chrome-Test erfolgreich.
Kein neuer Zugriff auf .112, erneute Android-Dauerprüfung steht aus.

## 0.1.13 – Mobile-Farben, Anzeigeupdates und automatische Tastenkanäle

Sicherung: `M:\backups\usb-extender\before-mobile-colors-topics-20261121-163502.zip`.
Nutzer: Rot/Blau vertauscht, Icon blinkt weiterhin; Tasteneingaben kommen an,
aber fehlen gespeicherte Standardkanäle. LZ4-Pixel jetzt BGRA; gleiche Bildpixel
und Context-Metadaten werden unterdrückt, veraltete Bildgrößen verworfen. Zähler
zeigen tatsächlichen Bild-/Metadatenversand. Blinken auf Android noch bestätigen.

Nach Freigabe/Speichern ergänzen Editor und Web-API fehlende Stream-Deck-Tasten
mit allen elf benannten Kanälen. Vorhandene Tasten bleiben unverändert, individuelle
Zusatzaktionen bleiben zusätzlich aktiv. Persistenz, Geheimniserhalt, eindeutige
Gerätenamen und echtes lokales MQTT mit Mobile-WebSocket geprüft. Keine Eingriffe
auf .112 und keine Veröffentlichung.

## 0.1.12 – Android-Mindestversion beim Handshake

Sicherung: `M:\backups\usb-extender\before-mobile-version-handshake-20261121-161715.zip`.
Nutzer meldet grauen Server und „Streamdeck Version min. 6.3“. Im eigenen Hello
wurde irrtümlich die Extender-Produktversion 0.1.x als Desktop-Version gesendet.
APK-Befund: N3/i und N3/m$d enthalten Mindestversionsangabe 6.3. Die unabhängige
Protokollimplementierung sendet jetzt die Kompatibilitätskennung 6.3.0; Produkt-
version bleibt getrennt sichtbar. Keine Änderung von Clientkaufstatus/Identität.
Lokaler verschlüsselter Test: Mindestversion und sechs Gestaltungsänderungen
ohne neue Verbindung/Vertrauensänderung geprüft. Bestätigung auf Android offen.

## 0.1.11 – Iconordner direkt vom PC importieren

Sicherung: `M:\backups\usb-extender\before-icon-folder-import-20261121-160645.zip`.
Browser-Ordnerauswahl lädt Bilder aus Unterordnern einzeln zum bestehenden
geschützten Upload-Endpunkt. Ordnername als Sammlung, Fortschritt und Fehlerliste.
Mehrfachauswahl für einzelne Dateien ergänzt; Raspi-Pfadimport bleibt erhalten.
Keine Änderung bestehender Konfiguration oder MQTT-Belegungen.

## 0.1.10 – unveränderte Mobile-Icons nicht erneut übertragen

Text oben/unten verkleinert jetzt das Icon zugunsten eines separaten Textbereichs;
Hintergrund bleibt vollflächig. Mittiger Text bleibt überlagert. Pixelprüfungen
für contain/cover, drei Bildgrößen und ohne Beschriftung erfolgreich.

Sicherung: `M:\backups\usb-extender\before-mobile-icon-refresh-20261121-160204.zip`.
Unveränderte UpdateKeypadConfig.iconSize löste bisher immer refresh_required aus.
Jetzt nur bei echter Größenänderung; zusätzlicher Bildvergleich pro Sitzung
verhindert wiederholten Versand gleicher Bilder auch bei allgemeinen Refreshs.
Neue Decköffnung und Größen-/Rasterwechsel leeren den Sendecache.

Nutzer bestätigt Kopplung/Decköffnung und sichtbares importiertes Icon auf dem
SM-T580. Gemeldete Rasterabweichung Tablet 3×5/Editor 5×5 noch nicht real verifiziert;
der Screenshot zeigt noch keine Rasterherkunft aus 0.1.9. Kein Zugriff auf .112.
Statische APK-Prüfung des Pro-Kaufstatus und Designfilters im Protokollbericht.

## 0.1.9 – Tabletraster und Editor ohne Verbindungsabbruch

Sicherung: `M:\backups\usb-extender\before-mobile-grid-20261121-154936.zip`.
Neuer Standard 5 Spalten × 3 Zeilen; vorhandene Einstellungen erhalten. Ein vom
Tablet gemeldetes Raster hat Vorrang und wird mit gleicher Ausrichtung im Editor
angezeigt. Die Android-Ansicht selbst ist in der App einzustellen; Serverfelder
sind jetzt ausdrücklich Rastervorgaben für Clients ohne eigene Meldung.

Bei neuem Mobile-Deck öffnet sich der grafische Editor automatisch, ohne Entwürfe,
Anlernen oder MQTT-Freigaben zu überschreiben. Nur Änderungen an Aktivierung,
Bindeadresse oder Port erfordern einen Listener-Neustart. Rasteränderungen halten
Verbindung und Deck offen. Timingfehler beim initialen Context-Versand behoben.
Lokal mit WebSocket-Gegenstelle, DOM und Chrome geprüft; nicht auf .112 eingespielt.

## 0.1.8 – fehlende Kopplungsbestätigung korrigiert

Der Nutzer zeigte auf .112 einen verbundenen Client „SM-T580 · Kopplung ausstehend“,
aber keinen Prüfcode/Bestätigungsbutton. 0.1.7 zeigte diese erst nach Authenticate.
Jetzt wird der bekannte Client schon nach Hello zur manuellen Prüfung angezeigt;
die Bestätigung kann vor oder nach seiner zusätzlichen Auth-Anfrage erfolgen.
Ok-Antworten verwenden ausschließlich tatsächlich empfangene Anfrage-IDs.

Sicherung: `M:\backups\usb-extender\before-mobile-pairing-fix-20261121-154051.zip`.
Wartender Hello-Client lokal mit echter WebSocket-Gegenstelle und Chrome geprüft:
Code stimmt überein, Button sichtbar, Freigabe und spätere Auth-Anfrage erfolgreich.
Ohne Bestätigung keine Steuerung; Ablehnung und ungültige Pakete weiterhin gesperrt.
Nutzereinstellungen erhalten. Neues ZIP 0.1.8 lokal; auf dem Pi noch nicht eingespielt.

## 0.1.7 – optionaler Stream-Deck-Mobile-Server

Sicherung vor Änderungen:
`M:\backups\usb-extender\before-mobile-server-20261121-151403.zip`.
Vorhandene 0.1.6-Arbeiten, Einstellungen und Bilder erhalten. Keine Software auf
dem Pi oder Android installiert und keine Live-Broker verändert.

Standard aus; unter Mobile-Server konfigurierbar. QR-Scan führt zum lokalen VSD2-
WebSocket-Server, zusätzlich ist eine Web-Bestätigung des Client-Prüfabdrucks nötig.
Schlüssel/Vertrauen/virtuelle Decks separat im Datenordner. Grafik-/MQTT-Zuordnung
über den bestehenden Stream-Deck-Tab; Raster bis 64 Tasten, ohne Server-Pro-Stufe.
Server läuft unabhängig von der abschaltbaren Weboberfläche. Einseitige Geräte-
löschung aus Android wird nicht übernommen; Daten bleiben erhalten.

88 Python-Tests erfolgreich, einschließlich echtem Loopback-WebSocket mit NaCl-Box-
Gegenstelle, LZ4-Pixelprüfung, MQTT-Empfang, Web-Aktivierung/Bestätigung, Portkonflikt,
Abschalten und Neustartpersistenz. DOM-Tests und Chrome Desktop/Mobil erfolgreich.
Ein echter Android-/Pi-Praxistest steht aus; App-Beschränkungen und mögliche eigene
Online-Prüfungen sind damit nicht bewertet. Technischer Befund in
`docs/MOBILE-PROTOKOLL.md`. Lokales ZIP 0.1.7; nichts veröffentlicht.

## 0.1.6 – grafischer Stream-Deck-Tab (lokales Paket)

Vorher gesichert unter `M:\backups\usb-extender\before-streamdeck-20261121-143206.zip`.
Keine Änderungen am Raspberry Pi, an Live-Brokern oder vorhandenen Einstellungen.
Zusätzlicher bedingt sichtbarer Tab, treuer Modellraster, Tastenbildgestaltung,
MQTT-Aktionen und Rückmeldungszuordnung umgesetzt. Eigenständige Implementierung
auf dem vorhandenen StreamDeck-Treiber; kein Deck-Switch-Code übernommen.

Chrome lokal mit simuliertem MK.2: 15 Tasten, echte authentifizierte PNG-Vorschau,
Speichern/Neuladen, bestehendes Topic und Desktop-/Mobilansicht geprüft.
Automatisierte Tests prüfen zusätzlich Mini-Layout, Pedal, Abziehen, stale Dienst,
Bildausgabe im nativen Geräteformat, ungültige Gestaltung und Erhalt der Zugangsdaten.
Ein physischer Stream-Deck-Test auf dem Pi steht aus. Neues ZIP 0.1.6 lokal,
keine Veröffentlichung oder Website-Bereitstellung in diesem Arbeitsschritt.

Abschluss: 72 Python-Tests, Tastenlisten-/Stream-Deck-DOM-Prüfungen und Chrome
erfolgreich. Installations-ZIP im Downloads-Ordner, einschließlich Prüfsummendatei.

## Öffentliche Veröffentlichung und Nutzer-Praxistest 0.1.5

Der Nutzer hat 0.1.5 inzwischen auf dem Raspberry Pi eingesetzt und neun
Screenshots bereitgestellt. Sie liegen unter `docs/screenshots/live-0.1.5/`.
Sichtbar: drei online gemeldete Brokerplätze, Funktionstasten, HA-Switchwerte Ein
und Tastenzustände Aus nach Loslassen sowie einzelne ioBroker-Datenpunkte mit
press/release/click/hold und ON/OFF. Leere Plus-Rücksetzungen erscheinen dort als null.
Der zuvor fehlende ioBroker-Empfang ist damit für die gezeigten Topics nachgewiesen.

Der Verlauf zeigt MQTT-Übergaben an drei Ziele; er allein beweist keinen Empfang
auf jedem Broker. Doppelklick und Neustartpersistenz bleiben automatisierte
Prüfnachweise, nicht zusätzliche durch die Bilder belegte Hardwaretests.
Physische Stream Decks und ähnliche Fremdgeräte benötigen weitere Praxistests.

Deutsche/englische README, Hardwaretest-Issueformular und bebilderte DE/EN/FR-
Webdokumentation sind für die öffentliche Veröffentlichung ergänzt. Der bestehende
Git-Verlauf wurde auf versehentlich versionierte Konfigurationen und typische
Zugangstoken/Privatschlüssel geprüft; keine solchen Treffer. Dies ist kein
vollständiges Sicherheitsaudit. GitHub Secret Scanning war im privaten Repo nicht aktiv.

Die folgenden Abschnitte dokumentieren die früheren Implementierungsstände.

## USB Extender für Home Assistant 0.1.5

Switch ist jetzt ein Umschalter mit dauerhaftem Zustand in `switches.json`.
Tastenzustand, gemeinsame Button-/Button+-Ereignisse und einzelne Klick-,
Doppelklick- und Halten-Kanäle sind ergänzt. Die Oberfläche nutzt die volle
Fensterbreite und gruppiert die Kanäle kompakt nebeneinander.

Sicherung der vorherigen Quellen:
`M:\repos-backups\usb-extender-before-buttons-20261121-133714`.
61 Python-Prüfungen und beide JavaScript-Prüfläufe erfolgreich. Die lokale
DOM-Prüfung lädt die echten Styles und prüft die aufgehobene Breitenbegrenzung.
Dies ist kein visueller Chrome-Live-Test auf dem Pi.

Auf .112 wurde inzwischen 0.1.4 mit gespeicherten Lautstärketasten gesehen.
Der zuvor in ioBroker betrachtete JSON-Wert gehörte zum alten Datenpunkt
`mqtt.0.Trust-key-f1`; neue Lautstärketopics waren vorhanden konfiguriert, aber
ihre letzten beobachteten Eingaben stammten noch aus dem Anlernmodus und wurden
nicht gesendet. Der neue Live-Nachweis bleibt offen.

0.1.5 wurde in diesem Schritt nicht auf dem Pi installiert; vorhandene
Pi-Einstellungen wurden nicht verändert. Neues ZIP für den regulären Installer.

## USB Extender für Home Assistant 0.1.4

Neue Tasten werden mit fünf lesbaren, vorbelegten Topics aus dem Gerätenamen
angelegt. Press+/Release+ sind jetzt eigene Kanäle, die nur sich selbst nach
50 ms zurücksetzen. Alle fünf sind standardmäßig an, einzeln abschaltbar und
bearbeitbar. Bestehende Belegungen werden nicht automatisch umbenannt.

Alle Discovery-Komponenten eines USB-Geräts teilen dieselbe stabile Gerätekennung
und denselben gewählten Anzeigenamen. Lokal geprüft: zwei Tasten mit insgesamt
acht Aktionsauslösern und zwei Switch-Binärsensoren unter einem gemeinsamen Gerät.
Der tatsächliche HA-Geräteregister-Nachtest nach Installation steht noch aus.

Vorherige Quellen gesichert unter
`M:\repos-backups\usb-extender-before-readable-topics-20261121-130409`.
47 Python-Prüfungen und beide JavaScript-Prüfläufe lokal erfolgreich.
Keine Installation auf .112, keine Änderungen an HA/ioBroker in diesem Schritt.
Der fehlende ioBroker-Tastenempfang bleibt offen.

## USB Extender für Home Assistant 0.1.3

Implementiert: Anlernmodus, editierbare Tastenliste, Press/Release, Switch ON/OFF,
Press+/Release+ und Wiederholung für KEY_VOLUMEUP/KEY_VOLUMEDOWN. Bestehende
Einzelbelegungen, Brokerzugangsdaten und Geräteziele werden nicht ersetzt.

Vorherige lokale Quellen und vorhandener lokaler Zustand gesichert unter
`M:\repos-backups\usb-extender-before-learning-20261121-123412`.
Keine Installation oder Einstellungsänderung auf dem Raspi in diesem Arbeitsschritt.
Das neue ZIP ist für ein Update mit `sudo bash install.sh` vorgesehen; der Installer
sichert dabei den tatsächlichen Zustand auf dem Pi vor dem Update.

Auf .112 wurde inzwischen **0.1.2** in der Weboberfläche bestätigt. Die Meldung
„an MQTT übergeben“ ist kein Empfangsnachweis. ioBroker mqtt.0 9.3.0 ist als Server
auf Port 1883 erreichbar; neue Objekte sind erlaubt und keine Topics ignoriert.
Nur availability wurde dort gesehen, Tastendaten fehlen weiterhin. Keine
ioBroker-Einstellungen geändert. Alte Discovery-Warnungen stammen von hass-mqtt;
seit Abschalten der IOB-Discovery keine neuen davon beobachtet.

0.1.3: 44 Python-Prüfungen, JavaScript-Anlernprüfung und DOM-Bedienablauf erfolgreich.
Physisches Anlernen, Lautstärke-Halten und tatsächlicher
Empfang auf HA/ioBroker sind nach Installation noch offen. Ältere Abschnitte unten
beschreiben den damaligen Stand.

## USB Extender für Home Assistant 0.1.2

- Ursache des fehlenden Versands im Browser gefunden: Belegung `key:tab`,
  tatsächliche Eingabe `KEY_TAB`. Auf dem Raspi auf `KEY_TAB` geändert und gespeichert;
  die vorige Konfiguration wurde automatisch gesichert.
- Discovery im vorhandenen Brokerplatz **IOB** ausgeschaltet, HA unverändert.
- Nach drei physischen Tab-Tastendrücken zeigte der offene HA-MQTT-Explorer
  genau drei Nachrichten unter `ugso/usbhub/1/event/...`, Payload mit
  `control: KEY_TAB`, `event_type: press`, `value: 1`.
- 0.1.2 normalisiert Tastenkennungen, bietet Discovery ausdrücklich als Aus/HA-Auswahl,
  räumt bekannte eigene Discovery-Ankündigungen auf und zeigt MQTT-Ziele sowie Sendestatus.
- 35 lokale automatisierte Prüfungen und die vollständige Linux-CI erfolgreich:
  [Prüflauf für 49a96c0](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/44894647551).
  Installation des neuen Pakets auf dem Raspi steht noch aus.

Der zusätzliche lokale Browsertest der neuen Oberfläche wurde von der
Computersteuerung wegen nicht verlässlich bestimmbarer Browser-URL abgebrochen.
Der vorherige Live-Nachweis im MQTT Explorer bleibt bestätigt.

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
