# Lokale Prüfung 0.1.32 – 22. November 2026

Vor Änderungen: Git-Quelle 99d5d9f in externem ZIP gesichert. Keine vorhandenen
Geräte- oder Mobile-Einstellungen geöffnet oder umgeschrieben. Alle Testdaten
entstehen in temporären Verzeichnissen; echte Geräte und Remotehosts bleiben aus.

## Geprüft

- Abschließender Gesamtlauf: `python -m unittest discover -v`, 210 Tests in
  96,420 Sekunden erfolgreich. Gesamtlauf nach der Richtungswechselkorrektur erneut
  ausgeführt. `git diff --check` ohne Fehler.

- Acht synthetische Ein-Finger-Wege: Mitte 50 und Endpunkte 0/100 passend zur
  Bewegungsrichtung, keine zusätzliche Tippaktion, keine unerwünschte X/Y-Ausgabe.
- Kurze Wege liefern Teilwerte; 1/5/30 Nachrichten pro Sekunde werden eingehalten.
  Gleiche Werte werden unterdrückt, der letzte ausstehende Wert einmal nachgeliefert.
- Deaktivierte Richtungen senden nicht. Kleine Richtungswechsel senden keine Werte
  auf dem Topic der vorherigen Richtung. Mehrfinger, Klick, SYN_DROPPED und geänderte
  Einstellungen verwerfen ausstehende Werte.
- Konfiguration speichern/neu laden: acht Optionen, eigene und automatisch erzeugte
  Topics erhalten. Unbekannte Richtungen, ungültige Typen/Wildcards und gleiche Topics
  innerhalb der aktivierten Touchpad-Werte werden zurückgewiesen.
- Drei echte Paho-MQTT-Verbindungen zu lokalen Testbrokern: identische reine Zahlen,
  QoS 0 ohne Retain; Zielauswahl, ausgeschalteter Kanal und Offline-Ziel berücksichtigt.
- Core-Weiterleitung und Unterdrückung im Anlernmodus geprüft.
- Zehn HA-Sensoranmeldungen (acht Richtungen + X/Y): eindeutige stabile IDs, dieselbe
  Gerätekennung, eigene State-Topics, Verfügbarkeit und Retain. Broker ohne Discovery
  bekommt Werte ohne Sensoranmeldungen.
- HA-Startmeldung löst erneute Anmeldung aus. X/Y und einzelne Richtung abschalten,
  neu starten sowie Discovery abschalten: eigene Sensoranmeldungen werden entfernt.
- Neun bestehende Node-/DOM-Prüfungen erfolgreich, einschließlich Speichern der neuen
  Richtungs-Checkbox und eines eigenen Topics. Syntaxprüfung erfolgreich.
- Lokales Edge/Playwright: Desktop 1280 px und Mobilansicht 390 px, kein horizontales
  Überlaufen oder JavaScript-Seitenfehler. Screenshots privat unter `.state`.
- Python-Wheel 0.1.32 mit isolierter Build-Umgebung erfolgreich erstellt. Der erste
  Versuch ohne Isolation scheiterte an lokal fehlendem setuptools; kein Produktfehler.

## Ergänzende Praxisaufnahme und Replay auf .112

Die Terminalausgabe wurde am 22. November 2026 ausgewertet. Die Weboberfläche
zeigt 0.1.32, aktiven Dienst und drei verbundene Broker. Die Aufnahme
`t650-results-20261122-164242/report.json` entstand mit dem älteren Prüfskript:
acht Richtungsaktionen erkannt, 128 Slide-Aktionen, 163 X/Y-Paare, keine Tipps in
den acht Slide-Phasen. Separater Tipptest neun Tipps. Drei lokale Broker je 600
identische Nachrichten; X/Y reine Zahlen. Bei UP_RIGHT zusätzlich einmal UP.
Die Rate-Phase enthält keine Ereignisse und wird nicht als erfolgreiche Prüfung
gewertet. Das alte Skript meldet unveränderte Einstellungen.

