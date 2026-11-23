# MQTT-Systemsteuerung und geplantes HA-Kartenpaket

Ab 0.1.37 kann der dauerhaft laufende USB-/MQTT-Dienst Weboberfläche, deren
Autostart und lokale Backups steuern. Die Weboberfläche darf dabei ausgeschaltet
sein. Unter **MQTT-Broker** für jeden gewünschten Broker **MQTT-Systemsteuerung
erlauben (Web/Autostart/Backup)** einschalten und speichern. Standard ist aus;
vorhandene Verbindungen, Topics, Geräte, Kennwörter und Kopplungen bleiben erhalten.

Die Topics sind fest und unabhängig von Gerätebelegungen und Broker-Präfixen.
`global` gilt für den gesamten Extender. Mehrere Extender am selben Broker würden
gemeinsam reagieren; für getrennte Installationen getrennte Broker verwenden.
Nur für vertrauenswürdige Broker freigeben: entsprechend berechtigte MQTT-Clients
können danach diese Betriebsfunktionen auslösen.

## Befehle ohne Retain

| Topic | Payload | Wirkung |
| --- | --- | --- |
| `usb-extender/global/web/set` | `ON` / `OFF` | Webfrontend starten / stoppen; Autostart unverändert |
| `usb-extender/global/web/autorun/set` | `ON` / `OFF` | enable + starten / disable + stoppen |
| `usb-extender/global/backup/set` | `PRESS` | Lokale Sicherung erstellen |
| `usb-extender/global/web/status/set` | `PRESS` | Status neu abfragen |

Payloads exakt großschreiben. Andere Topics/Kommandos führen keine Shellbefehle
aus. Retained Zustellungen beim Verbinden und als Duplikat markierte Zustellungen
werden ignoriert. MQTT-Broker können ein live mit Retain gesendetes Publish ohne
Retain-Flag weiterreichen: Befehle daher grundsätzlich mit Retain **aus** senden.
Die kleine Auftragswarteschlange begrenzt Lastspitzen. Solange ein Backup läuft
oder wartet, wird kein zweites gleichzeitig angenommen.

## Retained Rückmeldungen

| Topic | Inhalt |
| --- | --- |
| `usb-extender/global/state/webrun` | `ON`, `OFF`, bei nicht ermittelbarem Zustand `UNKNOWN` |
| `usb-extender/global/state/autorun` | `ON`, `OFF` oder `UNKNOWN` |
| `usb-extender/global/state/state` | Lesbare Meldung, etwa „Webfrontend erreichbar“ oder „Sicherung abgeschlossen“ |
| `usb-extender/global/state/backup` | JSON mit Sicherungsstatus und UTC-Zeit, bei Erfolg Dateiname |

Beispiel:

```json
{"status":"ok","time":"2026-11-23T14:00:00+00:00","file":"usb-extender-backup-20261123-140000-example.tar.gz"}
```

Backupstatus: `idle`, `running`, `ok`, `error`. Sicherungen enthalten Einstellungen,
Icons und Kopplungsdateien und liegen auf dem Raspi unter
`/var/lib/ugso-usbhub/exports`. Keine Sicherungsinhalte oder Zugangsdaten werden
per MQTT übertragen. Der letzte abgeschlossene Sicherungsstatus wird lokal
gespeichert; ein vorheriger abgebrochener Auftrag wird nicht automatisch wiederholt.
Auch `sudo usb-extender backup` verwendet denselben Archivcode. Archive schließen
den Exportordner aus, besitzen private Dateirechte und werden vor Erfolgsmeldung
auf vollständig lesbare gzip-Daten geprüft.

Der Dienst gleicht den Webstatus etwa alle fünf Sekunden ab, auch nach CLI-Aufrufen.
`webrun=ON` bedeutet: systemd meldet aktiv **und** der konfigurierte HTTP-Endpunkt
antwortet mit 200. Bei Start wird bis zu zehn Sekunden auf Erreichbarkeit gewartet;
danach meldet der Dienst einen Hinweis und prüft weiterhin regelmäßig. ON ist keine
Bestätigung einer Browser-Anmeldung. Bei MQTT-Reconnect werden Zustände erneut
veröffentlicht; die Broker-Verfügbarkeitsmeldung zeigt getrennt online/offline.

Backups laufen im Hintergrund. Die Verarbeitung von Tasteneingaben, MQTT und
Mobile muss nicht auf das Archiv warten. Freier Speicherplatz und I/O-Auslastung
des Raspi begrenzen trotzdem die Sicherungsgeschwindigkeit.

## Home Assistant

Sind Systemsteuerung **und HA-Discovery** am Broker aktiv, werden am Gerät
„USB Extender“ fünf Entitäten angekündigt:

- Webfrontend-Schalter mit echtem `webrun`-Zustand.
- Web-Autostart-Schalter mit `autorun`-Zustand.
- Backup-Button.
- Systemstatussensor.
- Backupstatussensor mit Zeitpunkt und Dateiname als Attributen.

Beim Abschalten wird die eigene Discovery-Anmeldung entfernt. ioBroker kann die
Topics ohne HA-Discovery verwenden. Ein Web-Befehl hat dieselbe Bedeutung wie
der entsprechende CLI-Befehl.

## Installation und Rechte

Das aktualisierte Installationspaket verwenden; nur Python-Dateien zu kopieren
reicht nicht. Der Installer ergänzt einen lokalen systemd-Socket und einen
kurzlebigen Helferdienst. Nur root und die Gruppe `ugso-usbhub` dürfen den Socket
verwenden. Der Helfer akzeptiert ausschließlich start/stop/status/enable/disable
für die feste Unit `ugso-usbhub-web.service`. Keine freien Unitnamen, Pfade oder
Shellbefehle, keine allgemeinen sudo-Rechte für den MQTT-Prozess. Backups laufen
weiter als unprivilegierter Dienstbenutzer.

## USB Extender Cards – ein separates Paket

Das [gemeinsame Home-Assistant-Kartenpaket](https://github.com/rockbaer2007/usb-extender-cards)
bietet eine eigenständige Custom Card mit Mushroom-/Bubble-Stil, Betriebs- und
Autostart-Schaltern, Backup, Status und „Webfrontend öffnen“. Beim Klick öffnet
die Karte einen Wartetab, fordert den Start an und wechselt nach Rückmeldung zur
eingestellten URL. Zeitlimit, Fehleranzeige und Popup-Fallback sind enthalten.
Sie nutzt HA-Entitäten statt direkter Broker-Zugangsdaten. Karten separat über
HACS oder manuell installieren; der Pi-Installer verändert kein HA-Dashboard.
Der Systembereich enthält den Paketlink. Die native Discovery funktioniert auch
ohne diese Karte. Echte HA-/Companion-Praxisprüfung bleibt im Kartenrepo dokumentiert.
