# Offene Schritte

## Als Nächstes: Praxisprüfung auf dem Raspberry Pi 4

- Gespeicherte Tasten nach einem Pi-Neustart und USB-Wiederanstecken praktisch prüfen.
- Press/Release, Plus-Rücksetzung und Switch ON/OFF praktisch prüfen; Lauter/Leiser
  halten und kontrollieren, dass die Wiederholung beim Loslassen stoppt.
- Switch als Umschalter, separaten Tastenzustand und Klick/Doppelklick/Hold per
  physischer Taste prüfen. App-Neustart mit gesetztem Switch praktisch nachtesten.
- Breite gruppierte Tastenliste zusätzlich auf Tablet prüfen; Desktop-Nutzerbilder liegen vor.
- Ein konkretes Stream-Deck-Modell prüfen: Erkennung, Freigabe,
  Drücken/Loslassen/Halten, Icons und Helligkeit.
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

- Profil-/Seitenwechsel für Stream Decks.
- Optionale Animationen und gestaltbare Stream-Deck-Plus-Touchscreen-Anzeigen.
- Weitere USB-Adapter anhand konkret vorhandener Geräte, zum Beispiel serielle
  Bedienelemente. Eine allgemeine USB-Erkennung ersetzt keine Protokollanbindung.
- Eigenständiges Tablet-Deck als separater Dienst. Dafür muss eine Oberfläche
  während der Tablet-Nutzung erreichbar bleiben; Stream Deck Mobile wird dadurch
  nicht automatisch mit dem Pi kompatibel.

Erledigte Implementierungsschritte stehen im Changelog und nicht als offene Aufgaben hier.
