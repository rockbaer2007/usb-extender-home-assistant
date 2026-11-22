# Gamepad-Sticks und Tasten ab 0.1.34

## Einrichtung

Das Profil gilt für das gemessene **DragonRise Inc. Generic USB Joystick,
USB-ID 0079:0006**. Andere Gamepads werden nicht mit dieser Zuordnung behandelt.
Gerät anschließen, Analogmodus wählen und in „USB / Virtuelle Geräte“ für Eingaben
freigeben. Den Abschnitt „Gamepad · DragonRise 0079:0006“ aufklappen und
„Stickwerte per MQTT senden (0–100)“ einschalten. Gewünschte Achsen aktivieren,
Geräte-Zielbroker wählen und speichern. Bestehende Einstellungen bleiben erhalten.

| Wert | Linux-Achse | Automatisches Topic bei Gerätename „Gamepad“ |
| --- | --- | --- |
| Linker Stick X | ABS_X | `gamepad-gamepad/left-x/value` |
| Linker Stick Y | ABS_Y | `gamepad-gamepad/left-y/value` |
| Rechter Stick X | ABS_RX | `gamepad-gamepad/right-x/value` |
| Rechter Stick Y | ABS_RZ | `gamepad-gamepad/right-y/value` |

Leere Topics werden beim Speichern aus dem Gerätenamen erzeugt. Vorhandene oder
manuell eingetragene Topics bleiben erhalten. Der Webbereich zeigt zuletzt
empfangene Werte; vor Bewegung gibt es keinen erfundenen Startwert.

Der gemeldete Hardwarebereich wird auf 0–100 umgerechnet, Mitte 50. Die Hardware-
Totzone beruhigt die Mittelstellung. Die Y-Richtung folgt dem Gerät; keine zusätzliche
Inversion. Die Senderate von 1–30/s gilt **je Achse**, Standard 10. Zwischenwerte
werden bei zu schneller Bewegung zusammengefasst, unveränderte Werte nicht erneut
gesendet. `ABS_Z` wird vollständig ignoriert.

## MQTT und Home Assistant

Ausgabe sind reine Zahlen, kein JSON. Aktivierte Geräte-Zielbroker erhalten die
gleichen Werte. HA-Discovery muss am jeweiligen Broker eingeschaltet sein: Vier
Sensoren mit stabilen IDs gehören zum selben Gerät. Deaktivierte Achsen werden
abgemeldet. Ohne Bewegung können HA-Werte zunächst unbekannt sein. ioBroker braucht
keine Discovery. Offline-Broker erhalten keine später nachgespielten Bewegungen.
Im Anlernmodus werden die analogen Werte dieses Geräts nicht gesendet.

## Schultertasten und Stick-Klicks

Unter „Tasten & Anzeigen“ wie normale Tasten anlernen. Press/Release, Plus-Topics,
Switch ON/OFF und Button-Gesten verwenden die vorhandene Tastenverarbeitung.
Die Linux-IDs bleiben gleich, bestehende Belegungen werden nicht neu angelegt.

| Bedienelement | Linux-ID | Code |
| --- | --- | --- |
| L1 | BTN_BASE | 294 |
| R1 | BTN_BASE2 | 295 |
| L2 | BTN_TOP2 | 292 |
| R2 | BTN_PINKIE | 293 |
| Linker Stick-Klick | BTN_BASE5 | 298 |
| Rechter Stick-Klick | BTN_BASE6 | 299 |

L2/R2 sind bei diesem Gerät digitale Tasten, keine analogen Druckwerte. Das
Steuerkreuz erhält durch diese Erweiterung keine neue Achsen-Zuordnung.

## Prüfstand und Installation

Lokaler, unveröffentlichter Stand. Die Implementierung ist mit simulierten evdev-
Ereignissen und lokalen MQTT-Brokern geprüft; der echte Betrieb muss noch folgen.
[Prüfbericht](tests/gamepad-0.1.34-20261122.md).
Das ZIP auf den Pi kopieren, entpacken und aus dem entpackten Ordner
`sudo bash install.sh` starten. Vor einem später freigegebenen Update auf dem Pi
zusätzlich die dortigen Einstellungen und Kopplungen sichern.
