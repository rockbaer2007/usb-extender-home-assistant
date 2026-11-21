# Offene Schritte

## Als Nächstes: Praxisprüfung auf dem Raspberry Pi 4

- 0.1.5 auf dem Pi installieren und den Anlernmodus mit der Trust-Tastatur prüfen:
  keine Aktionen beim Anlernen, keine Duplikate, Übernahme/Speicherung und Neustart.
- Press/Release, Plus-Rücksetzung und Switch ON/OFF praktisch prüfen; Lauter/Leiser
  halten und kontrollieren, dass die Wiederholung beim Loslassen stoppt.
- Switch als Umschalter, separaten Tastenzustand und Klick/Doppelklick/Hold per
  physischer Taste prüfen. App-Neustart mit gesetztem Switch praktisch nachtesten.
- Breite gruppierte Tastenliste visuell in Chrome und auf Tablet prüfen.
- Fehlenden ioBroker-Empfang unabhängig davon weiter eingrenzen: .116:1883 ist
  online, neue Objekte sind erlaubt, keine ignorierten Topics; Tastendaten fehlen.
- Ein konkretes Stream-Deck-Modell prüfen: Erkennung, Freigabe,
  Drücken/Loslassen/Halten, Icons und Helligkeit.
- Weitere Medientasten prüfen, insbesondere Play/Pause und Titelsprung.
  Tastatur press/release sowie Lautstärke− und Stumm wurden bereits live bestätigt.
- USB-Geräte abziehen/wieder anstecken, den Pi neu starten und die gespeicherten
  Belegungen sowie MQTT-Wiederverbindung prüfen.
- Drei reale MQTT-Broker anschließen, Ausfall eines Brokers prüfen und HA-Discovery
  sowie Display-Rückmeldungen mit der tatsächlichen HA-Installation testen.
- HA-Binärsensor für den Switch-Zustand sowie gefilterte Press/Release-Auslöser
  einschließlich der separaten Plus-Kanäle unter einem benannten USB-Gerät
  mit Discovery praktisch prüfen. IOB-Discovery bleibt aus: hass-mqtt meldete
  `device_automation` als nicht unterstützt.
- Webdienst per CLI beenden und bestätigen, dass die Geräte weiterarbeiten und
  Port 8098 geschlossen ist. Anschließend erneut starten.
- Ein tatsächlich verwendetes Marketplace-Iconpack mit eigener gültiger Lizenz
  importieren; Bericht auf nicht unterstützte SVG-/Archivvarianten prüfen.

## Mögliche Erweiterungen nach der Praxisprüfung

- Profil-/Seitenwechsel für Stream Decks.
- Optionale Animationen und gestaltbare Stream-Deck-Plus-Touchscreen-Anzeigen.
- Weitere USB-Adapter anhand konkret vorhandener Geräte, zum Beispiel serielle
  Bedienelemente. Eine allgemeine USB-Erkennung ersetzt keine Protokollanbindung.
- Eigenständiges Tablet-Deck als separater Dienst. Dafür muss eine Oberfläche
  während der Tablet-Nutzung erreichbar bleiben; Stream Deck Mobile wird dadurch
  nicht automatisch mit dem Pi kompatibel.

Erledigte Implementierungsschritte stehen im Changelog und nicht als offene Aufgaben hier.
