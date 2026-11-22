# Änderungen

## 0.1.35 – 22. November 2026 (öffentliches Testrelease)

Enthält die zuvor lokalen Zwischenstände 0.1.32–0.1.34: acht Richtungswerte und
X/Y mit HA-Sensoren, fünf alternative Touchpad-Regler sowie Gamepad-Stickwerte.

- Barcode-/QR-Modus für USB-HID-Tastaturscanner, je Gerät ausdrücklich aktivierbar.
  DE/US, Enter/Tab/Scanpause, Text mit führenden Nullen und wiederholten Scans.
- Eigenes MQTT-Topic und native HA-MQTT-Tag-Discovery; HA-Tag-URLs optional als ID.
  Geräte-Zielbroker und individuelle Discovery-Schalter gelten. Keine Retain-Scans.
- Lesbare letzte Scan-Anzeige, Schutz vor unvollständigen/überlangen Eingaben,
  Scanner-Tasten lösen keine normalen Belegungen aus. Bestehende Aktionen pausieren
  ohne Löschen ihrer Einstellungen; Kopplungen bleiben erhalten.
- Echter Aplic-305045-Test bestanden: zwei gleiche Barcodes, Text-QR und HA-Tag-QR
  als vier getrennte native HA-Ereignisse empfangen; Übergabe an drei MQTT-Broker
  und ioBroker-Empfang bestätigt. Beide Dienste aktiv, keine Neustarts oder Fehler.
- ZIP mit SHA256-Prüfsumme, README DE/EN und Dokumentation DE/EN/FR aktualisiert.
  [Praxistest und Prüfgrenzen](docs/tests/scanner-live-0.1.35-20261122.md).

## 0.1.34 – 22. November 2026 (Zwischenstand, enthalten in 0.1.35)

- Opt-in für das gemessene DragonRise-Gamepad 0079:0006: vier Stickachsen mit
  0–100, Mitte 50, Hardware-Totzone, eigener Topic und Ein-/Ausschalter je Achse.
  Senderate 1–30/s je Achse; identische Werte werden nicht erneut gesendet.
- HA-Discovery als vier Sensoren am selben Gerät, Geräte-Zielbroker und jeweilige
  Discovery-Einstellung gelten. Beim Abschalten wird die Anmeldung entfernt.
- L1/R1, L2/R2 und beide Stick-Klicks nutzen vorhandene Tastenfunktionen mit
  unveränderten Linux-IDs und verständlichen Namen beim neuen Anlernen.
- ABS_Z wird verworfen. Keine Startwerte oder Nachsendung an Offline-Broker.
- Vorherige lokale Quellen gesichert; lokale Protokoll-, UI- und Regressionstests.
  Keine Änderung auf .112, keine Veröffentlichung.

## 0.1.33 – 22. November 2026 (Zwischenstand, enthalten in 0.1.35)

- Umschaltbarer Flächenmodus mit fünf senkrechten Reglern, je MQTT-Topic und
  HA-Sensor. Festlegung des Streifens beim Aufsetzen bis zum Abheben; 0 unten,
  100 oben, Empfindlichkeit und Senderate weiter einstellbar.
- Richtungsaktionen/-werte im Flächenmodus pausiert; Belegungen und Topics bleiben
  erhalten. HA-Discovery gleicht den Moduswechsel ab. X/Y bleibt unabhängig.
- Webansicht mit Farben für aktive/pausierte Bereiche, fünf Füllständen, letzter
  Trigger-Markierung und deutlich gekennzeichneter ungespeicherter Modusvorschau.
- Nur lokale Prüfungen und ZIP; keine Remoteänderung und keine Veröffentlichung.

## 0.1.32 – 22. November 2026 (Zwischenstand, enthalten in 0.1.35)

- Acht einzeln aktivierbare Slide-Werte mit eigenen, automatisch vorbelegten oder
  frei einstellbaren MQTT-Topics. Absolute Position 0–100, diagonale Projektion,
  vorhandene Empfindlichkeit und Senderate; standardmäßig deaktiviert.
- HA-Discovery für X/Y und Richtungswerte als Sensoren am selben Gerät, inklusive
  Abgleich beim Neustart und Entfernung deaktivierter Anmeldungen.
- Bestehende Richtungsaktionen, X/Y-Topics, Einstellungen und Kopplungen erhalten.
- Nur lokale Prüfungen und neues ZIP; keine Installation und keine Veröffentlichung.

## 0.1.31 – 22. November 2026 (öffentliches Testrelease)