`tools/t650_replay_values.py` wertete anschließend dieselben Rohdaten auf .112
isoliert aus. Keine Änderung der laufenden Gerätekonfiguration, keine Nachrichten
an konfigurierte externe Broker. Ergebnis
`values-replay-20261122-164727.json`: `passed: true`.

| Richtung | Zahlenwerte | beobachteter Wertebereich |
| --- | ---: | --- |
| UP | 21 | 5–98 |
| DOWN | 17 | 3–92 |
| LEFT | 18 | 1–95 |
| RIGHT | 16 | 6–97 |
| UP_LEFT | 21 | 12–96 |
| UP_RIGHT | 19 | 6–93 |
| DOWN_LEFT | 20 | 4–94 |
| DOWN_RIGHT | 15 | 14–94 |

147 X/Y-Paare und 147 Richtungswerte: drei Broker je 441 identische Zahlennachrichten,
exakt passend zu den erzeugten Ereignissen, ohne Retain. Keine Tipps. Die Bereiche
spiegeln die tatsächlich berührte Fläche wider; 0/100 wurde nicht überall erreicht.
Wiederholte Gesten innerhalb einer Phase sind kein durchgehend monotoner Weg.

Discovery-Zählung `[10, 0, 10]`: je zehn gültige Sensor-Payloads mit eindeutigen IDs,
richtigen State-Topics und derselben Gerätekennung; null am Broker ohne Discovery.
Konfiguration, Switch-Zustände, Mobile-Identität, Vertrauen und Mobile-Geräte blieben
während des Replays anhand ihrer SHA256-Werte unverändert. Dieser Vergleich belegt
den Replay-Datenerhalt, nicht nachträglich den Zustand vor der Installation.

## Live-Sensorprüfung in Home Assistant .193

Am 22. November 2026 um 16:51–16:52 im bestehenden Browser geprüft:
`http://192.168.178.193/config/devices/device/1b19b779014e60767f9e98a7387a7eca`.
Der HA-Connector war nicht verfügbar; Prüfung über die sichtbare Geräteoberfläche.

X/Y bereits vorhanden mit Zahlenwerten. Die acht neuen Werte waren zunächst auf
.112 ausgeschaltet. Nach Einschalten und Speichern aller acht Checkboxen erschien
die erfolgreiche Speichermeldung. save_config sichert die alte Konfiguration vor
dem Schreiben; keine Änderung bestehender X/Y-Topics oder Zielauswahl.

Alle acht Richtungssensoren erschienen per MQTT-Discovery am selben T650-Gerät.
Zunächst unbekannt, da die Werte ohne Retain gesendet werden. Der Nutzer führte
anschließend acht Richtungsbewegungen aus und bestätigte dies. Danach zeigten
alle zehn Sensoren Zahlen; die HA-Aktivität enthielt neue Werte um 16:52:18.

| Sensor | letzter beobachteter Wert |
| --- | ---: |
| Slide DOWN | 2 |
| Slide DOWN LEFT | 7 |
| Slide DOWN RIGHT | 95 |
| Slide LEFT | 2 |
| Slide RIGHT | 92 |
| Slide UP | 98 |
| Slide UP LEFT | 12 |
| Slide UP RIGHT | 95 |
| X | 2 |
| Y | 88 |

Damit sind echte Discovery-Zuordnung und Live-Empfang aller zehn Werte in HA
bestätigt. Die acht Optionen bleiben eingeschaltet. Bestehende Switch-/Tastenzustand-
Entitäten waren weiterhin vorhanden. Prüfung auf .193, keine Browseraktionen auf
anderen HA-Instanzen. Die konfigurierte MQTT-Zielauswahl wurde beibehalten.

## Weiterhin nicht durchgeführt

Keine neue rohe evdev-Aufnahme der zuletzt ausgeführten Live-Gesten. Kein neuer
Neustart oder Abschalttest am echten HA; diese Abläufe sind nur lokal getestet.
Vollständiger Installations-Prüfsummenvergleich noch offen.
Keine Veröffentlichung, kein Push und keine Änderungen an öffentlichen Doku-Domains.
