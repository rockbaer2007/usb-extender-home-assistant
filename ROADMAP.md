# Offene Schritte

## Als Nächstes: Praxisprüfung auf dem Raspberry Pi 4

- ZIP kopieren und den neunstufigen Installer auf Raspberry Pi OS 64 Bit ausführen;
  Paketprüfung, Installation und Dienststart bestätigen.
- Ein konkretes Stream-Deck-Modell sowie eine Medien-/Makrotastatur prüfen:
  Erkennung, Freigabe, Drücken/Loslassen/Halten, Icons und Helligkeit.
- USB-Geräte abziehen/wieder anstecken, den Pi neu starten und die gespeicherten
  Belegungen sowie MQTT-Wiederverbindung prüfen.
- Drei reale MQTT-Broker anschließen, Ausfall eines Brokers prüfen und HA-Discovery
  sowie Display-Rückmeldungen mit der tatsächlichen HA-Installation testen.
- ioBroker-Adapter für HA-Discovery praktisch prüfen: Werden die MQTT-
  Geräteauslöser (`device_automation`) übernommen? Identische Topics und Payloads
  an Produktiv- und Testbroker sind bereits lokal protokollseitig bestätigt.
- Webdienst per CLI beenden und bestätigen, dass die Geräte weiterarbeiten und
  Port 8098 geschlossen ist. Anschließend erneut starten.
- Ein tatsächlich verwendetes Marketplace-Iconpack mit eigener gültiger Lizenz
  importieren; Bericht auf nicht unterstützte SVG-/Archivvarianten prüfen.

## Mögliche Erweiterungen nach der Praxisprüfung

- Profil-/Seitenwechsel für Stream Decks und Doppelklick-Gesten.
- Optionale Animationen und gestaltbare Stream-Deck-Plus-Touchscreen-Anzeigen.
- Weitere USB-Adapter anhand konkret vorhandener Geräte, zum Beispiel serielle
  Bedienelemente. Eine allgemeine USB-Erkennung ersetzt keine Protokollanbindung.
- Eigenständiges Tablet-Deck als separater Dienst. Dafür muss eine Oberfläche
  während der Tablet-Nutzung erreichbar bleiben; Stream Deck Mobile wird dadurch
  nicht automatisch mit dem Pi kompatibel.
- Persistente Discovery-Bereinigung auch für Belegungen, die bei einem längeren
  Broker-Ausfall entfernt werden.

Erledigte Implementierungsschritte stehen im Changelog und nicht als offene Aufgaben hier.
