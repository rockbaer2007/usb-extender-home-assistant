# Gamepad: Digital- und Analogmodus untersuchen

## Geführter Einzeltest

Mit `--guided --seconds 10` startet ein separater Test im Analogmodus: zehn Sekunden
Ruhemessung, danach linker/rechter Stick jeweils horizontal/vertikal, L1/R1, L2/R2
und linker/rechter Stick-Klick. Pro Schritt nur das genannte Bedienelement betätigen.
Die Modusumschaltung erst nach Start des Programms vornehmen, wenn der normale
USB-/MQTT-Dienst bereits pausiert ist. `s` überspringt ein nicht vorhandenes Element.

Tastendrücke und Loslassen werden gezählt, Achsenbereiche und unterschiedliche
Werte erfasst. Schwankungen werden mit der Ruhemessung verglichen. Mehrere reagierende
Codes bleiben als Kandidaten sichtbar und werden nicht künstlich eindeutig zugeordnet.
Am Ende werden alle Schritte nochmals kompakt ausgegeben, damit sie im Terminalpuffer
sichtbar bleiben. Auch übersprungene oder signalfreie Schritte werden dokumentiert.
Alle Rohdaten enthalten zusätzlich die Schrittbezeichnung. Frühere Ergebnisse bleiben
in ihren eigenen Ordnern erhalten. Der reine Digital-/Analogvergleich ohne `--guided`
bleibt weiterhin verfügbar. Sieben lokale Tests einschließlich Dienstwiederherstellung
und Ruherauschfilter erfolgreich; tatsächlicher geführter Hardwarelauf noch offen.

Eigenständiger Rohdatenmonitor `tools/gamepad_probe.py`, ohne Imports des
USB-Extenders, MQTT-Clients oder Netzwerkanbindung. Der normale USB-/MQTT-Dienst
wird vor der Auswahl des Gamepads pausiert und beim Ende/Abbruch in seinen
vorherigen Laufzustand versetzt. Andere Belegungen pausieren währenddessen mit.
Der Webdienst bleibt unberührt; ungespeicherte Formulare werden nicht gespeichert.

Der Monitor wählt nur Linux-Gamepad-/Joystick-Schnittstellen, keine normalen
Tastaturen, Mäuse oder Touchpads. Das konkret gewählte USB-Gerät wird nach einem
Moduswechsel am selben USB-Port erneut gesucht, sodass neue event-Nummern und
geänderte Produktkennungen protokolliert werden können. Werden Schnittstellen
nicht mehr als Gamepad erkannt, wird abgebrochen statt fremde Eingaben zu lesen.

1. Prüf-ZIP auf den Pi kopieren, entpacken und Prüfsummen kontrollieren.
2. Mit Python aus der bestehenden USB-Extender-Umgebung und `sudo` starten.
3. Gamepad aus der Liste auswählen. Digitalmodus einstellen, Sticks loslassen,
   Enter drücken. Ab „MESSUNG … STARTET“ alle Tasten, Steuerkreuz, Sticks und
   Trigger einzeln betätigen. Dieselbe Folge nach Aufforderung im Analogmodus.

Beide Phasen dauern standardmäßig 60 Sekunden (`--seconds 10…300`). Ausgabe
enthält Zeit, Linux-Eingabename, Rohwert, Tastenzustand und bei absoluten Achsen
eine Normalisierung auf 0–100 Prozent. Die Prozentzahl beschreibt den gelesenen
Wertebereich; sie ist kein MQTT-Wert und keine Controller-Kalibrierung. Nullbereich
wird als unbekannt behandelt. Fähigkeiten zeigen Achsengrenzen, Ruhewerte und
Totzonen; der Bericht zählt tatsächlich betätigte Eingaben und beobachtete Bereiche.

Im privaten Ergebnisordner entstehen `ausgabe.txt`, `ereignisse.jsonl`,
`digital-faehigkeiten.json`, `analog-faehigkeiten.json` und `bericht.json`.
Eine leere Phase oder verlorene Ereignisse (`SYN_DROPPED`) gelten nicht als Erfolg.
Fünf Einstellungs-/Kopplungsdateien werden vor/nach der Messung per SHA256 verglichen,
ihre Inhalte werden weder verändert noch in den Bericht kopiert. Die Originalmodi
des Gamepads werden vom Benutzer gewählt und sind nicht automatisch beweisbar.

Bislang lokal mit simulierten Geräten geprüft. Gerät auf .112 sichtbar als
„Generic USB Joystick“, USB-ID 0079:0006; reale Fähigkeiten und Ereignisse erst
nach Durchführung der beiden Messungen bewerten. Keine Veröffentlichung.
