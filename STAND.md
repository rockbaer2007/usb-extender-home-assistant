# Aktueller Stand

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
