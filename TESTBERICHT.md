# Prüfungen

## 0.1.37: MQTT-Systemsteuerung (lokal)

- Vollständige Suite: 250 Python-Tests erfolgreich. Abschließende gezielte
  Systemsteuerungstests nach Detailkorrekturen zusätzlich erfolgreich.
- 14 Node-/DOM-Prüfprogramme erfolgreich; Opt-in/Speichern, Rückmeldungen und
  ausdrücklicher Hinweis „Kartenpaket geplant / noch nicht verfügbar“ geprüft.
- Reale lokale MQTT-Verbindungen, zwei Broker und lokaler HTTP-Server:
  ON/OFF, Autostart, tatsächliche HTTP-Erreichbarkeit, retained Rückmeldungen,
  Backupabschluss und unveränderte Konfiguration nachgewiesen. Systemd-Aufrufe
  sind dabei simuliert, keine Steuerung eines anderen Hosts.
- Helper-Protokoll, Längenbegrenzung, feste Unit-/Befehlsliste, Ablehnung ungültiger,
  retained/duplizierter Befehle, volle Queue und Backup-Deduplizierung geprüft.
- Private, vollständig lesbare Backuparchive mit Konfiguration, Icons und
  Kopplungsdaten; keine Exportrekursion und keine Inhalte im MQTT-Ergebnis.
- Desktop 1280 px / Mobil 390 px mit Headless Edge: System- und Brokeransicht ohne
  horizontale Überläufe oder Seitenfehler; Systemansicht visuell geprüft.
- Isolierter Wheel-Build, Shell-Syntax, Installer-Umask und `git diff --check` bestanden.
  Windows hat hier keinen verfügbaren WSL/systemd-Dienst; der Linux-Helferdienst
  wurde daher nicht real gestartet. CI-Test `tests/management-systemd.test.sh`
  ist vorbereitet und muss vor einer öffentlichen Freigabe auf Linux laufen.

## 0.1.36: USB-Laufwerke und kompakte Anzeige

- 241 Python-Tests erfolgreich, darunter USB-Geräte-/Interface-Klasse und
  Speicherung der Anzeigeoptionen mit unveränderten Bestandszielen.
- 13 Node-/DOM-Prüfprogramme erfolgreich: keine voreingestellten Haken bei neuen
  Laufwerken, gegenseitiger Ausschluss, Auf-/Zuklappen, Speichern/Neuladen und
  gespeicherte Offline-Laufwerke. Andere Geräte und Kopplungsdaten bleiben erhalten.
- Headless Edge bei 1280 und 390 Pixeln ohne horizontalen Überlauf oder Seitenfehler.
  Desktopansicht visuell geprüft: [Beispiel](docs/screenshots/usb-drives.png).
- USB-Klassen simuliert; keine Installation oder Änderung auf .112 für diesen
  Test. Linux-Installer wird zusätzlich durch den vorhandenen CI-Workflow geprüft.

## 0.1.35: Barcode-/QR-Scanner und MQTT-Tags

Anschließend [Praxistest auf .112 / HA .193 abgeschlossen](docs/tests/scanner-live-0.1.35-20261122.md):
native Discovery, Barcode zweimal, Text-QR und HA-Tag-Ereignis nachgewiesen.
Alle vier an drei Broker übergeben; HA-Empfang direkt, ioBroker durch Nutzerbild
bestätigt. Abschluss: beide Dienste aktiv, keine Neustarts/Fehler. Abschließender
Metadatenvergleich wegen nicht mehr vorhandenem Sicherungsarchiv nicht möglich.

[Prüfbericht](docs/tests/scanner-0.1.35-20261122.md): synthetische USB-Tastatur-
Eingaben, drei Loopback-MQTT-Broker, native Tag-Discovery-Nachrichten und lokale
Desktop-/Mobil-Webansicht. Der nachfolgende echte Test ist oben separat dokumentiert.

## 0.1.34: Gamepad-Achsen und normale Tasten (lokal)

Details: [Prüfbericht](docs/tests/gamepad-0.1.34-20261122.md). Synthetische evdev-
Eingaben, temporäre Konfigurationen, drei Loopback-MQTT-Broker und lokale Webansicht.
Die frühere physische Messung bestimmt das Profil; diese Implementierung wurde
noch nicht am echten Gamepad auf .112 installiert oder geprüft.

## 0.1.33: Fünf Regler und sichtbare Modusumschaltung (lokal)

Details: [Prüfbericht](docs/tests/faders-0.1.33-20261122.md). Synthetische Eingaben,
temporäre Einstellungen, drei Loopback-MQTT-Broker und lokale Webansicht. Keine
Remoteprüfung, keine Installation und keine Veröffentlichung.

## 0.1.32: Acht Richtungswerte und HA-Discovery (lokal)

Ergebnisse und Grenzen: [Prüfbericht](docs/tests/slide-values-0.1.32-20261122.md).
Prüfungen verwenden synthetische Eingaben, temporäre Einstellungen und drei
MQTT-Broker ausschließlich auf 127.0.0.1. Kein neuer Test auf .112 oder echtem HA.

## 0.1.28: Seiten und Mobile-Stabilität

- 168 lokale Python-Tests erfolgreich; JavaScript-/DOM-Prüfungen für Seiten,
  Tastenliste, Mobile, Iconbibliothek und Iconauswahl erfolgreich.
- Verschlüsselte Protokolltests für getrennte Geräte, Vor/Zurück/Home/Gehe zu,
  8×8 mit 144×144-Bildern, Erhalt der Topics und keine MQTT-Ausgabe bei Navigation.