Enthält auch die zuvor lokalen Zwischenstände 0.1.29 und 0.1.30: Schrittfilter
1–5, eingeklappte Gerätegruppen, stabile/manuelle Gerätezuordnung, bestätigtes
Entfernen sowie Ein-Finger-Slide mit optionalen X/Y-MQTT-Zahlenwerten.

- Echter T650-Test auf dem Raspberry Pi 4 bestanden: alle acht erwarteten
  Richtungen erkannt, keine Tipps in Slide-Phasen. Separater Tipptest: vier Tipps,
  keine X/Y-Ausgabe. Drei Loopback-Broker erhielten je 752 identische Nachrichten.
- Live Empfindlichkeit 5 und Rate maximal 10/s; andere Werte mit denselben echten
  Aufnahmen im Replay geprüft. Zwei benachbarte Richtungsereignisse und einmal
  Halten mitprotokolliert; keine Garantie exklusiver Richtungserkennung.
- Anschließende Installation geprüft: CLI/Dienst 0.1.31, USB-/MQTT und Web aktiv,
  keine Neustarts, Mobile aktiv und keine gemeldeten Fehler. Einstellungen und
  Kopplungen durch fünf unveränderte SHA256-Prüfsummen bestätigt.

- Installer setzt für Programmdateien ausdrücklich umask 022, statt eine
  restriktive Aufruf-Umask zu erben. Sicherungsarchive entstehen weiterhin mit
  umask 077. Verhindert nicht zugängliche venv-Dateien für den Dienstbenutzer.

- Messwerkzeug-Korrektur nach erstem T650-Praxistest: evdev-Puffer durch
  Konsumieren des Generators leeren, mit Zeit-/Ereignisgrenze und sichtbarem
  Messbeginn/Fortschritt. Verhindert Stillstand beim Wechsel zur nächsten Phase.

- Vier diagonale Ein-Finger-Slides zusätzlich zu den vier geraden Richtungen.
  Acht Sektoren zu je 45°, mit bisherigen Grenzwerten und ohne Tipp nach Slide.
- Geführte T650-Hardwareprüfung mit Geräte-/Kennungsprüfung, isolierten lokalen
  MQTT-Brokern, temporären Einstellungen und JSON-Bericht. Vorherige Dienste
  werden auch bei Test-/Berichtsfehlern wieder gestartet. K400/T400 ausgeschlossen.
- [Vollständiger Hardware- und Installationsbericht](docs/tests/t650-0.1.31-20261122.md).

## 0.1.30 – 22. November 2026 (Zwischenstand, enthalten in 0.1.31)

- Ein-Finger-Slide in vier Richtungen als anlernbare Press-/Release-Aktionen;
  keine zusätzliche Tippaktion nach erkannter Schiebebewegung.
- Je Gerät Empfindlichkeit 1–10 und Senderate 1–30/s, standardmäßig 5 und 10/s.
- Optionale absolute X/Y-Werte 0–100 auf getrennten, anpassbaren MQTT-Topics.
  Standard aus; reine Zahlen an die Geräte-Zielbroker, kein JSON/Retain/Replay.
  Automatische Topics werden gespeichert und bleiben nach Umbenennung erhalten.
- Begrenzte Übertragung, letzter X/Y-Wert nach Abheben; Abbruch bei Mehrfinger-
  kontakt, mechanischem Klick, Eingabeverlust oder Optionsänderung.
- Lokale Tests mit synthetischen Linux-Ereignissen und echten Loopback-Brokern.
  Bestehende Einstellungen bleiben erhalten, .112 unverändert.

## 0.1.29 – 22. November 2026 (Zwischenstand, enthalten in 0.1.31)

- Schrittfilter 1–5 für Lautstärke, Bildschirmhelligkeit und Tastaturlicht;
  getrennte Zähler und sicheres Loslassen, Lautstärke-Haltewiederholung berücksichtigt.
- Alphabetische, eingeklappte Gerätegruppen mit jeweils einer offenen Taste.
- Stabile Serien-/HID++-Zuordnung sowie bestätigte manuelle Zuordnung nach
  Umstecken ohne Verlust von Topics, Belegungen und Deck-Seiten.
- Geräte mit Sicherung entfernen, gemeinsame Icons behalten. Mobile-Vertrauen
  separat widerrufen; nur betroffene aktive Mobile-Verbindungen schließen.
- Experimentelle Linux-Type-B-Touchpad-Gesten zum Anlernen; Koordinaten bleiben
  lokal. T650-Hardwaretest noch offen, keine Änderungen auf .112.

## 0.1.28 – 22. November 2026 (öffentliches Testrelease)

