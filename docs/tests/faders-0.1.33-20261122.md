# Lokale Prüfung 0.1.33 – 22. November 2026

Vor Änderungen alle von Git erfassten und nicht ignorierten neuen Quelldateien
inklusive uncommittetem 0.1.32-Stand außerhalb des Repos gesichert; ZIP-CRC geprüft.
Keine vorhandenen USB-Extender-Einstellungen oder Kopplungsdaten geändert. Kein Zugriff auf .112,
.193 oder andere Remotehosts im Rahmen dieser Änderung.

## Geprüfte Fälle

- Gesamtlauf `python -m unittest discover -v`: 217 Tests in 100,549 Sekunden,
  erfolgreich. Alle zehn Node-/DOM-Prüfungen, JavaScript-Syntaxprüfung und
  `git diff --check` erfolgreich. Python-Wheel 0.1.33 erfolgreich gebaut.

- Alle fünf Streifen jeweils aufwärts/abwärts, Zwischenwert 50, Endwerte 0/100.
  Seitliches Kreuzen mehrerer Streifen bleibt beim ursprünglich gewählten Regler.
- Grenzen 0/20/40/60/80/100 Prozent und außerhalb liegende Rohwerte sicher begrenzt.
  Reine Horizontalbewegung ohne Reglerwert. Abheben und Neuberühren wählt neu.
- Raten 1/5/30/s, letzter ausstehender Wert und optionales X/Y. Mehrfinger, Klick,
  SYN_DROPPED und Moduswechsel verwerfen ausstehende Werte. Kein Tipp nach Schieben.
- Deaktivierter Regler sendet nicht. Rückschalten aktiviert wieder die bisherigen
  Richtungsaktionen und unterdrückt Reglerwerte.
- Konfiguration speichern/neu laden und zurückschalten erhält eigene Regler-,
  Richtungs- und X/Y-Topics. Ungültige Modi, Reglernummern, Datentypen, Wildcards
  und kollidierende aktive Topics werden abgewiesen.
- Drei Paho-Verbindungen zu lokalen Testbrokern: alle fünf Regler liefern identische
  reine Zahlen ohne Retain. Geräte-Zielauswahl gilt. Anlernmodus unterdrückt Werte.
- HA-Discovery: fünf Regler plus X/Y am selben Gerät, keine Anmeldungen am Broker
  ohne Discovery. Richtungs- und zugehörige Tastenauslöser-Anmeldungen verschwinden
  im Flächenmodus. Rückschalten entfernt Regler und stellt bisherige Sensor-IDs her.
- Web-/DOM-Prüfung: beide Modi, gesperrte Einstellungen des pausierten Modus,
  graue Richtungsbelegungen, Erhalt eigener Topics, Vorschauhinweis, Reglerfüllstand
  und letzter Trigger. Farbliche Unterscheidung auf 1280 und 390 px visuell geprüft;
  kein horizontales Überlaufen und keine JavaScript-Seitenfehler.

## Grenzen

### Ergänzende Empfangsprüfung nach Nutzerinstallation

Am 22.11.2026 zeigt die Oberfläche auf .112 Version 0.1.33 und gespeicherten
Flächenmodus. Alle fünf Regler und das IOB-Ziel sind aktiv. Eigene X/Y-Topics
T650-X und T650-Y weiterhin vorhanden. Zuletzt angezeigte Reglerwerte:
98, 98, 85, 3, 8. ioBroker .116:8081 zeigt dieselben fünf Werte als Datenpunkte:
`mqtt.0.t650-touchpad.fader-1.value` bis `mqtt.0.t650-touchpad.fader-5.value`.
Objektansicht nach `mqtt.0.t650-touchpad.fader` gefiltert und aufgeklappt.
Keine Werte, Topics oder Geräteeinstellungen geändert. Reiner Empfangsnachweis;
keine kontrollierte neue Gestenfolge und keine HA-Reglerprüfung.

Während der Implementierung keine Hardwareprüfung, kein Test mit echtem HA und
kein vom Agenten ausgeführtes Update auf dem Pi. Die
erfolgreichen T650-/HA-Prüfungen von 0.1.32 betreffen den Richtungsmodus. Der neue
Flächenmodus muss nach Freigabe separat am echten T650 und HA praktisch geprüft
werden. Nichts veröffentlicht, keine Änderungen an Doku-Domains oder GitHub.