- Langsame Bildübertragung simuliert: kleine Pakete lassen den Empfang und
  Heartbeat zwischen den Sendeabschnitten wieder zum Zug kommen.
- [15-Minuten-Praxistest am SM-T580](docs/tests/mobile-0.1.28-15min-20261122.md)
  bestanden: Navigation und Leerlauf, kein neuer Heartbeat-Timeout und keine
  Trennung im Journal. Grenzen und alle Messwerte stehen im verlinkten Bericht.

## Importoptimierung 0.1.22

Gesicherter alter Quellstand gegen aktuellen Stand, jeweils neue temporäre Ablage,
dieselben unveränderten ZIP-Eingaben auf diesem Windows-PC. Einzelmessungen,
keine kontrollierte Raspberry-Pi-Hardwaremessung und keine Laufzeitgarantie.

| Datensatz | Vorher | Nachher | Indexschreibvorgänge vorher/nachher | Vorabrendern nachher |
| --- | ---: | ---: | ---: | ---: |
| Itsyhome, echte 240 PNGs | 4,262 s | 0,395 s | 240 / 1 | 0 |
| Synthetische 6800 unterschiedliche 32×32-PNGs | 458,323 s | 10,464 s | 6800 / 1 | 0 |

Die 6800er-Testdaten sind kein Abbild des unbekannten laufenden Nutzerpakets.
Speicher direkt nach Import: 9.443.441 → 3.604.281 Bytes für den synthetischen
Datensatz; spätere Anzeige erzeugt Cachedateien zusätzlich.

- Unit: Index ein Commit, Metadaten im selben Commit, Originale erhalten,
  bekannte ältere IDs und Einstellungen beim Wiederimport unverändert.
- Simulierter finaler Schreibfehler: vorheriger Index und Einstellungen bleiben
  erhalten. Fehlgeschlagene Vorschau kann ohne Verlust des Originals erneut entstehen.
- Vier parallele Anfragen nach demselben Icon erzeugen genau eine Vorschau.
- Chrome: 20 echte SVG-Dateien aus zwei Ordnerpaketen in einem komprimierten
  Upload, lesbare Namen und Lizenz erhalten; Vorschaurendering erst bei Anzeige.
- Chrome: Animation, Hover und reguläre Deckvorschau funktionieren weiterhin.
- ZIP-Writer mit Python-Standardbibliothek auf UTF-8, CRC und Dekompression geprüft.

## Importfortschritt und Paketmetadaten 0.1.21

- Ordnerupload mit manifest.json: lesbarer Name, technischer Paketordner und Lizenz
  getrennt übernommen; Metadaten nicht als fehlerhafte Bilddateien gemeldet.
- Wiederimport benennt dieselben Originaldateien um, ohne neue Icon-IDs zu erzeugen.
- Fortschrittszähler berücksichtigen unterstützte Bilder und fehlgeschlagene Bilder.
- Status während laufendem Upload abrufbar, nicht angemeldeter Abruf abgewiesen.
- Chrome: echter Itsyhome-ZIP-Upload, Ladebalken sichtbar, mehrere Zwischenstände
  von 20 bis 235 der 240 Icons; danach erfolgreicher Abschluss und Balken ausgeblendet.

## Itsyhome-Import 0.1.20

- Original-ZIP nur lesend in temporäre Testablage importiert: vorher 0 Bilder,
  nach Freigabe von imgs/ 240 Bilder, 14 Unterordner, 0 übersprungen.
- Regressionsprüfung für binäre Plugin-Manifeste und imgs/actions/fan/ ergänzt.
- Keine Plugin-JavaScript-Dateien übernommen oder ausgeführt, Originaldatei erhalten.

## Paketlizenz/Kachelgröße 0.1.19

- DOM: Lizenz einmal pro Paket, keine Lizenzdetails innerhalb der Iconkacheln,
  bestehende Suche/Hover/Paketentfernung unverändert.
- Chrome: 52×52-Kachelgröße, 48×48-Bildfläche, Animation im Hover und kompakte
  Desktop-/Mobilansicht ohne horizontalen Seitenüberlauf geprüft.

## Iconpakete, Animationen und Speicher 0.1.18

- Isolierte Datenkopien: Originalnamen, Unterordner, mehrere Pakete, doppelte Bildinhalte
  mit unterschiedlichen Dateinamen, alter Cache, GIF und animiertes WebP geprüft.
- Bildzeiten und Framewechsel normal/gedrückt; statische Anzeige sendet nicht fortlaufend.
- Reale lokale WebSocket-/NaCl-/LZ4-Verbindung überträgt wechselnde Frames und gedrücktes
  Bild korrekt, Rückkehr nach Loslassen; kein Nachweis am physischen Tablet.
- Browser-Vorschau tatsächlich animiert, Paket-/Unterordnerstruktur aus dem bereitgestellten
  Home-Assistant-Plugin-ZIP, Suchfilter, Hover und schmale Ansicht in Chrome geprüft.
- Paketentfernung nur unbenutzt, vorheriges ZIP-Backup, erhaltene gemeinsame Cachedateien,
  Speicheranzeige und Abweisung bei vollem Laufwerk geprüft.

## Kompakte Tastenliste 0.1.17

- DOM: zunächst geschlossen, Wechsel schließt vorherige Taste, Name aktualisiert
  die Zusammenfassung, geöffnete Taste bleibt bei erneutem Rendern erhalten.