Erste Veröffentlichung seit 0.1.22; enthält auch die unten dokumentierten,
bisher lokalen Zwischenstände 0.1.23–0.1.27: grafische 48×48-Iconauswahl mit
Miniaturcache, Duplikatbereinigung je Paket, MDI-Favoriten, USB / Virtuelle Geräte,
bis zu acht Deck-Seiten, fortlaufende Tasten und Vor/Zurück/Home/Gehe zu.

- Mobile-Bildübertragung pro Durchlauf auf vier Bilder und ein Zeitbudget
  begrenzt. Zwischen Paketen werden Eingaben und Heartbeat wieder bearbeitet;
  neue Bilder ersetzen weiterhin ältere noch ausstehende Bilder derselben Taste.
- MDI-Paketgenerator verwendet ein festes ZIP-Systemkennzeichen, damit das
  gebündelte Favoritenpaket unter Windows und Linux bytegleich reproduzierbar ist.
- Ausführlichere Trennungsdiagnose ohne Nachrichteninhalte oder Zugangsdaten:
  Ping/Pong-Zähler, letzte Nachrichtenart, deren Alter und Bildwarteschlange.
- 15-Minuten-Praxistest am SM-T580 bestanden: 8×8, zwei Seiten, mehrfach
  Vor/Zurück und danach rund 14 Minuten Leerlauf; alle 16 Messpunkte verbunden,
  Ping/Pong 56/56 → 232/232. Kein neuer Heartbeat-Timeout und keine Trennung
  im abschließenden Journal; keine erneuten Bilder/Metadaten im Leerlauf.
- Testbericht mit Messwerten und Grenzen unter
  `docs/tests/mobile-0.1.28-15min-20261122.md`. Keine allgemeine Zusage für
  Bildschirmabschaltung, Hintergrundbetrieb oder alle Geräte/Netzbedingungen.

## 0.1.27 – 22. November 2026 (lokales ZIP, nicht veröffentlicht)

- Unter Gestaltung → Tastenfunktion: MQTT, Vor, Zurück, Home und neu „Gehe zu“
  mit Auswahl der Zielseite. Navigationstasten blättern am Tablet ohne MQTT.
- Beim Löschen einer Seite werden Sprungziele nachgeführt; eine gelöschte
  Zielseite wird durch Seite 1 ersetzt. Andere Geräte bleiben unabhängig.

## 0.1.26 – 22. November 2026 (lokales ZIP, nicht veröffentlicht)

- Geräteansicht in „USB / Virtuelle Geräte“ umbenannt.
- Bis zu acht Seiten je Deck, fortlaufende Tastennummern und getrennte Belegungen
  für Handy/Tablet. Neue Seite und Löschen nach Rückfrage; erste Seite geschützt.
- Vor-/Zurück-/Home-Tasten ohne MQTT-Aktion, optionaler Seitenzähler am Tastenbild.
- Verbleibende IDs/Topics beim Löschen einer anderen Seite erhalten. Seite 1 ist
  zu alten Konfigurationen kompatibel; keine automatische Migration bestehender Topics.
- Native Mobile-Seitenbefehle und Seitenmetadaten, ohne die Verbindung neu aufzubauen.
- Gestaltungs- und Farbfelder kompakter. Seitenwechsel beenden gehaltene Aktionen;
  MQTT-Rückmeldungen bleiben ihrer Seite zugeordnet.

## 0.1.25 – 21. November 2026 (lokales ZIP, nicht veröffentlicht)

- Doppelte Icon-IDs im Such-/Auswahlkatalog und der Bibliotheksanzeige je Paket
  zusammenfassen. Gleicher Inhalt unter verschiedenen Namen erzeugt nur eine Kachel.
- Alle alternativen Dateinamen/Suchbegriffe und Lizenzhinweise erhalten. Originale,
  Importzuordnungen und gespeicherte Icon-IDs bleiben unverändert; kein Neuimport nötig.
- Material Vault Black/White enthalten jeweils 6.862 Dateien, davon 5.576 eindeutige
  Dateiinhalte. Echte Stilvarianten und unterschiedliche Pakete bleiben getrennt.

## 0.1.24 – 21. November 2026 (lokales ZIP, nicht veröffentlicht)

- Grafische Iconauswahl statt langer Selectlisten: Pakete, Suche, 48×48-Raster,
  Einzelvorschau, Übernehmen/Abbrechen, Escape und direkte Übernahme per Doppelklick.
- Normal, gedrückt, Hintergrund und MQTT-Rückmeldung nutzen dieselbe Auswahl.
- Höchstens 96 Kacheln pro Paketseite; Bildabruf nur im sichtbaren Bereich.
- Getrennter atomarer Miniaturcache auf dem Pi und privater Browsercache. Auswahl
  rendert nur das erste Bild und erzeugt weder Vollbild- noch Animationscache.
