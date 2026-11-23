# Offene Schritte

## USB Extender Cards – ein gemeinsames Home-Assistant-Kartenpaket

- Eine eigenständige Custom Card, wählbarer Mushroom-/Bubble-Stil, gemeinsam als
  Paket ausliefern. Keine Voraussetzung einer zusätzlichen Mushroom-/Bubble-Installation.
- Webfrontend öffnen: beim Klick Wartetab gegen Popupblocker öffnen, ON senden,
  auf aktuelle bestätigte Erreichbarkeit warten, dann URL laden. Zeitlimit,
  Fehleranzeige und Browser-/Tabletprüfung vor Veröffentlichung.
- Webbetrieb, Web-Autostart, Backup, Offline-/Start-/Fehlerzustand anzeigen und
  steuern. Konfigurierbare URL und HA-Entitäten der MQTT-Discovery verwenden.
- Erst nach fertiger Veröffentlichung Downloadlink im Systembereich ergänzen.
  Dort steht bis dahin ausdrücklich „geplant / noch nicht verfügbar“.

## MQTT-Systemsteuerung 0.1.37 – zusätzliche Praxisprüfung

- Auf freigegebenem Raspi nach Sicherung: Web Start/Stop, enable/disable und
  Neustart prüfen. Rückmeldung ON erst bei HTTP-Erreichbarkeit, USB/MQTT weiter aktiv.
- HA-Discovery mit zwei Schaltern, Backup-Button und Statussensoren praktisch
  prüfen; CLI-Änderungen, MQTT-Reconnect, Fehlerfall, behaltene Kopplungen.
- Eingebauter Linux/systemd-Smoke-Test für den isolierten CI-Runner; dessen echter
  Diensttest ist durch lokale Windows-Mocks nicht ersetzt.

## Scanner: ergänzende Praxisprüfungen

- Ergänzend zum bestandenen Barcode-/QR-/HA-Tag-Test: Neustart, Abschalten,
  US-Layout und alternative Abschlusszeichen am echten Scanner prüfen.
  Metadatenvergleich nur nachholbar, falls die
  ursprünglich geprüfte, am bisherigen Pfad fehlende Sicherung wieder verfügbar ist.
- Bei Gelegenheit UI-Gerätezuordnung korrigieren: Die Auswahl eines vorhandenen
  Zielgeräts setzt die globale Ungespeichert-Markierung und blockiert damit
  „Zuordnung übernehmen“. Im Scanner-Praxistest beobachtet, keine Zuordnung
  übernommen und keine Serverkonfiguration dadurch geändert.
- Serielle Scanner, GS1-Steuersequenzen und zusätzliche Layouts bleiben außerhalb
  der bisherigen Umsetzung.

## 0.1.34: Gamepad praktisch prüfen (lokal umgesetzt)

- Nach Freigabe auf .112 im Analogmodus: beide Sticks, Enden und Mitte, Senderate,
  Achsenabschaltung, L1/R1/L2/R2 und Stick-Klicks mit bestehendem Anlernmodus.
- HA auf dem freigegebenen Testsystem: vier Sensoren, Live-Empfang, Abschalten und
  Neustart sowie unveränderte T650-/Mobile-Funktionen prüfen.
- Weitere Gamepads benötigen eigene gemessene Profile. ABS_Z bleibt ausgeschlossen;
  analoge Trigger und neue Steuerkreuz-Aktionen sind nicht Teil dieser Umsetzung.

## 0.1.33: Nach Freigabe praktisch prüfen

- Fünf Regler am echten T650: Aufsetzen in jedem Streifen, vertikale Werte, seitliches
  Verrutschen, Abheben/Neuwahl, Empfindlichkeit und Senderate.
- Auf .193 Moduswechsel und HA-Discovery praktisch prüfen: fünf Regler statt acht
  Richtungswerten, X/Y unabhängig, Rückschalten mit bisherigen IDs und Topics.
- Live-Farben und Füllstände am echten Gerät prüfen. Lokal auf Desktop/Mobil geprüft.

## 0.1.32: Noch ausstehende Praxisprüfung