- Bestehende Anlern-, Speichern- und Bearbeiten-Abläufe erhalten.
- Speichern/Abbrechen im Eintrag, Hinweis bei Änderungen und Erhalt anderer
  Tastenedits beim Abbrechen geprüft. Chrome auf localhost: Öffnen/Wechseln,
  Abbrechen, Speichern/Neuladen und Darstellung bei 1440/430 Pixeln erfolgreich.

## Gedrückte Tastengestaltung 0.1.16

- Mit isolierten Testeinstellungen: zweites Icon, Hintergrund- und Schriftfarben,
  Speichern/Neuladen, Press/Release und Rücksetzen nach Trennung geprüft.
- Normaldarstellung und MQTT-Anzeigetext werden beim Loslassen wiederhergestellt.
- DOM-Workflows und echte Chrome-Vorschau auf localhost erfolgreich, einschließlich
  Speichern/Neuladen und schmaler Ansicht ohne Seitenüberlauf.
- Kein Live-Test auf .112; keine dortigen Einstellungen geändert, nichts veröffentlicht.

## App-Raster/Keepalive 0.1.15

103 Python-Tests, alle fünf Node-Prüfungen, Syntax und Diff erfolgreich.
Chrome mit lokalem Testserver: native Rastermeldung aktualisiert 15 auf 24 Tasten,
Textentwurf bleibt erhalten, Offline/Online unverändert stabil; kein X/Y-Element,
Speichern und 390-px-Ansicht ohne Überlauf. Aufnahme `.state/streamdeck-grid-0.1.15.png`.

- Echter WebSocket mit unabhängiger Gegenstelle und 10-Sekunden-Empfangswächter:
  16,2 Sekunden ohne Datenpakete, mindestens drei leere Pings und bestätigte Pongs;
  kein Receive-Timeout, keine neuen Bilder/Contexts, Tastendruck danach erfolgreich.
- App-Raster 5×3 → 6×4 → 4×6 ohne Listener-/Verbindungstausch. Altes mobile_layout
  bleibt gespeichert und wird ignoriert. Offline-Geometrie/Vertrauen nach Neustart
  erhalten, erneute App-Meldung überschreibt den alten Stand.
- DOM: keine X/Y-Übersteuerung, App-Raster trotz gespeichertem 8×8 korrekt; natives
  Rasterupdate lässt dasselbe Eingabefeld und den Textentwurf bestehen.
- Der Nutzer bestätigte receive timeout auf dem Tablet. Erneuter echter Android-
  Dauertest mit dem korrigierten Keepalive steht noch aus.

## Offline-Editor/Raster 0.1.14

102 Python-Tests, alle fünf Node-Prüfungen und Diff-Prüfung erfolgreich.

- Chrome mit isoliertem lokalem Testserver: Offline/Online wechselt nur Hinweis;
  identische Editor-DOM und ungespeicherter Text bleiben bestehen. X+1/Y+1 ergibt
  24 statt 15 Tasten, Speichern erhält den Text. 390-px-Viewport ohne Überlauf.
  Aufnahmen `.state/streamdeck-offline-0.1.14.png` / `streamdeck-grid-0.1.14.png`.
- DOM: Tab auch ohne verbundenes Gerät sichtbar, Auswahl und Editor bleiben bei
  Trennung, Dienstpause und Wiederverbindung erhalten. Gespeichertes Raster nach
  erneutem Laden offline angezeigt.
- WebSocket: optionale Shortcut- und zukünftige Erweiterungsnachricht beendet
  Sitzung nicht; Fehlerantwort für nicht unterstützte Anfrage, Tastendruck danach
  weiterhin empfangen und keine zusätzliche Context-Aktualisierung.
- Gespeichertes 4×6-Raster gewinnt vor Tablet-Meldung, Listener bleibt gleich.
  Bekanntes Deck offline nach Trennung und Serverneustart erhalten; erneute
  Verbindung mit gespeichertem Vertrauen und 24 Tasten erfolgreich.
- Die Ursache der echten Tablet-Trennungen bleibt ohne neues Geräteprotokoll
  unbestätigt; lokale Fehlerpfade und UI-Neuaufbau sind korrigiert.

## Mobile-Farben/Topics 0.1.13

100 Python-Tests sowie alle fünf Node-/DOM-Prüfungen erfolgreich; Diff sauber.

- Verschlüsselte LZ4-Übertragung: BGRA-Bytes und dekodierte RGB-Pixel geprüft.
- Wiederholte gleiche Konfiguration/Refresh: keine Pakete und unveränderte Bild-
  sowie Context-Zähler. Änderungen/Resize/Decköffnung übertragen nötige Daten.
- Automatische Tastenkanäle: elf Topicarten, mehrere Geräte mit gleichem Namen,
  eigene Topics/ausgeschaltete Kanäle und Speicherung/Neuladen erhalten.
- Web-API ergänzt 15 Tasten nach Freigabe, keine Duplikate beim zweiten Speichern;
  vorhandene MQTT-Zugangsdaten erhalten.
- Mobile-Tastendruck über echtes lokales WebSocket/Core/MQTT: Press, Release,
  Umschalter ON, Tastenzustand OFF, Button/Klick und Plus-Leerrücksetzung empfangen.
- DOM: automatische Zeilen, lesbare Topics, bestehende Einzelaktionen erhalten.
- Kein eigener Tablet-Livetest: Farben, ruhiges Bild und Kanäle dort nachprüfen.

## Mobile-Handshake 0.1.12