- Kompakter Bibliothekskatalog überträgt gleiche Paketlizenzen nur einmal.
- Bestehender asynchroner MQTT-Test wartet auch auf den Empfang der Plus-Rücksetzung.

## 0.1.23 – 21. November 2026 (lokales ZIP, nicht veröffentlicht)

- Optionales Offline-Favoritenpaket: 20 MDI-Ein-/Aus-Paare in SteelBlue, direkt aus
  der Iconbibliothek hinzufügen; gespeicherte Zuordnungen bleiben erhalten.
- 147 einzeln importierbare Farbsets aus gelieferten CSS-SVG-Hintergründen,
  40 Icons je Farbe in 48×48 mit kontrastierenden Symbolen, Namen und Suchbegriffen.
- Reproduzierbarer Offline-Generator, Originalquellen, Paketlizenzen und Vorschau.
- ZIP-Erstellung behandelt eingebettete Iconarchive als Binärdateien.

## 0.1.22 – 21. November 2026 (öffentliches Testrelease)

- Paket-/Ordnerimport sammelt den Index im Speicher und speichert einmal am Ende.
- Vorschaubilder und Animationsdaten entstehen erst bei Bedarf, anschließend Cache.
- Browser-Ordner werden vor dem Upload als ein ZIP gebündelt; mehrere Pakete,
  Metadaten und Originalpfade bleiben erhalten.
- Vorhandene IDs beim Wiederimport erhalten, atomare Cachedateien und Indexablage.
- Windows-Einzelvergleich: 240 echte Bilder 4,262 auf 0,395 s; 6.800 synthetische
  PNGs 458,323 auf 10,464 s. Kein Zugriff auf den laufenden Pi-Import.

## 0.1.21 – 21. November 2026 (lokales ZIP)

- Paketimport mit Ladebalken und echten Serverzählständen „x von y Icons“.
- Ordnerupload liest manifest.json für Paketname und Autor sowie vorhandene Lizenzdateien.
- Beispiel geprüft: Fluent UI System Icons (Filled) statt technischem Ordnernamen.
- Erneuter Import aktualisiert den Anzeigenamen, ohne bestehende IDs zu duplizieren.
- Lokaler Chrome-Test mit echtem Itsyhome-Upload: 240 Icons, Zwischenstände während
  der Verarbeitung sichtbar. Keine Einstellungen auf .112 geändert, nichts veröffentlicht.

## 0.1.20 – 21. November 2026 (lokales ZIP)

- Pluginbilder zusätzlich unter imgs/ samt Unterordnern importieren.
- Itsyhome 1.2: Fehler mit 0 Icons reproduziert, nach Korrektur 240 PNG-Dateien
  in 14 Unterordnern ohne übersprungene Bilder übernommen. Kein Plugincode importiert.
- Leere Bildimporte liefern einen verständlichen Hinweis statt nur 0 ohne Erklärung.
- Enthält die Paketlizenz und kompakten 52×52-Kacheln aus 0.1.19.

## 0.1.19 – 21. November 2026 (lokales ZIP)

- Lizenzhinweis im Paketkopf, vollständige Lizenztexte einmal je Paket aufklappbar.
- Keine Lizenzdetails pro Icon; 52×52-Kacheln für 48×48-Miniaturen.
- Originalnamen und Animationshinweise weiterhin im Hover-/Fokuspopup.
- Vorher gesichert, DOM und Chrome lokal geprüft, nichts veröffentlicht.

## 0.1.18 – 21. November 2026 (lokales ZIP)

- Iconbibliothek als aufklappbare Pakete mit Suche, Unterordnern und Hover-/Fokusvorschau.
- 48×48-Miniaturen; Originaldateinamen bleiben erhalten, keine IDs in der Bibliothek.
- Originale unter icons/IconPacks, abgeleitete Daten unter icons/.cache; Altbestand kompatibel.
- GIF-/WebP-Animationen normal und gedrückt, bis 120 Bilder und 10 Bilder/s; statische
  Tasten ohne laufende Übertragung. Plugin-ZIPs liefern nur Bilder, keinen ausführbaren Code.
- Paketentfernung mit vorheriger Sicherung und Schutz noch verwendeter Icons.
- Freier/gesamter Datenspeicher im Kopf, Warnfarbe bei knappem Speicher und Importprüfung.
- Lokal einschließlich verschlüsselter Mobile-Verbindung geprüft; echter Tablet-Test offen.

## 0.1.17 – 21. November 2026 (lokales ZIP)

