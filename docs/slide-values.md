# Richtungswerte und HA-Discovery – 0.1.32 (lokal)

Gerät freigeben, Touchpad-Gesten aktivieren und speichern. Unter „Ein-Finger-Slide“
die gewünschten Richtungswerte einzeln aktivieren. Jede Richtung hat ein eigenes
Topic; leer bedeutet automatisch beim Speichern anlegen. Die Geräte-Zielbroker
gelten auch für diese Werte. X/Y bleibt unabhängig einschaltbar.

Alle Werte sind absolute Positionen auf der gesamten Fläche, keine Weglänge ab
dem Aufsetzen. `x` und `y` sind normalisiert: links/oben 0, rechts/unten 100.

| Bewegung | Wert | Vollständiger Weg |
| --- | --- | --- |
| Unten → oben (UP) | 100 − y | 0 → 100 |
| Oben → unten (DOWN) | 100 − y | 100 → 0 |
| Links → rechts (RIGHT) | x | 0 → 100 |
| Rechts → links (LEFT) | x | 100 → 0 |
| Links unten → rechts oben (UP_RIGHT) | (x + 100 − y) / 2 | 0 → 100 |
| Rechts oben → links unten (DOWN_LEFT) | (x + 100 − y) / 2 | 100 → 0 |
| Links oben → rechts unten (DOWN_RIGHT) | (x + y) / 2 | 0 → 100 |
| Rechts unten → links oben (UP_LEFT) | (x + y) / 2 | 100 → 0 |

Gerundet auf ganze Zahlen, begrenzt auf 0–100. Kurze Wege liefern Teilbereiche.
Nur die aktuell erkannte Richtung sendet, nicht gleichzeitig die benachbarten
Achsenrichtungen. Empfindlichkeit und maximale Senderate 1–30/s gelten weiterhin.
Unveränderte Werte werden nicht erneut gesendet. Ein zuletzt zurückgestellter Wert
darf nach dem Abheben einmal gesendet werden. Mehrfinger, mechanischer Klick,
Ereignisverlust und Konfigurationswechsel verwerfen zurückgestellte Werte.
Nach einem Slide entsteht kein zusätzlicher Tipp. Im Anlernmodus werden die
Zahlen unterdrückt; bestehende anlernbare Richtungsaktionen bleiben unabhängig.

## Home Assistant und ioBroker

HA-Discovery beim betreffenden MQTT-Broker einschalten. Aktivierte Richtungswerte
und X/Y erscheinen mit stabilen IDs als Sensoren am selben Gerät. Beim Speichern,
Neuverbinden und HA-Start werden die Anmeldungen abgeglichen. Abschalten eines
Kanals, der Gesten oder des Geräts, Abwählen eines Ziels und Abschalten der
Discovery entfernen die eigenen Anmeldungen. Fremde Topics werden nicht gelöscht.
Die bestehende Gerätekennung und selbst gewählte X/Y-Topics ändern sich nicht.

Die Werte selbst sind reine Zahlen mit QoS 0, ohne Retain und ohne Wiedergabe
verpasster Offline-Bewegungen. Nach erstmaliger Anmeldung können Sensoren bis zur
nächsten Bewegung unbekannt sein. ioBroker bekommt dieselben Werte auf seinen
gewählten Zielbrokern; Discovery dort kann ausgeschaltet bleiben.

## Prüfgrenze

Dieser Stand wird ausschließlich lokal mit synthetischen Touchpad-Ereignissen,
temporären Konfigurationen und drei MQTT-Brokern auf 127.0.0.1 geprüft. Der echte
T650-Test von 0.1.31 belegt die bisherige Richtungs-/X/Y-Erkennung, ersetzt aber
keinen Praxistest der neuen Richtungswerte oder ihrer Darstellung in echtem HA.