97 Python-Tests und alle fünf Node-/DOM-Prüfungen erfolgreich; Syntax und Diff sauber.
Ein bestehender Discovery-Test wartete nur auf „online“, nicht auf die drei
initialen MQTT-Ankündigungen, und mischte alte/neue Gerätenamen. Seine Warte-
bedingung korrigiert; keine Änderung am MQTT-Produktionscode. Erneuter Gesamtlauf grün.

- Echtes lokales WebSocket: Hello.version erfüllt Desktop-Mindestversion 6.3,
  echte Extender-Version bleibt getrennt in osVersion vorhanden.
- Text „Licht ÄÖÜ 42“ oben/mittig/unten in 8/32 px: aktualisierte Icons empfangen,
  identischer Listener, gleiches virtuelles Gerät und gespeichertes Vertrauen;
  anschließender Tastendruck weiterhin empfangen.
- Keine Behauptung eines erfolgreichen erneuten Android-/Pi-Livetests.

## Iconimport 0.1.11

- DOM: einzelne/mehrere Icons, Ordner mit Unterordnern, Sammlungsname, übersprungene
  Fremdformate/defekte Bilder und Größenlimit vor Upload geprüft.
- HTTP: Bild abrufbar, Sammlung gespeichert, wiederholter Import ohne Duplikat,
  ungültiger Sammlungsname abgewiesen und Konfiguration unverändert.

## Icon-Aktualisierung 0.1.10

96 Python-Tests und alle vier Node-/DOM-Tests erfolgreich; git diff --check sauber.
Gerenderte Textpositionen optisch geprüft (`.state/text-position-0.1.10.png`).

- Textbereich oben/unten, unveränderte mittige Überlagerung, vollflächiger
  Hintergrund und Icon ohne Text: Pixeltests für contain/cover in 32/72/144 px.

- Echter lokaler verschlüsselter WebSocket: sechs initiale Icons, zehn identische
  Größenmeldungen ohne Refresh; erneuter allgemeiner Refresh ohne Bildpakete.
- Eine Hintergrundänderung: genau ein Icon, LZ4-Pixelwerte geprüft. Erneuter
  Refresh ohne Daten. Echte Größenänderung: alle sechs Icons in neuer Größe;
  erneute Decköffnung: vollständige Übertragung wieder möglich.
- Nutzer bestätigt importiertes Icon auf dem Android-Tablet; kein eigener neuer
  Pi-/Android-Livetest. Rasterabweichung weiterhin praktisch nachzuprüfen.

## Raster/Verbindung 0.1.9

94 Python-Tests erfolgreich; Stream-Deck-, Mobile- und Anlern-DOM sowie Diff-Prüfung erfolgreich.

- Gemeldetes Tablet-Raster 5×3 führt zu 15 Editor-Tasten, 3 Zeilen hoch/5 Spalten
  breit. Adapter, Inventar und Context verwenden dieselben Abmessungen.
- Servervorgabe ändern behält denselben Listener und dieselbe Client-Verbindung;
  geöffnete Decks müssen nicht neu ausgewählt werden. Clientgemeldete Raster haben
  Vorrang. Auch spätere Tablet-Updates werden ohne Verbindungstrennung übernommen.
- Regression für Context-Timing direkt nach OpenVirtualDevice: Änderung geht
  nicht mehr durch nachträgliches Zurücksetzen der Sendemarkierung verloren.
- DOM: neuer Mobile-Client öffnet Editor automatisch, schmutziger Entwurf verhindert
  Umschaltung bis zum Speichern. Kein wiederholtes Zurückspringen beim Navigieren,
  keine automatische MQTT-Aktivierung.
- Chrome mit echter lokaler WebSocket-Gegenstelle: automatische 15-Tasten-Ansicht,
  Vorgabe auf 4×4 ändern, Tablet-Raster bleibt 5×3, Verbindung und Deck bleiben offen.
  Prüfaufnahme `.state/mobile-auto-editor-5x3.png`. Kein neuer Test auf .112.

## Kopplungsbestätigung 0.1.8

91 Python-Tests erfolgreich; Mobile-DOM, JavaScript-Syntax und Diff-Prüfung ohne Befund.

- Nutzerbild belegt in 0.1.7 den wartenden Client SM-T580 ohne Bestätigungsanzeige;
  kein Beleg einer abgeschlossenen Kopplung oder funktionierender Tasten.
- Regression: Client sendet Hello und wartet. Status zeigt nun bereits seinen
  Prüfabdruck und die Bestätigung. Browsercode stimmt mit Client-Schlüssel überein.
- Manuelle Freigabe vor Authenticate liefert die verschlüsselte Geräteliste;
  spätere Anfrage 42 bekommt Ok mit genau dieser ID und anschließend Geräteliste.
- Vorherige Reihenfolge Authenticate → Freigabe weiterhin erfolgreich.
- Ablehnung des Hello-Clients speichert kein Vertrauen und erzeugt keine Eingabe.
  ClientCapabilities vor der Freigabe autorisiert keine Tastendrücke.
- Echter lokaler WebSocket-Client plus Chrome bestätigt den vollständigen Ablauf
  einschließlich des sichtbaren Buttons. Prüfbild `.state/mobile-pairing-fixed.png`.
- Kein neuer Zugriff auf .112 und kein abgeschlossener Android-Praxistest behauptet.

## Mobile-Server 0.1.7 – lokale Protokoll- und Webprüfungen