- Tastenliste zunächst eingeklappt: Gerätename – Key – Name.
- Höchstens eine Taste geöffnet; Öffnen der nächsten schließt die vorherige.
- Namensänderungen sofort in der Zeile sichtbar; Entwürfe bleiben beim Wechsel erhalten.
- Speicherhinweis und Markierung geänderter Zeilen, Speichern/Abbrechen direkt
  im Eintrag. Abbrechen setzt nur diese Taste zurück und erhält andere Entwürfe.
- Vorher gesichert, lokal geprüft, nichts veröffentlicht.

## 0.1.16 – 21. November 2026 (lokales experimentelles ZIP)

- Zweites Icon, Hintergrund- und Schriftfarbe pro gedrückter Stream-Deck-Taste.
- Loslassen stellt normale bzw. letzte MQTT-Anzeige wieder her; normale Werte
  gelten weiterhin, wenn keine eigene gedrückte Darstellung gewählt wurde.
- Browser-Vorschau ohne MQTT-Auslösung; Persistenz und Darstellung lokal geprüft.
- Echter Tablet-Test offen, nichts veröffentlicht.

## 0.1.15 – 21. November 2026 (lokales experimentelles ZIP)

- Android-App bestimmt wieder das Mobile-Raster. X/Y-Übersteuerung und globale
  Rasterfelder entfernt; alte gespeicherte Übersteuerung bleibt inaktiv.
- Rasterwechsel aktualisiert bei Textentwürfen nur die Tastenansicht; das
  Eingabeformular bleibt bestehen. Offline bleibt das letzte App-Raster erhalten.
- Keepalive korrigiert: leerer Ping alle fünf Sekunden, passend zum leeren Android-
  Pong und vor dessen Receive-Timeout. Keine Bild-/Context-Aktualisierung dafür.
- Ping/Pong-Zähler sichtbar; Verbindung mit realem Empfangswächter über das alte
  15-Sekunden-Fenster hinaus und Tastendruck danach lokal geprüft.

## 0.1.14 – 21. November 2026 (lokales experimentelles ZIP)

- Stream-Deck-Tab dauerhaft; Offline-Status ersetzt weder Editor noch Tastenauswahl
  oder Textentwurf. Wiederverbindung navigiert nicht erneut zum Editor.
- Gerätegeometrie gespeichert, Mobile-Raster im Register auch offline abrufbar.
- Mobile-Raster je Gerät in X/Y-Einerschritten 1–8 einstellbar, ohne Neuverbindung.
  Gespeicherte Tasten bleiben beim Verkleinern erhalten.
- Nicht unterstützte optionale Protokollbefehle trennen vertrauenswürdige Sitzungen
  nicht mehr; begrenzte Liste letzter Trennungsgründe zur Diagnose.

## 0.1.13 – 21. November 2026 (lokales experimentelles ZIP)

- LZ4-Mobile-Bilder in BGRA statt RGBA: Rot/Blau korrigiert, Webvorschau und
  physische USB-Ausgabe unverändert.
- Identische Context-Metadaten und gleiche Bildpixel nicht erneut senden;
  veraltete Bildgrößen verwerfen. Versandzähler zur Blink-Diagnose sichtbar.
- Fehlende Stream-Deck-Tasten erhalten nach Freigabe/Speichern alle elf lesbaren
  Standardkanäle. Vorhandene Tasten und Einzelaktionen bleiben erhalten.
- Kopplung/Icon-/Tastenempfang auf Android vom Nutzer bestätigt; Prüfung der
  Farb-/Blinkkorrektur und automatischen Topics auf .112 bleibt offen.

## 0.1.12 – 21. November 2026 (lokales experimentelles ZIP)

- Falsche Produktversion in HelloFromServer.version korrigiert: Android verlangt
  dort Desktop-Kompatibilität ab 6.3. Jetzt 6.3.0; echte Extender-Version bleibt
  in Oberfläche/CLI und in der ergänzenden Serverkennung erhalten.
- Regression für Mindestversionsprüfung und Textänderungen oben/mittig/unten
  mit kleinem/großem Text ohne Verbindungsabbruch ergänzt.
- Serveridentität, gespeicherte Kopplung, Icons und Einstellungen bleiben erhalten.

## 0.1.11 – 21. November 2026 (lokales experimentelles ZIP)

- Einzelne/mehrere Icons und komplette PC-Ordner mit Unterordnern importieren.
  Ordnername als Sammlung, Fortschritt und Meldungen zu übersprungenen Dateien.
- Vorhandener Raspi-Pfadimport und ZIP-/Elgato-Iconpacks bleiben verfügbar.
  Bestehende Icons, Belegungen und Einstellungen werden erhalten.

