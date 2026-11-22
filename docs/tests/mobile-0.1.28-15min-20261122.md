# Tablet-Verbindung 0.1.28: 15-Minuten-Praxistest

Datum: 22. November 2026. Ziel: Raspberry Pi .112, SM-T580 mit 8×8-Deck,
zwei Seiten. Version 0.1.28 zuvor durch CLI-Ausgabe bestätigt.

Der Nutzer startete den ausschließlich lesenden Monitor in seiner integrierten
SSH-Sitzung. Codex las dessen laufende Ausgabe und das abschließende Journal.
Keine Konfigurationsänderung, kein Dienstneustart und keine Veröffentlichung.

## Zeitraum und Verfahren

- Start 11:39:17, Ende 11:54:17 **laut Pi-Uhr**. Dauer 900 Sekunden,
  über monotone Zeit gesteuert; 16 Statusmessungen im Minutenabstand.
- Anfangs mehrfach Vor/Zurück am echten Tablet. Danach Leerlauf bei geöffneter
  App, entsprechend der Testanweisung. Keine Android-App-Fernsteuerung.
- Statusdatei `/run/ugso-usbhub/status.json` ausschließlich gelesen.
- Anschließend `journalctl -u ugso-usbhub --since <Teststart> --no-pager`.
- Die Uhrzeiten sind die im Terminal ausgegebenen Gerätezeiten; zwischen
  Pi-Uhr und Beobachteruhr bestand eine Abweichung. Für die Dauer wurde kein
  Vergleich verschiedener Rechneruhren verwendet.

## Messwerte

Das Tablet war bei allen Messungen autorisiert und mit demselben Deck geöffnet.

| Minute | Pi-Zeit | Statusalter (s) | Bilder | Context | Ping | Pong |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 11:39:17 | 1,9 | 332 | 5 | 56 | 56 |
| 1 | 11:40:17 | 0,4 | 1228 | 19 | 68 | 68 |
| 2 | 11:41:17 | 1,7 | 1228 | 19 | 79 | 79 |
| 3 | 11:42:17 | 1,0 | 1228 | 19 | 91 | 91 |
| 4 | 11:43:17 | 0,2 | 1228 | 19 | 103 | 103 |
| 5 | 11:44:17 | 1,4 | 1228 | 19 | 114 | 114 |
| 6 | 11:45:17 | 0,8 | 1228 | 19 | 126 | 126 |
| 7 | 11:46:17 | 0,2 | 1228 | 19 | 138 | 138 |
| 8 | 11:47:17 | 1,5 | 1228 | 19 | 150 | 150 |
| 9 | 11:48:17 | 0,8 | 1228 | 19 | 161 | 161 |
| 10 | 11:49:17 | 1,6 | 1228 | 19 | 173 | 173 |
| 11 | 11:50:17 | 0,8 | 1228 | 19 | 185 | 185 |
| 12 | 11:51:17 | 0,0 | 1228 | 19 | 197 | 197 |
| 13 | 11:52:17 | 1,4 | 1228 | 19 | 208 | 208 |
| 14 | 11:53:17 | 0,4 | 1228 | 19 | 220 | 220 |
| 15 | 11:54:17 | 1,8 | 1228 | 19 | 232 | 232 |

## Journal und Ergebnis

Im Journal des Testzeitraums steht ausschließlich:

```text
Nov 22 11:48:38 raspi-usbextender-ha ugso-usbhub[61379]: 2026-11-22 11:48:38,382 INFO connection open
```

Der Eintrag nennt kein Gerät; er ist keiner bestimmten Gegenstelle zugeordnet.
Die beobachtete Tablet-Sitzung zeigt keine Zählerrücksetzung. Es gibt keinen
Trennungseintrag, keinen Heartbeat-Timeout und keinen Dienstneustart im Zeitraum.

**Dieser 15-Minuten-Test ist bestanden.** Währenddessen wurden 176 Pings
zusätzlich gesendet und 176 Pongs empfangen. Ab Minute 1 bleiben Bild- und
Context-Zähler 14 Minuten konstant; kein unnötiger Bildversand im Leerlauf.

Dies belegt die beobachtete Stabilität nach der Änderung, nicht abschließend
die Ursache sämtlicher früherer Abbrüche. Verhalten bei Bildschirmabschaltung,
App-Hintergrundbetrieb und anderen Netzbedingungen wurde hier nicht geprüft.