Gesamtergebnis: 88 Python-Tests sowie Tastenlisten-, Stream-Deck- und Mobile-DOM-
Abläufe erfolgreich. JavaScript-Syntax und Diff-Prüfung ohne Befund.

- Loopback-WebSocket mit unabhängiger PyNaCl-Box-Gegenstelle: Klartextbegrüßung,
  gemeinsame Schlüssel, verschlüsselte Anmeldung und Web-Bestätigung.
- QR-Bild ist ein lesbares PNG; Server-ID und Adresse/Port entsprechen den
  konfigurierten Werten. Kein echter Kamerascan durchgeführt.
- Unbekannter Client bei geschlossenem Fenster abgelehnt. Ablehnung und manipulierte
  Pakete erzeugen keine Eingaben. Nachrichtenlimits und Größenbegrenzung implementiert.
- Virtuelles Deck öffnen, Hardwareadapter nutzen, sechs Icons empfangen und LZ4-
  Bilddaten pixelgenau gegen die konfigurierte Farbe prüfen.
- Verschlüsselter Tastendruck führt über Core und Paho zum lokalen MQTT-Testbroker:
  `probe/mobile/press` mit Nutzdaten `ON`. Doppelte Press-Nachricht wird unterdrückt;
  Loslassen und Trennung werden weitergegeben bzw. Zustände zurückgesetzt.
- 15 Server-Tasten ohne gesetztes Pro-Flag mit Simulator geprüft; keine Aussage
  über die sichtbare Tastenanzahl in der tatsächlichen Android-App.
- Serverneustart erhält Schlüssel, Vertrauen und Deck-ID. Ausschalten schließt den
  Port und Client, erhält Vertrauen und beendet nicht den USB-/MQTT-Prozess.
- Echter separater Core-Prozess und HTTP-Weboberfläche: Aktivierung speichern,
  Status aktiv, QR abrufen, Anfrage erlauben, deaktivieren; MQTT-Passwort/Hub-ID erhalten.
- Chrome Desktop 1440 px und Mobil 430 px: Aktivierung, echter QR-Code, Deaktivierung,
  keine Browserfehler und kein horizontaler Seitenüberlauf. Prüfaufnahmen lokal unter
  `.state/mobile-server-desktop.png` und `.state/mobile-server-phone.png`.

Grenze: Alle neuen Laufzeitnachweise sind lokal mit einem Protokollsimulator.
Keine Installation auf Pi/Android, kein Test mit der laufenden Elgato-App, keine
vollständig bestätigte Android-Interoperabilität und keine neue Veröffentlichung.

## Stream-Deck-Tab 0.1.6 – lokal, simulierte Geräte

Ergebnis: 72 Python-Tests erfolgreich, beide DOM-Abläufe und Tastenlisten-Test
erfolgreich, JavaScript-Syntax und `git diff --check` ohne Befund. Chrome-Prüfung
mit echtem lokalem HTTP-Server und temporärer Konfiguration ebenfalls erfolgreich.

- Vorherige Quell- und lokale Einstellungsstände vollständig gesichert; nur
  temporäre Konfigurationen und lokale Testserver verwendet.
- Mini-Raster aus Treibermetadaten; MK.2 mit 15 Tasten im echten Chrome geprüft.
- Tab ohne Gerät verborgen, bei Anschließen sichtbar, bei Abziehen und inaktivem
  Dienst wieder verborgen. Gestaltungsdaten bleiben erhalten. Pedal ohne Bildeditor.
- Beschriftung, Hintergrundfarbe, Icon und zusätzliche MQTT-Aktion gespeichert;
  nach Neuladen wieder vorhanden, bestehendes MQTT-Topic und Payload unverändert.
- Preview-API erfordert Anmeldung, ändert keine Konfiguration und liefert dieselben
  Pixel wie der Hardware-Renderer. Übergrößen, ungültige Farben und Bild-IDs abgelehnt.
- Hintergrund/Alpha und Text in nativen BMP-Tastendaten geprüft; Neuladen rendert
  auch unbelegte Tasten neu. MQTT-Zustand wählt aktives bzw. gestaltetes Basis-Icon;
  Nachrichten eines nicht zugeordneten Empfangsbrokers werden nicht dargestellt.
- Chrome Desktop 1440 px und Mobil 430 px ohne seitlichen Seitenüberlauf.
  Lokale Prüfaufnahmen unter `.state/streamdeck-desktop.png` und `streamdeck-mobile.png`.
- Keine physische USB- oder Pi-Prüfung: die Geräte wurden simuliert. Kein Live-
  Nachweis neuer Stream-Deck-Funktionen oder einer bestimmten Modellkompatibilität.

## Nutzerbilder 0.1.5 – Praxisempfang bestätigt

Neun vom Nutzer gelieferte Screenshots zeigen die installierte 0.1.5 und die
breite Oberfläche, drei online gemeldete Brokerplätze, USB-/Anlerneinstellungen,
Ereignisübergaben und die tatsächlichen Anzeigen in HA/ioBroker. In ioBroker sind
einzelne Topics mit press, release, click, hold, ON und OFF erkennbar. Plus-Kanäle
werden leer zurückgesetzt (im gezeigten Adapter als null). HA zeigt getrennte
Switch- und Tastenzustand-Sensoren mit Werten nach der Betätigung.

Damit ist der vorher fehlende ioBroker-Empfang für die gezeigten Topics bestätigt.
Keine neue Agenten-Liveprüfung und kein vollständiger Nachweis aller drei Broker,
aller Gesten oder Neustarts. Die Screenshots beweisen keinen physischen Stream-Deck-Test.