## 0.1.10 – 21. November 2026 (lokales experimentelles ZIP)

- Text oben/unten reserviert eigenen Platz und verkleinert das Vordergrundicon.
  Hintergrundbild bleibt vollflächig, Text mittig bleibt überlagert. Gemeinsamer
  Renderer für Vorschau, physisches Deck und Mobile.

- Unveränderte Größenmeldungen von Mobile starten keine Bildaktualisierung mehr.
- Bereits übertragene, unveränderte Tastenbilder werden nicht erneut gesendet.
  Ein geändertes Icon wird einmal übertragen; neue Decköffnung und tatsächliche
  Größen-/Rasteränderung laden die benötigten Bilder erneut.
- Nutzer bestätigt Iconimport und Bilddarstellung auf Android. Abweichung zwischen
  Tablet 3×5 und Editor 5×5 bleibt als Praxisprüfung offen.
- Android-Kaufstatus statisch geprüft: RevenueCat „Full Access“, gespeicherter
  Pro-Status und Freigabe zusätzlicher Designs. Keine Änderung der Android-App.

## 0.1.9 – 21. November 2026 (lokales experimentelles ZIP)

- Neue Mobile-Vorgabe 5 Spalten × 3 Zeilen. Editor übernimmt das vom Tablet in
  KeypadConfig/UpdateKeypadConfig gemeldete Raster; bestehende Konfiguration bleibt.
- Neue Mobile-Verbindung öffnet den grafischen Editor automatisch. Ungespeicherte
  Änderungen, Anlernen und laufende Bearbeitung werden geschützt; keine automatische
  MQTT-Freigabe.
- Rastervorgaben ändern nur die Vorgabe, nicht die native Android-App. Oberfläche
  benennt dies ausdrücklich und zeigt das gemeldete Raster samt Herkunft.
- Raster- und Anzeigeänderungen starten den WebSocket-Listener nicht mehr neu.
  Bestehende Verbindung und virtuelles Deck bleiben erhalten.
- Verlorene Context-Aktualisierung bei Änderungen direkt nach Decköffnung behoben.
- Lokaler Protokoll-/Chrome-Test: 15 Tasten, 3 hoch/5 breit, Editor automatisch offen,
  Vorgabe ändern ohne Trennung und ohne Übersteuern des Tablet-Rasters.

## 0.1.8 – 21. November 2026 (lokales experimentelles ZIP)

- Kopplungsanfrage mit Prüfabdruck und Bestätigungsbutton direkt nach Hello
  anzeigen; nicht erst nach der zusätzlichen Authenticate-Nachricht.
- Menschliche Bestätigung vor oder nach Authenticate verarbeiten. Keine erfundenen
  Anfrage-IDs: Ok nur als Antwort auf eine tatsächlich empfangene Anfrage.
- ClientCapabilities darf vor der Bestätigung eintreffen, gewährt aber keine
  Steuerung und ändert keine Pro-Freischaltung.
- Deutlicher Prüfcode und hervorgehobenes „Gerät vertrauen“. Ablehnen, Fenster-
  ablauf und fehlende Freigabe sperren weiterhin Eingaben.
- Wartendes Tablet lokal mit echtem WebSocket und Chrome nachgestellt. Erneuter
  vollständiger Android-/Pi-Praxistest weiterhin erforderlich.

## 0.1.7 – 21. November 2026 (lokales experimentelles ZIP)

- Optionaler, standardmäßig deaktivierter Stream-Deck-Mobile-Server im Core-Dienst.
  Eigener WebSocket-Port, Aktivierung und Rasterwahl in der Weboberfläche.
- QR-Code mit Server-ID und lokalem Endpunkt, zweiminütiges Kopplungsfenster und
  ausdrückliche Bestätigung/Ablehnung mit öffentlichem Schlüsselprüfabdruck.
- Unabhängig implementierter VSD2-Nachrichtenausschnitt, libsodium-kompatibler
  Schlüssel­austausch und verschlüsselte Datenpakete. Kein Elgato-Code/Binary enthalten.
- Virtuelle Decks, lokale Iconübertragung per LZ4/PNG, Eingaben über bestehende
  MQTT-Belegungen und Rückmeldungsanzeige. Mobile-Geräte im grafischen Deck-Tab.
- Frei konfigurierbares Raster bis 8×8, keine serverseitige Kauf-/Pro-Stufe.
  App-eigene Freischaltungen werden nicht verändert; eine Seite, keine Shortcuts.
