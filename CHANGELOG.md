# Änderungen

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