## 0.1.5 – Umschalter, Button-Gesten und breite Liste

61 Python-Prüfungen und beide JavaScript-Prüfläufe lokal erfolgreich.

- Reale Paho-/TCP-Verbindungen zu zwei isolierten MQTT-Testbrokern: Switch
  liefert ON beim ersten Druck und OFF beim zweiten. Loslassen und native
  Wiederholungen toggeln nicht. `/state` liefert parallel ON/OFF bei Drücken/Loslassen.
- App-Neuinitialisierung und neue MQTT-Verbindungen lesen den gespeicherten
  Switch-Wert zurück; der nächste Druck schaltet korrekt weiter. Konfiguration bleibt gleich.
- Klick erst nach Doppelklick-Fenster; Doppelklick ohne Einzelklick, Hold einmalig
  ohne Klick beim Loslassen. Verspätete zweite Klicks, gehaltene zweite Betätigung,
  native Repeat-Ereignisse, unabhängige Geräte und eigene Zeitwerte geprüft.
- `/button`, `/button-plus` und einzelne Gesten-Topics liefern einfache Werte.
  Button+ wird leer zurückgesetzt; keine Datenmeldung retained.
- Anlernmodus und bekannte Geräteverluste verwerfen wartende Gesten, ohne den
  gespeicherten Switch umzuschalten.
- 15 Discovery-Komponenten einer voll aktivierten Taste (13 Geräteauslöser,
  zwei Binärsensoren) mit einer Gerätekennung; Type/Subtype-Paare eindeutig.
- DOM-Ablauf prüft neue Topicvorgaben, Speichern und echte CSS-Regel für die volle
  Breite. Syntaxprüfung und `git diff --check` erfolgreich.