- Serveridentität, Vertrauen und virtuelle Geräte überstehen Neustarts. Beim
  Deaktivieren schließen Listener/Clients; USB/MQTT und vorhandene Daten bleiben.
- 88 lokale Python-Tests, DOM und Chrome erfolgreich. Kein echter Android-/Pi-
  Verbindungstest; Funktion bleibt ausdrücklich experimentell. Keine Veröffentlichung.

## 0.1.6 – 21. November 2026 (lokales ZIP)

- Zusätzlicher Stream-Deck-Tab nur bei aktuell erkanntem Gerät und aktivem Dienst.
- Echtes Treiberlayout, Geräteauswahl, grafische Tastenauswahl und Vorschau mit
  derselben Bildaufbereitung wie auf der Hardware.
- Icons, Hintergrundbilder/-farben, Beschriftung, Schriftfarbe/-größe/-position,
  Einpassen und Zuschneiden. Keine Fremdsoftware oder fremden Bilder übernommen.
- MQTT-Einzelaktionen je Taste, Zielbroker sowie Rückmelde-Topic und aktives Icon.
  Bestehende Tastenlisten und Topics bleiben erhalten; Gestaltung erzeugt keine Aktion.
- Gestaltung separat in der Gerätekonfiguration; alle Tasten bei Neuladen neu
  aufbauen, damit entfernte Belegungen keine alten Bilder zurücklassen.
- Authentifizierte Vorschau ohne Konfigurationsänderung; Bilder bleiben in der
  bestehenden Bibliothek. Pedal ohne Display mit MQTT-Zuordnung, ohne Bildeditor.
- Abziehen/Dienst-Ausfall blendet den Tab aus; gespeicherte Einstellungen bleiben.
- Lokal getestet; noch kein physischer Stream-Deck-Praxistest und nicht veröffentlicht.

## 0.1.5 – 21. November 2026

- Switch als Umschalter: erster Druck ON, nächster OFF. Zustand dauerhaft separat
  gespeichert und beim Wiederverbinden synchronisiert; Loslassen schaltet nicht um.
- Separater Tastenzustand `/state` für gedrückt ON / losgelassen OFF. Bisheriger
  Switch-Modus bleibt bei Bedarf ausdrücklich als Kompatibilitätsauswahl verfügbar.
- Button mit Einzel-/Doppelklick und Halten; gemeinsames `/button`, optional
  `/button-plus` mit Leer-Rücksetzung sowie einzelne Gesten-Topics.
- Zeiten pro Taste einstellbar; keine zusätzlichen Einzelklicks bei Doppelklick
  oder Halten. OS-Wiederholung zählt weder als Klick noch als neuer Switch-Druck.
- Gemeinsame HA-Gerätezuordnung, eindeutige Button-Auslöser und separater
  Binärsensor für den Tastenzustand; nur einfache Werte auf allen Daten-Topics.
- Volle Fensterbreite, kompakte gruppierte Tastenliste, einblendbare Broker-Ziele.
- Bestehende Topics/Aktivierungen erhalten. Neue Zusatzkanäle bestehender Zeilen
  sind zunächst aus; neu angelernte Tasten haben alle elf Kanäle vorbereitet.

## 0.1.4 – 21. November 2026

- Neue Tasten haben sofort lesbare, ausgefüllte Topics:
  `geraetename-key-f1/press`, `/release`, `/switch`, `/press-plus`, `/release-plus`.
- Alle fünf Kanäle werden vorbereitet und sind einzeln aktivierbar. Plus ist ein
  separater Kanal mit Leer-Rücksetzung; normale Press/Release bleiben unverändert.
- Gleiche Gerätenamen erhalten lesbare Zähler, Umlaute werden MQTT-tauglich
  umgewandelt. Gespeicherte Topics ändern sich bei späterer Umbenennung nicht.
- HA-Discovery verwendet durchgehend dieselbe Gerätekennung und denselben
  Anzeigenamen für alle Tasten, Plus-Auslöser und Binärsensoren eines Geräts.
- Lautstärkewiederholung berücksichtigt auch den separaten Press+-Kanal.
- Bestehende Einzelbelegungen und Tasten aus 0.1.3 bleiben kompatibel und behalten
  Topics, Aktivierung sowie die bisherige Plus-Funktion.

## 0.1.3 – 21. November 2026

- Anlernmodus mit 15-Sekunden-Lease pro Gerät; unterdrückt dessen MQTT-Aktionen,
  erfasst neue Tasten ohne Duplikate und übernimmt sie erst nach bewusster Auswahl.
- Kompakte Tastenliste mit Name, Aktivierung, Press-/Release-/Switch-Topics,
  Plus-Checkboxen, Iconwahl und Brokerwahl pro Zeile. Altbelegungen bleiben erhalten.
