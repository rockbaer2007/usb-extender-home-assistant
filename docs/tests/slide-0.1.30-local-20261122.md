# 0.1.30 – Ein-Finger-Slide, lokale Prüfung

22. November 2026. Windows, Python 3.13, Node, JSDOM und Chrome headless.
Isolierte temporäre Konfigurationen und ausschließlich Loopback-Verbindungen.
Keine Installation/Änderung auf .112, keine Veröffentlichung.

## Sicherung und Erhalt

Quellstand vor Änderungen inklusive lokalem 0.1.29-Stand gesichert:
`M:\repos\_backups\ugso-usb-hub\before-one-finger-slide-20261122-142013.zip`.
ZIP-CRC geprüft. Vorhandene Konfigurationen nicht für Tests verwendet.
Speicher-/Neustartprüfung erhält MQTT-Passwort und Geräte-Ziele; gespeicherte
X/Y-Topics bleiben bei Umbenennung unverändert. Standard X/Y aus.

## Ergebnisse

- Gesamtlauf: **197 Python-Tests bestanden**. Nach der letzten Anpassung zur
  Rücksetzung des Koordinatenvergleichs bei Optionsänderung die **27 Geräte-/
  Gesten-/Slide-Tests erneut bestanden**.
- Vier Richtungen liefern anlernbare Press-/Release-Paare. Kein zusätzlicher Tipp
  nach Slide, auch nach Rückkehr zum Ausgangspunkt. Kurzer normaler Tipp bleibt.
- Empfindlichkeitsunterschied nachgewiesen: identische Bewegung löst bei 10 aus,
  bei 1 nicht. Senderaten 1, 5 und 30 geprüft: Richtungen und Koordinatenpaare
  bleiben jeweils innerhalb ihres Intervalls. Unveränderte Positionen senden
  nach Abarbeitung des letzten Zwischenstands nicht weiter.
- Absolute Werte auf 0–100 begrenzt. Letzter ausstehender Wert wird nach Abheben
  im nächsten erlaubten Intervall übertragen. Mehrfingerkontakt, mechanischer
  Klick, SYN_DROPPED und Optionsänderung verwerfen ausstehende Koordinaten.
- Zweifinger-Scrollen erzeugt keine Ein-Finger-X/Y-Ausgabe. X/Y ist im Anlernmodus
  unterdrückt, Richtungen werden dort mit der Anlernsitzung erfasst.
- Kompletter lokaler Weg Touchpad-Ereignisse → Core → echte Paho-Verbindungen
  zu drei Loopback-Brokern: gleiche Topics und Zahlenwerte, z. B. `80` und `50`,
  kein JSON, kein Retain. Richtungs-Press und -Release ebenfalls angekommen.
- Geräte-Routing auf zwei Broker, dritter ausgeschlossen; ein Broker getrennt,
  verbleibender Broker empfängt weiter. X/Y abschaltbar. Konfiguration während
  der Ausgabe bytegleich erhalten.
- **Neun Node-/DOM-Prüfungen bestanden**. Erweiterte Geräteprüfung speichert
  Empfindlichkeit, Senderate, X/Y und eigene Topics. Chrome bedient die Felder
  auf Desktop und prüft die Geräteansicht bei 390 Pixel Breite auf Überlauf.
- Python-/JavaScript- und Shell-Syntax sowie `git diff --check` erfolgreich.
  Wheel und Installations-ZIP werden mit aktuellem Quellstand gebaut; ZIP-CRC,
  SHA256-Manifest und Quellvergleich beim Paketabschluss geprüft.

## Grenzen und Bedienung

Kein Hardwaretest am echten T650 und kein neuer Linux-Installer-Praxistest.
Der Linux-Treiber muss Type-B-Multitouch liefern; BTN_LEFT allein genügt nicht.
Achsenorientierung des tatsächlichen Treibers ist noch praktisch zu prüfen.
Die Senderate ist eine Obergrenze, keine garantierte Frequenz und keine Grenze
der Gesamtzahl aller MQTT-Kanäle: eine Richtungsaktion kann mehrere aktivierte
Tastenkanäle auslösen, ein X/Y-Paar sind zwei MQTT-Nachrichten je Zielbroker.

Unter USB / Virtuelle Geräte Gesten aktivieren, Slide-Optionen öffnen,
Empfindlichkeit/Rate wählen und optional X/Y einschalten. Speichern. Für
Richtungsaktionen anschließend Anlernen starten und in jede Richtung schieben.
X/Y-Topics werden beim Speichern automatisch angelegt, sofern keine eigenen
Topics eingegeben wurden. X/Y braucht keine zusätzliche Tastenbelegung.