Kein physischer Pi-/HA-/ioBroker-Nachtest und keine visuelle Browserabnahme der
neuen Fassung. Die Discovery-Auslöser verwenden die dokumentierten
[HA-Geräteauslöser](https://www.home-assistant.io/integrations/device_trigger.mqtt/).

## 0.1.4 – Lesbare Topics und Gerätezuordnung

47 Python-Prüfungen und beide JavaScript-Prüfläufe lokal erfolgreich.

- Namen mit Umlauten, gleichen Schreibweisen und späterer Umbenennung geprüft:
  lesbare Zähler statt Hashes; gespeicherter Topic-Namensraum bleibt stabil.
- Zwei TCP-MQTT-Testbroker empfangen dieselben fünf lesbaren Topics.
  Nur `press-plus` und `release-plus` erhalten anschließend leere Nutzdaten;
  normale Press/Release und Switch bleiben unverändert. Keine Retain-Markierung.
- Discovery für zwei Tasten: acht verschiedene Geräteauslöser und zwei
  Binärsensoren tragen identischen Gerätenamen und identische Gerätekennung.
- DOM-Anlernablauf zeigt die fertigen lesbaren Topics einschließlich der beiden
  Plus-Kanäle bereits vor dem Speichern an und speichert sie unverändert.
- Vorhandene 0.1.3-Belegungen und deren MQTT-Verhalten werden weiter geprüft.

Kein physischer Pi-/HA-/ioBroker-Nachtest dieser Fassung. Referenz für die
Gerätezuordnung: [Home Assistant MQTT](https://www.home-assistant.io/integrations/mqtt/).

## 0.1.3 – Anlernmodus und Tastenliste

44 Python-Prüfungen sowie die beiden JavaScript-Prüfläufe sind lokal erfolgreich.
Syntaxprüfung beider Skripte und `git diff --check` ebenfalls erfolgreich.
Der DOM-Test umfasst auch eine erst beim Beenden sichtbare letzte Taste.

Lokale Prüfung mit isolierten Konfigurationen und TCP-MQTT-Testbrokern:

- Press → ON → Leer-Rücksetzung sowie Release → OFF → Leer-Rücksetzung in der
  richtigen Reihenfolge auf zwei echten Paho-Verbindungen; nichts retained.
- Schnell aufeinanderfolgende Press+-Meldungen haben eine leere Trennmeldung.
- Kanal-/Zeilen-Deaktivierung und individuelle Brokerwahl greifen.
- HA-Discovery enthält ON/OFF-Binärsensor und gefilterte Press/Release-Auslöser.
- Lautstärkewiederholung startet nach dem Zeitlimit und endet beim Loslassen;
  Switch und Release werden nicht wiederholt. Anlernen unterdrückt den Versand.
- Anlernsitzungen benötigen ein freigegebenes Gerät, Fremdsitzungen sind gesperrt;
  abgelaufene Sitzungen pausieren keine Eingaben mehr.
- Speichern/erneutes Laden erhält neue Zeilen, alte Einzelbelegungen und Passwörter.
- Authentifizierter HTTP-Anlernzyklus verändert die gespeicherte Konfiguration nicht.
- JavaScript prüft Sitzungsfilter, Duplikate, bestehende Zuordnungen und Medienvorgaben.
- DOM-Bedientest: Anlernen → Liste → Beenden → Übernehmen → Speichern → Bearbeiten.

Keine physische Prüfung dieser neuen Fassung auf .112 und kein behaupteter
ioBroker-Empfangsnachweis. Das bleibt ein eigener Live-Nachtest.

## 0.1.2 – MQTT-Versand und Discovery pro Broker

**35 lokale Prüfungen erfolgreich.** Zusätzliche lokale TCP-/Paho-Prüfungen:

- Neue Profile starten mit Discovery aus; Daten erreichen trotzdem alle drei Broker.
- Ohne vorherige Discovery werden weder HA-Ankündigungen veröffentlicht noch
  `homeassistant/status` abonniert.
- Ein absichtlich ausgelöster lokaler Discovery-Fehler unterbricht den MQTT-
  Netzwerkprozess nicht; Eingaben erreichen weiterhin alle drei Testbroker.
- Ausschalten auf einem verbundenen Broker nimmt dessen eigene retained Konfiguration
  zurück; die anderen Broker bleiben davon unberührt.
- Nach Wiederverbindung werden alte eigene Konfigurationen anhand des lokalen
  Discovery-Verzeichnisses zurückgenommen; keine neuen Definitionen bei Discovery aus.
- Migration von 0.1.0/0.1.1 über Konfigurationssicherungen ebenfalls geprüft.
- `key:tab` und `key_tab` werden zu `KEY_TAB`, `key:0` bleibt eine Stream-Deck-Kennung.
- Diagnose unterscheidet erfolgreiche MQTT-Übergabe, fehlende Belegung, fehlende
  Ziele und getrennten Broker und enthält die tatsächlichen Topics.

Live auf dem Raspi mit noch installierter 0.1.0:

1. Gespeicherte Belegung enthielt `key:tab`; Eingabetabelle zeigte `KEY_TAB`.
2. Auf `KEY_TAB` korrigiert, gespeichert; automatische Konfigurationssicherung.
3. Discovery nur im Brokerplatz IOB ausgeschaltet und gespeichert.
4. Nutzer drückte dreimal Tab auf der Trust-Tastatur.
5. Offener MQTT Explorer am HA-Broker zeigte genau drei Nachrichten auf
   `ugso/usbhub/1/event/145f-02c9-378b5b8d2956/847173d76d5d524f4a4c0210961fbacf`.

Bestätigte Payload:

```json
{"device":"145f-02c9-378b5b8d2956","control":"KEY_TAB","event_type":"press","value":1}
```

Der Empfang direkt im ioBroker-Broker und das vollständige 0.1.2-Update auf dem
Raspi sind noch nicht bestätigt. Der ioBroker-Brokerplatz wird als online angezeigt.

Die [Linux-CI für 49a96c0](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/44894647551)
ist vollständig grün: 35 Prüfungen, native SVG-Verarbeitung, Installer, systemd,
Webstart/-stopp und ZIP-Erstellung. Ein zusätzlicher lokaler Browsertest der neuen
Discovery-Auswahl wurde von der Computersteuerung abgebrochen, weil sie die
aktuelle URL nicht verlässlich erkennen konnte. Für die neue Oberfläche wird
deshalb kein erfolgreicher visueller Nachtest behauptet.

## 0.1.1 – Tastaturberechtigungen und Statusanzeige

Lokaler Gesamtlauf: **28 Prüfungen erfolgreich**, einschließlich Statusprüfung mit abweichender
PC-Uhr und Vereinheitlichung von evdev-Aliaslisten/-tupeln. Bash- und
JavaScript-Syntaxprüfung erfolgreich.

Auf dem Raspi wurde im angemeldeten Browser festgestellt:

- HCT USB Entry Keyboard, Arduino Micro und Trust Keyboard werden erkannt.
- MQTT-Broker 1 ist online, der Kernprozess läuft.
- Freigegebene Eingabekanäle melden `Permission denied`.
- Nach dem vom Nutzer ausgeführten Befehl zum Sichern, Ergänzen der Gruppe `input`
  und Neustarten des Kernprozesses: neue Prozess-ID, **keine Gerätefehler mehr**,
  MQTT weiterhin online. Keine Belegungen oder Einstellungen geändert.
- Physische Eingaben in der Liveansicht bestätigt: HCT USB Entry Keyboard
  `KEY_LEFTCTRL` mit press/release sowie Volumeregler mit Lautstärke− und Stumm.
- Stumm wurde von 0.1.0 als Alias-Paar angezeigt. 0.1.1 normalisiert dieses Paar
  zu `KEY_MUTE`; der Regressionstest erhält auch bestehende Alias-Zuordnungen.

Die Korrektur für den Installer nimmt die Standardgruppe `input` auf und erhält
sie in der udev-Regel. Die Statusanzeige verwendet die Uhr des Raspi statt der
PC-Uhr. Auf dem Raspi ist während dieser Diagnose noch 0.1.0 installiert.

Auch die [Linux-CI für 9623d8b](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/44892114882)
ist grün: alle 28 Prüfungen, native Bibliotheken, vollständiger Installer und
Dienstprüfung. Zusätzlich konnte das Dienstkonto eine nur für root und die Gruppe
`input` lesbare Testdatei tatsächlich öffnen. Damit ist die Gruppenmitgliedschaft
unter Linux geprüft; der reale Tastatur-Nachtest erfolgte wie oben beschrieben.

![Live-Eingaben nach Ergänzen der Eingabegruppe, Statushinweis noch aus 0.1.0](docs/screenshots/tastatur-live-0.1.0.png)

## Bestätigte Basis 0.1.0

Datum: 21. November 2026. Lokale Windows-Prüfung mit Python 3.13.14.

## Automatisierte Prüfung

`python -m unittest discover -v`

**26 Prüfungen erfolgreich**, lokal und in der Linux-CI, einschließlich
identischer Spiegelung zu mehreren Brokern.

- Konfigurationsversion und genau drei Brokerplätze; Passwort-Hash,
  ausgeblendete Zugangsdaten und Erhalt gespeicherter MQTT-Passwörter.
- Atomare Speicherung und Begrenzung auf zehn Konfigurationssicherungen.
- Zielvorrang Belegung → Gerät → Standard; stabile USB-Identität und Port-Fallback.
- Zuordnung zweier Stream Decks ohne USB-Seriennummer über libusb-Pfade.
- Drei echte Paho-MQTT-Clients über lokale TCP-Verbindungen zu isolierten
  MQTT-3.1.1-Testgegenstellen. Ereignisse erreichen alle drei Ziele ohne retained.
- Festes Sende-Topic an allen drei Brokern: Topic und Payload sind bytegleich.
- Ausfall einer Gegenstelle beeinträchtigt die anderen zwei nicht.
- Fehlerhafte CA-Datei eines Brokers blockiert die übrigen Verbindungen nicht.
- Zustandsabonnement am ausgewählten Empfangsbroker und Wiederholung der
  Discovery nach Home-Assistant-Birth-Nachricht.
- Retained-Discovery-Löschung für eine entfernte Belegung bei verbundenen Brokern.
- Ordnerimport, normalisierte PNG-Ausgabe und Vermeidung identischer Bibliothekseinträge.
- `.streamDeckIconPack`-Testarchiv in offizieller Verzeichnisstruktur mit Namen,
  Tags, Autor und Lizenztext; gefährliche Archivpfade und aktive/externe SVG-Inhalte
  werden abgelehnt. GIF verwendet das erste Bild.
- Native Stream-Deck-JPEG-Aufbereitung mit Icon, Text und Helligkeit an einem
  Testobjekt; ungültige Tastennummer erzeugt keinen Bildauftrag.
- HTTP-Anmeldung, Zugriffsschutz, Fremdursprungs-Abweisung, Konfigurationsspeicherung,
  Iconupload und Sitzungsbeendigung.
- Getrennte Web-/USB-MQTT-Prozesse: Webprozess beendet, dessen TCP-Port geschlossen,
  Kernprozess schreibt weiterhin Status. Kernprozess neu gestartet, gespeicherte
  Gerätezuordnung bleibt erhalten.

Die MQTT-Gegenstellen sind eigene lokale Protokoll-Testserver, kein bestätigter
Test mit Mosquitto oder einer echten Home-Assistant-Instanz.

## Chrome

Lokale Oberfläche `http://127.0.0.1:8098` mit ausdrücklich künstlichen Beispieldaten:

- Anmeldung und vollständige Darstellung der drei MQTT-Karten.
- Tastenbelegung geändert, gespeichert, nach Neuladen vorhanden.
- Dieselbe Belegung erneut geändert und zweimal gespeichert; anschließend
  Speicherzustand wieder grau/deaktiviert.
- Iconbibliothek mit Vorschaubildern, Namen, Sammlung sowie Lizenz-/ID-Details.
- Keine beobachteten Anwendungs-JavaScriptfehler; Browsererweiterungen meldeten
  eigene, nicht aus dieser Anwendung stammende Fehler.

![MQTT-Konfiguration mit lokalen Beispieldaten](docs/screenshots/mqtt-demo.jpg)

![Iconbibliothek mit eigenen Beispielbildern](docs/screenshots/iconbibliothek-demo.jpg)

## Paket und Installer

- Bash-Syntaxprüfung für Installer und CLI-Starter.
- JavaScript-Syntaxprüfung, Python-Kompilierung und Python-Paketinstallation.
- ZIP-Prüfung mit SHA-256-Dateiliste, LF-Zeilenenden und Linux-Ausführungsrechten.
- Keine lokalen Konfigurationen, Passwörter, venv, Git-Daten oder erworbenen Iconpacks
  im Auslieferungspaket.

## Noch nicht bestätigt

- Ausführung des Installers auf Raspberry Pi OS und tatsächliche ARM-Abhängigkeiten.
- Physische USB-/Stream-Deck-Geräte, Hotplug und Stromversorgung am Pi.
- HA-Geräteauslöser und Anzeigezustände mit der tatsächlichen HA-Installation.
- Alle Varianten realer Elgato-Marketplace-Iconpacks sowie Animationen.

## Linux-CI

Die Linux-CI unter Ubuntu 24.04 / Python 3.11 ist erfolgreich:
[Linux-Prüfung für 2432764](https://github.com/rockbaer2007/usb-extender-home-assistant/actions/runs/44889742734).

- Native Bibliotheken und Linux-Python-Abhängigkeiten installiert, einschließlich evdev.
- Gesamttests, echte SVG-Rasterung und ZIP-Erstellung erfolgreich.
- `sudo bash install.sh` auf der isolierten Linux-VM vollständig ausgeführt.
- CLI-Versionsanzeige 0.1.0; USB-/MQTT-Dienst aktiv; systemd-Units geprüft.
- Weboberfläche gestartet und HTML erfolgreich abgerufen; Konfigurations-API
  ohne Anmeldung wie vorgesehen mit HTTP 401 abgewiesen.
- Weboberfläche gestoppt, HTTP-Port geschlossen; USB-/MQTT-Dienst weiterhin aktiv.
- Kernprozess über systemd neu gestartet und danach wieder aktiv.

Der Installationslauf enthält alle 26 Gesamttests und die native USB-Bibliotheksprüfung.
Ein Linux-x86-VM-Test ersetzt keinen Raspberry-Pi-/USB-Hardwaretest.