- Ergänzend nach Bedarf: kurze Wege, Richtungswechsel und praktische Senderate
  systematisch vergleichen; alle acht Live-Werte sowie X/Y-Empfang auf .193 bestätigt.
- Entfernung nach Abschalten und erneute Anmeldung nach Neustart am echten HA
  prüfen. Sensorzuordnung und Live-Empfang aller zehn Werte auf .193 abgeschlossen.

## Nach abgeschlossener isolierter T650-Messung

Die acht Richtungen, Tippunterdrückung, X/Y und drei lokale MQTT-Ziele sind am
echten T650 geprüft. Live mit Empfindlichkeit 5/Rate 10, weitere Werte per Replay.
Ergebnis und Grenzen: [Prüfbericht](docs/tests/t650-0.1.31-20261122.md).

- Nach Bedarf separat: sämtliche Empfindlichkeiten/Raten in der laufenden
  Weboberfläche umschalten und neue physische Aufnahmen vergleichen. Dieser
  Live-Umschalttest ist durch Replay nicht ersetzt.
- Einzelne benachbarte Richtungsereignisse wurden protokolliert. Eine optionale
  Richtungsstabilisierung erst bei entsprechendem Nutzerwunsch untersuchen.
Die anschließend beauftragte Installation von .31 auf .112 ist abgeschlossen:
beide Dienste laufen, keine Neustarts, Mobile aktiv, fünf Metadaten-Prüfsummen
unverändert. Die Veröffentlichung von 0.1.31 ist anschließend beauftragt.

## 0.1.29: Nächste Praxisprüfung (lokal umgesetzt)

- Weitere T650-Mehrfingergesten und erneutes Einstecken praktisch prüfen.
  Ein-Finger-Slides und die vorhandene HID++-Kennung sind inzwischen nachgewiesen.
- Schrittfilter 1–5 mit Vol+/Vol−, Helligkeit und Tastaturlicht sowie gehaltenen
  Tasten praktisch prüfen. Pro Taste getrennte Zähler und Stopp beim Loslassen.
- USB-Hub/Portwechsel, explizite Offline-Zuordnung und Entfernen praktisch prüfen.
  Mobile-Deck entfernen und Vertrauen separat widerrufen, andere Geräte erhalten.
- Neues ZIP erst nach Freigabe auf .112 installieren. Noch nichts veröffentlichen.

## Als Nächstes: Praxisprüfung auf dem Raspberry Pi 4

- 0.1.26 auf echtem Handy/Tablet oder physischem Deck prüfen: eigene Seiten,
  fortlaufende Nummern, Vor/Zurück/Home ohne MQTT-Aktion, Zähler, neue Seite und
  bestätigtes Löschen (Seite 1 geschützt). IDs/Topics übriger Seiten, Rückmeldungen
  und erneute Verbindung prüfen. Lokale GUI-/Protokolltests sind abgeschlossen.

- Nach Nutzerfreigabe: 0.1.24-Auswahl mit großer Bibliothek auf dem Pi testen;
  erstmalige/wiederholte Miniaturen, Suche, Paketwechsel und Speicherung prüfen.
  Lokale 6.862-Einträge-/Cache-Prüfung ist abgeschlossen; .112 blieb unverändert.

- 0.1.23 bleibt lokal: MDI-Farbsets später nach Nutzerfreigabe als Open-Source-
  Downloads veröffentlichen. Bis dahin nicht auf .112 importieren. Zuordnung von
  normal/gedrückt beziehungsweise MQTT-Rückmeldung später mit ausgewähltem Set prüfen.

- Nach Ende des laufenden Imports: 0.1.22 auf dem Pi prüfen, großes reales Paket
  mit einem Indexcommit, Vorschauen bei Bedarf und Erhalt vorhandener Tastenzuordnungen.

- 0.1.18 auf dem Pi praktisch prüfen: Paketimport mit Originalnamen/Unterordnern,
  Suche und Hover, GIF/WebP normal und gedrückt, statische Ruhe und Speicheranzeige.

