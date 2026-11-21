# Änderungen

## 0.1.2 – 21. November 2026

- Lokale Discovery-Fehler werden abgefangen und in der Diagnose angezeigt;
  MQTT-Daten werden unabhängig davon weitergesendet.
- Discovery pro Broker ausdrücklich wählbar: **Aus – nur MQTT-Daten senden**
  oder **Home Assistant – Geräteauslöser anmelden**. Neue Konfigurationen starten
  ohne Discovery; vorhandene Einstellungen bleiben erhalten.
- Bekannte eigene retained Discovery-Konfigurationen werden beim Abschalten und
  Wiederverbinden zurückgenommen. Ältere Versionen werden anhand der lokalen
  Konfigurationssicherungen berücksichtigt. Fremde Discovery-Einträge bleiben erhalten.
- Tastaturschreibweisen wie `key:tab` oder `key_tab` werden zu `KEY_TAB` vereinheitlicht;
  numerische Stream-Deck-Kennungen wie `key:0` bleiben erhalten.
- Sende-Topic und effektive Ziele stehen direkt in der Belegung. Die Ereignistabelle
  zeigt MQTT-Sendestatus, Zielbroker und Topic oder den Grund für fehlenden Versand.
- Live-Nachtest: Nach Korrektur der Tab-Belegung empfing der offene HA-MQTT-Explorer
  drei Nachrichten mit `control: KEY_TAB` und `event_type: press`.

## 0.1.1 – 21. November 2026

- Tastaturzugriff auf Raspberry Pi OS: Dienstkonto zusätzlich in der Standardgruppe
  `input`; systemd setzt diese Gruppe ebenfalls ausdrücklich. Die udev-Regel erhält
  die Standardgruppe, statt sie durch eine private Gruppe zu ersetzen.
- Installer wartet auf abgeschlossene udev-Verarbeitung und prüft Leserechte der
  erkannten Eingabegeräte unter dem tatsächlichen Dienstkonto.
- Dienststatus wird mit der Uhr des Raspberry Pi berechnet. Eine abweichende
  PC-Uhr erzeugt keine falsche Anzeige „Dienst nicht aktiv“ mehr.
- evdev-Aliase werden zu einem Tastennamen vereinheitlicht, insbesondere
  `KEY_MIN_INTERESTING,KEY_MUTE` zu `KEY_MUTE`. Bestehende Alias-Zuordnungen bleiben nutzbar.
- Bestätigte Browserdiagnose auf dem Raspi: Eingabegeräte und MQTT erkannt,
  aber `Permission denied` beim Öffnen der Eingabekanäle. Nach Korrektur der Gruppe
  `input` kommen HCT-Tastatur- und Volumeregler-Ereignisse in der Liveansicht an.

## 0.1.0 – 21. November 2026

Erste eigenständige Fassung von **USB Extender für Home Assistant**.

- Drei unabhängig konfigurierte MQTT-Broker, Ziele pro Gerät und Taste.
- USB-Bestandsliste, bewusst freigegebene evdev-Eingaben und Stream-Deck-Adapter.
- Medien-/Makrotasten, Halten, Wiederholung und Drehregler-Ereignisse.
- Stream-Deck-Icons, Text, Helligkeit und MQTT-Zustandsrückmeldungen.
- Eigene Iconordner, Einzelbilder, ZIP und lokale Elgato-Iconpack-Archive.
- Separat abschaltbare, passwortgeschützte Weboberfläche.
- Neunstufiger Installer mit Prüfung und Nachinstallation fehlender Pakete,
  Update-Sicherung, separatem Dienstkonto, getrennten Prozessen und Programm-Rückschaltung.
- Anleitung, automatisierte Prüfungen und kopierbares Raspi-Installations-ZIP.

Physischer Raspberry-Pi-/USB-Test steht vor dem Praxiseinsatz noch aus.
