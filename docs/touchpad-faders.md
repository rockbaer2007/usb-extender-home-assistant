# Fünf senkrechte Touchpad-Regler – 0.1.33 (lokal)

Unter „USB / Virtuelle Geräte“ beim freigegebenen Touchpad die Gestenauswertung
einschalten. Im Bereich „Ein-Finger-Slide“ den „Touchpad-Modus“ auswählen:

- **Acht Slide-Richtungen:** bisherige Richtungsaktionen und aktivierte Richtungswerte.
- **Flächenmodus:** fünf gleich breite senkrechte Streifen von links nach rechts.

Der beim Aufsetzen gewählte Regler bleibt bis zum Abheben fest. Seitliches
Verrutschen wechselt den Regler nicht. Erst nach Abheben wird neu gewählt.
Nur vertikale Bewegung aktiviert den Regler; reine horizontale Bewegung sendet
keinen Reglerwert. Nach oben steigen die Werte, nach unten fallen sie. Die Werte
bezeichnen die absolute Höhe der gesamten Fläche: unten 0, oben 100. Kurze Wege
nutzen Teilbereiche. Es wird keine lokale Gesamtlautstärke verändert.

Jeder Regler ist einzeln aktivierbar und besitzt ein eigenes MQTT-Topic. Beim
erstmaligen Flächenmodus sind alle fünf Regler aktiv. Leere Topics werden beim
Speichern erzeugt, beispielsweise `t650-touchpad/fader-3/value`. Eigene Topics
bleiben erhalten. Die Geräte-Zielbroker gelten unverändert. Zahlen werden mit
QoS 0 ohne Retain gesendet, offline verpasste Bewegungen nicht nachgesendet.
Empfindlichkeit 1–10 und Senderate 1–30/s gelten weiter. Ein letzter zurückgestellter
Wert darf nach Abheben einmal gesendet werden. Mehrfinger, mechanischer Klick,
Ereignisverlust oder Konfigurationswechsel verwerfen ausstehende Reglerwerte.
Kein zusätzlicher Tipp nach Schieben; andere bestehende Mehrfingergesten bleiben.

## Erhalt der Einstellungen und HA-Discovery

Die acht Richtungsbelegungen und ihre Topics werden nicht gelöscht. Im Flächenmodus
pausieren ihre Aktionen, Zahlenwerte und HA-Anmeldungen; am gleichen Gerät werden
stattdessen die aktivierten Regler als Sensoren angemeldet. Rückschalten entfernt
die Regler-Anmeldungen und stellt die aktiven Richtungen mit bisherigen IDs wieder
her. Beide Konfigurationen bleiben gespeichert. Ohne Modusangabe bleibt eine ältere
Konfiguration automatisch im Richtungsmodus. X/Y ist in beiden Modi separat nutzbar;
die X/Y-Topics und Sensor-IDs ändern sich beim Umschalten nicht.

Discovery muss beim ausgewählten HA-Broker eingeschaltet sein. ioBroker benötigt
keine Discovery und erhält reine Zahlen. Nach erstmaliger Anmeldung kann der
Sensor bis zur nächsten Bewegung unbekannt sein. „Speichern“ sichert vorher die
alte Konfiguration nach dem bestehenden Verfahren. Die Mobile-Kopplungen bleiben
unberührt. Für ein Update das neue ZIP separat entpacken und `sudo bash install.sh`
verwenden; `install_032_checked.sh` ist ein historisches Hilfsskript nur für 0.1.32.

## Farben und Triggeranzeige

Die Webansicht zeigt beide Bereiche mit ihren jeweiligen Zuständen:

- Türkis: aktive Regler; der Füllstand entspricht dem letzten empfangenen Wert.
- Gold: aktive Richtungsaktionen. Ihre zuletzt empfangenen Zahlen werden angezeigt,
  soweit entsprechende Zahlenkanäle aktiv sind.
- Grau und „Pausiert“: anderer Modus, deaktivierter Regler oder ausgeschaltetes Gerät.
- Leuchtender Rand: zuletzt empfangener Trigger, bis zu sechs Sekunden sichtbar.

Auch gespeicherte Richtungsbelegungen in „Tasten & Anzeigen“ sind im Flächenmodus
grau mit dem Hinweis „pausiert“. Sie lassen sich weiter verwalten. Der Moduswechsel
im Formular ist zunächst eine gekennzeichnete Vorschau. Erst Speichern schaltet
die echte Verarbeitung um. Die Anzeige verwendet vorhandene Statusabfragen (etwa
alle 2,5 Sekunden); sie bildet keine lückenlose Echtzeitberührung ab und lädt keine
Tastenbilder hoch. Geschlossene Weboberfläche beeinflusst USB/MQTT nicht.

Dieser Stand ist nur lokal geprüft, nicht auf dem Pi installiert oder veröffentlicht.