- Gedrückte Tastengestaltung 0.1.16 auf echtem Deck/Tablet prüfen: zweites Icon,
  Text-/Hintergrundfarbe und Rückkehr beim Loslassen; im Leerlauf keine Bildwiederholung.

- Experimentellen Mobile-Server 0.1.15 mit echter Android-App 2.1.2 weiter prüfen:
  Rot/Blau korrekt, ruhige Iconanzeige und stehende Versandzähler ohne Änderungen,
  alle automatischen Tastenkanäle nach Freigabe/Speichern, Übernahme des Android-
  Rasters und dauerhaften Offline-Editor prüfen; fünfsekündigen Keepalive gegen
  den gemeldeten Receive-Timeout praktisch nachtesten,
  Iconfarben/-größe und MQTT-Tastendruck,
  App-eigene Rastergrenzen und erneute Verbindung nach Pi-/App-Neustart.
- Androidseitiges Löschen virtueller Decks und optionale Shortcut-Befehle
  erst nach dem grundlegenden Mobile-Praxistest ergänzen.

- Gespeicherte Tasten nach einem Pi-Neustart und USB-Wiederanstecken praktisch prüfen.
- Press/Release, Plus-Rücksetzung und Switch ON/OFF praktisch prüfen; Lauter/Leiser
  halten und kontrollieren, dass die Wiederholung beim Loslassen stoppt.
- Switch als Umschalter, separaten Tastenzustand und Klick/Doppelklick/Hold per
  physischer Taste prüfen. App-Neustart mit gesetztem Switch praktisch nachtesten.
- Breite gruppierte Tastenliste zusätzlich auf Tablet prüfen; Desktop-Nutzerbilder liegen vor.
- Ein konkretes Stream-Deck-Modell prüfen: Erkennung, Freigabe,
  Drücken/Loslassen/Halten, Icons und Helligkeit.
- Neuen Stream-Deck-Tab 0.1.6 praktisch prüfen: richtiges Modellraster, Gestaltung
  auf dem Gerät, MQTT-Zuordnung/-Rückmeldung, Abziehen/Wiederanstecken und Neustart.
- Weitere Medientasten prüfen, insbesondere Play/Pause und Titelsprung.
  Tastatur press/release sowie Lautstärke− und Stumm wurden bereits live bestätigt.
- USB-Geräte abziehen/wieder anstecken, den Pi neu starten und die gespeicherten
  Belegungen sowie MQTT-Wiederverbindung prüfen.
- Drei Broker sind im Nutzeraufbau online sichtbar. Ausfall eines Brokers und
  Wiederverbindung praktisch prüfen, außerdem HA-Display-Rückmeldungen testen.
- HA-Binärsensor für den Switch-Zustand sowie gefilterte Press/Release-Auslöser
  einschließlich der separaten Plus-Kanäle unter einem benannten USB-Gerät
  mit Discovery praktisch prüfen. IOB-Discovery bleibt aus: hass-mqtt meldete
  `device_automation` als nicht unterstützt.
- Webdienst per CLI beenden und bestätigen, dass die Geräte weiterarbeiten und
  Port 8098 geschlossen ist. Anschließend erneut starten.
- Ein tatsächlich verwendetes Marketplace-Iconpack mit eigener gültiger Lizenz
  importieren; Bericht auf nicht unterstützte SVG-/Archivvarianten prüfen.

## Mögliche Erweiterungen nach der Praxisprüfung

- Zusätzliche Profile für Stream Decks; Deck-Seiten sind bereits implementiert.
- Gestaltbare Stream-Deck-Plus-Touchscreen-Anzeigen.
- Weitere USB-Adapter anhand konkret vorhandener Geräte, zum Beispiel serielle
  Bedienelemente. Eine allgemeine USB-Erkennung ersetzt keine Protokollanbindung.
- Eigenständiges Tablet-Deck als separater Dienst. Dafür muss eine Oberfläche
  während der Tablet-Nutzung erreichbar bleiben; Stream Deck Mobile wird dadurch
  nicht automatisch mit dem Pi kompatibel.

Erledigte Implementierungsschritte stehen im Changelog und nicht als offene Aufgaben hier.