- Press/Release senden `press`/`release`; Switch sendet `ON`/`OFF`. Plus setzt nur
  seinen Aktionswert nach 50 ms leer zurück, auch bei schnell folgenden Eingaben.
- Lauter/Leiser mit begrenzter Wiederholung beim Halten; beendet bei Release,
  Geräteverlust, Konfigurationswechsel und spätestens nach 30 Sekunden.
- HA-Discovery für neue Press-/Release-Auslöser mit Payloadfilter und Switch als
  Binärsensor. Kein retained Versand und keine Wiederholung von Offline-Eingaben.
- Neues ZIP mit unverändertem Update-/Sicherungsweg. Physischer Pi-Nachtest und
  ioBroker-Empfang bleiben ausdrücklich offen.

## 0.1.2 – 21. November 2026

- Lokale Discovery-Fehler werden abgefangen und in der Diagnose angezeigt;
  MQTT-Daten werden unabhängig davon weitergesendet.
- Discovery pro Broker ausdrücklich wählbar: **Aus – nur MQTT-Daten senden**
  oder **Home Assistant – Geräteauslöser anmelden**. Neue Konfigurationen starten
  ohne Discovery; vorhandene Einstellungen bleiben erhalten.
- Bekannte eigene retained Discovery-Konfigurationen werden beim Abschalten und
  Wiederverbinden zurückgenommen. Ältere Versionen werden anhand der lokalen
  Konfigurationssicherungen berücksichtigt. Fremde Discovery-Einträge bleiben erhalten.
- Tastaturschreibweisen wie `key:tab` oder `key_tab` werden zu `KEY_TAB` vereinheitlicht;
  numerische Stream-Deck-Kennungen wie `key:0` bleiben erhalten.
- Sende-Topic und effektive Ziele stehen direkt in der Belegung. Die Ereignistabelle
  zeigt MQTT-Sendestatus, Zielbroker und Topic oder den Grund für fehlenden Versand.
- Live-Nachtest: Nach Korrektur der Tab-Belegung empfing der offene HA-MQTT-Explorer
  drei Nachrichten mit `control: KEY_TAB` und `event_type: press`.

## 0.1.1 – 21. November 2026

- Tastaturzugriff auf Raspberry Pi OS: Dienstkonto zusätzlich in der Standardgruppe
  `input`; systemd setzt diese Gruppe ebenfalls ausdrücklich. Die udev-Regel erhält
  die Standardgruppe, statt sie durch eine private Gruppe zu ersetzen.
- Installer wartet auf abgeschlossene udev-Verarbeitung und prüft Leserechte der
  erkannten Eingabegeräte unter dem tatsächlichen Dienstkonto.
- Dienststatus wird mit der Uhr des Raspberry Pi berechnet. Eine abweichende
  PC-Uhr erzeugt keine falsche Anzeige „Dienst nicht aktiv“ mehr.
- evdev-Aliase werden zu einem Tastennamen vereinheitlicht, insbesondere
  `KEY_MIN_INTERESTING,KEY_MUTE` zu `KEY_MUTE`. Bestehende Alias-Zuordnungen bleiben nutzbar.
- Bestätigte Browserdiagnose auf dem Raspi: Eingabegeräte und MQTT erkannt,
  aber `Permission denied` beim Öffnen der Eingabekanäle. Nach Korrektur der Gruppe
  `input` kommen HCT-Tastatur- und Volumeregler-Ereignisse in der Liveansicht an.

## 0.1.0 – 21. November 2026

Erste eigenständige Fassung von **USB Extender für Home Assistant**.

- Drei unabhängig konfigurierte MQTT-Broker, Ziele pro Gerät und Taste.
- USB-Bestandsliste, bewusst freigegebene evdev-Eingaben und Stream-Deck-Adapter.
- Medien-/Makrotasten, Halten, Wiederholung und Drehregler-Ereignisse.
- Stream-Deck-Icons, Text, Helligkeit und MQTT-Zustandsrückmeldungen.
- Eigene Iconordner, Einzelbilder, ZIP und lokale Elgato-Iconpack-Archive.
- Separat abschaltbare, passwortgeschützte Weboberfläche.
- Neunstufiger Installer mit Prüfung und Nachinstallation fehlender Pakete,
  Update-Sicherung, separatem Dienstkonto, getrennten Prozessen und Programm-Rückschaltung.
- Anleitung, automatisierte Prüfungen und kopierbares Raspi-Installations-ZIP.

Physischer Raspberry-Pi-/USB-Test steht vor dem Praxiseinsatz noch aus.
