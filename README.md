# USB Extender für Home Assistant

**USB-Geräte und Stream Decks über MQTT verbinden – für Raspberry Pi.**

Version **0.1.3** · Privates Projekt · Stand 21. November 2026

Ein Raspberry Pi 4 wird zur USB-/MQTT-Brücke: Tastaturen, Medientasten,
Makropads und unterstützte physische Stream Decks liefern Eingaben an bis zu
drei unabhängige MQTT-Broker. Die Weboberfläche dient nur zur Einrichtung und
lässt sich vollständig abschalten. Der USB-/MQTT-Dienst arbeitet weiter.

Eigenständiges Projekt, keine offizielle Software von Home Assistant oder Elgato.

## Im Paket

- Anlernmodus pro USB-Gerät mit editierbarer Tastenliste: Press, Release,
  Switch ON/OFF, optionale Leer-Rücksetzung und Lautstärkewiederholung.
- Installer mit neun sichtbaren Schritten und Paketprüfung. Fehlende apt- und
  Python-Pakete werden installiert; bestehende Konfiguration wird gesichert.
- Drei getrennte MQTT-Verbindungen mit Benutzer/Passwort, optional TLS und
  eigener CA-Datei; automatische Wiederverbindung je Broker.
- Zielauswahl pro Gerät und pro Tastenbelegung. Eine Taste kann an mehrere
  Broker senden. Pro Gerät genau ein Broker für Display-Rückmeldungen.
- USB-Bestandsliste; Freigabe jeder Eingabequelle ausdrücklich in der Oberfläche.
- Tasten drücken/loslassen/halten, gedrosselte Wiederholung und relative
  Drehbewegungen, soweit das Gerät sie über evdev bzw. den Stream-Deck-Treiber liefert.
- Stream-Deck-Tasten mit eigenen Icons, Text und Helligkeit; Zustandsanzeige über
  ein MQTT-Topic oder einen gezielten Displayauftrag.
- Iconbibliothek mit lokalem Ordnerimport, Einzelbildern, ZIP und lokal vorliegenden
  `.streamDeckIconPack`-Dateien im ZIP-Format. Name, Sammlung, Tags, Autor und
  Lizenztext bleiben verfügbar.
- Home-Assistant-MQTT-Geräteauslöser über Discovery für angelegte Belegungen.
- Passwortgeschützte Konfiguration; atomare Speicherung und zehn automatische
  Konfigurationssicherungen. MQTT-Passwörter werden nicht an den Browser zurückgeliefert.

## Tasten anlernen (ab 0.1.3)

1. Unter **USB-Geräte** das Gerät freigeben, seine Zielbroker wählen und speichern.
2. Unter **Tasten & Anzeigen** das Gerät wählen und **Anlernen starten** drücken.
3. Gewünschte Tasten nacheinander drücken und loslassen. Jede neue Taste erscheint
   einmal als Listenzeile; bereits vorhandene Belegungen werden nicht verdoppelt.
4. **Anlernen beenden**, dann **Tasten übernehmen** und **Speichern**.
   Alternativ die neue Liste verwerfen. Erst gespeicherte Zeilen senden MQTT.
5. Name, Aktivierung, Topics und Icon direkt in der Liste anpassen. **Bearbeiten**
   öffnet die Brokerwahl und bei Lauter/Leiser die Wiederholungszeiten.

Während des Anlernens sendet das gewählte Gerät keine Aktionen; andere Geräte
laufen weiter. Bei geschlossener oder unerreichbarer Weboberfläche endet diese
Pause spätestens nach 15 Sekunden. Anlernentwürfe liegen bis zur Übernahme nur
im Browser; vorhandene Einstellungen und Einzelbelegungen bleiben erhalten.

| Kanal | Nachricht | Vorgabe |
| --- | --- | --- |
| Press | `press` beim Drücken | an |
| Release | `release` beim Loslassen | an |
| Switch | `ON` beim Drücken, `OFF` beim Loslassen | an |
| Press+ | Press danach nach 50 ms leer zurücksetzen | aus |
| Release+ | Release danach nach 50 ms leer zurücksetzen | aus |

Die Plus-Optionen gelten für das jeweilige Press-/Release-Topic. Ihre Leer-
Nachricht ist kein physisches Loslassen. Switch wird niemals leer zurückgesetzt.
Beispieltopic: `ugso/usbhub/2/<geraete-id>/key_volumeup/press`; daneben gibt es
`release` und `switch`. Leere Topicfelder nutzen den Präfix des Zielbrokers,
explizite Topics werden unverändert an alle gewählten Broker gesendet.
Alle Tastenmeldungen bleiben QoS 0 und nicht retained; Offline-Eingaben werden
nicht nachgesendet. Die Anzeige „übergeben“ bestätigt die lokale MQTT-Übergabe,
nicht den Empfang oder die Entitätsanlage im Zielsystem.

**Lauter/Leiser:** `KEY_VOLUMEUP` und `KEY_VOLUMEDOWN` starten beim Anlernen mit
Wiederholung an: nach 500 ms alle 150 ms eine weitere Press-Nachricht. Zeiten sind
einstellbar; Release, Switch und vorhandene Einzelbelegungen werden dadurch nicht
wiederholt. Loslassen, Abziehen und eine Konfigurationsübernahme beenden die
Wiederholung. Nach 30 Sekunden greift ein Sicherheitsstopp. Das Gerät muss
Drücken und Loslassen zuverlässig melden. Den Lautstärkeschritt und die
Zielaktion legt die HA-Automation bzw. ioBroker-Logik fest.

Bei aktivierter HA-Discovery werden Press/Release als Geräteauslöser mit passendem
Payloadfilter und Switch als MQTT-Binärsensor angemeldet. Der Binärsensor zeigt
die gedrückte Taste an; zum Steuern anderer Geräte ist eine Zuordnung/Automation
erforderlich. Für ioBroker Discovery ausgeschaltet lassen und die MQTT-Topics
verwenden. Der tatsächliche ioBroker-Tastenempfang ist noch separat zu klären.

## Installation auf dem Raspberry Pi

Empfohlen: **Raspberry Pi OS Lite 64 Bit, Bookworm oder neuer**, Raspberry Pi 4,
Python mindestens 3.11, Internetzugang für apt und PyPI. Auch die Installation
auf 32-Bit-Pi-OS ist vorgesehen, aber noch nicht praktisch geprüft. Eine laufende
systemd-Installation und sudo-Rechte werden benötigt. Das ZIP ist ein
Installationspaket, kein vollständig offline installierbares ARM-Abbild.

1. ZIP auf den Pi kopieren, beispielsweise in den Home-Ordner.
2. Terminal oder SSH öffnen und ausführen:

   ```bash
   # Falls unzip noch nicht vorhanden ist:
   sudo apt-get update && sudo apt-get install -y unzip
   unzip USB-Extender-Home-Assistant-0.1.3-Raspi4.zip
   cd USB-Extender-Home-Assistant-0.1.3
   sudo bash install.sh
   ```

3. Den Installer durchlaufen lassen. Er zeigt vorhandene und fehlende Pakete,
   installiert Abhängigkeiten in einer eigenen Python-Umgebung und fragt bei der
   ersten interaktiven Installation nach einem Webpasswort mit mindestens zwölf
   Zeichen. Ohne interaktives Terminal anschließend setzen:

   ```bash
   sudo usb-extender password
   ```

4. Weboberfläche starten:

   ```bash
   sudo usb-extender web start
   ```

5. `http://<IP-des-Raspi>:8098` im Browser öffnen und anmelden. Die IP zeigt
   `hostname -I`. Keine spitzen Klammern in die Adresse übernehmen.

Der Installer aktiviert **nur den USB-/MQTT-Dienst automatisch beim Booten**.
Bei einer Neuinstallation bleibt der Webdienst zunächst aus. Bei einer späteren
Installation bleiben Daten und ein bereits laufender Webdienst erhalten.

### Die neun Installationsschritte

1. Linux, Architektur, systemd und Paketinhalt prüfen.
2. Vorhandene Systempakete auflisten und Fehlendes installieren.
3. Dienste für eine konsistente Sicherung stoppen und bestehende Daten sichern.
4. Separates Dienstkonto und Datenordner anlegen.
5. Neue Programmversion samt eigener Python-Umgebung installieren.
6. Python-Bibliotheken einschließlich SVG-Rasterung und Konfiguration prüfen.
7. USB-Berechtigungen und zwei getrennte systemd-Dienste einrichten.
8. USB-/MQTT-Dienst starten und aktiven Status prüfen.
9. Abschlussübersicht mit Adresse und Bedienbefehlen anzeigen.

Schlägt ein Update fehl, werden vorher laufende Dienste wieder gestartet; nach
einem bereits erfolgten Programmwechsel wird der alte Programmverweis zurückgesetzt.
Die Datensicherung liegt unter `/var/backups/`. Programmversionen werden unter
`/opt/ugso-usbhub/releases/` getrennt abgelegt. Es wird keine vorhandene Konfiguration
durch eine Demokonfiguration ersetzt.

## Erstes Gerät einrichten

### 1. MQTT-Broker

Unter **MQTT-Broker** einen Platz aktivieren. Host, Port und gegebenenfalls
Benutzer/Passwort eintragen. Ein eigenes, eindeutiges Topic-Präfix wählen.
Bei mehreren Extendern dürfen deren Präfixe auf demselben Broker nicht kollidieren.
TLS prüft Zertifikate; eine eigene CA-Datei kann auf dem Pi hinterlegt werden.
Ein leer gelassenes Passwortfeld erhält ein bereits gespeichertes Passwort.
Die separate Checkbox löscht es ausdrücklich.

**Discovery ist von der Datenübertragung getrennt.** Für jeden Broker gibt es
die Auswahl **Aus – nur MQTT-Daten senden** oder **Home Assistant – Geräteauslöser
anmelden**. Für ioBroker zunächst **Aus** wählen; MQTT-Ereignisse werden trotzdem
gesendet. Die verwendete HA-Discovery-Komponente `device_automation` wird nicht
von jedem ioBroker-Discovery-Adapter unterstützt. Neue Profile starten mit Discovery aus;
bestehende Profile werden nicht ungefragt umgestellt.

Beim Abschalten nimmt der Extender bekannte eigene retained Discovery-Ankündigungen
zurück. Bereits bekannte Namen bleiben lokal in `discovery.json` gespeichert,
damit die Bereinigung bei einem Verbindungsabbruch wiederholt werden kann.
Für den Wechsel von 0.1.0/0.1.1 werden eigene Zuordnungen aus den letzten zehn
Konfigurationssicherungen berücksichtigt. Fremde Discovery-Topics werden nicht gelöscht.

Unter **Vorgabe für neue Geräte** die gewünschten Broker ankreuzen. Speichern.

**Beispiel: ioBroker produktiv und Testsystem gleichzeitig.** Broker 1 mit dem
MQTT-Server des Produktivsystems verbinden, Broker 2 mit dem MQTT-Server des
Testsystems. An Gerät oder Belegung beide Ziele ankreuzen. Für identische Topics
bei beiden dasselbe Präfix oder in der Belegung ein festes Sende-Topic setzen.
Die Eingabe-Payload ist dann bytegleich. Die Übertragungen laufen unabhängig,
aber ohne Garantie auf exakt gleichzeitige Ankunft. Bei Ausfall eines Brokers
empfangen die anderen weiter; ausgefallene Eingaben werden nicht nachgesendet.
Dieselben Zugangsdaten sind nicht erforderlich. Wenn zwei Plätze auf denselben
MQTT-Server mit demselben Topic zeigen, entstehen doppelte Nachrichten.

### 2. USB-Gerät freigeben

Gerät einstecken, **USB-Geräte** öffnen. Bei neu eingesteckten Geräten die Seite
über einen anderen Menüpunkt erneut aufrufen. Die Bestandsliste wird im Dienst
alle fünf Sekunden erneuert. Namen vergeben, **Gerät für Eingaben freigeben**
aktivieren, MQTT-Ziele wählen, speichern.

Wichtig: Eine freigegebene Tastatur kann auch normale Buchstaben liefern.
Nur dedizierte Eingabegeräte freigeben, nicht die Tastatur für persönliche Eingaben.
Es wird kein Linux-Eingabegerät exklusiv gesperrt; das Betriebssystem kann weiterhin
darauf reagieren. Zwei Treiber verarbeiten dasselbe Stream Deck nicht parallel.

Geräte werden nach USB-Hersteller-/Produkt-ID und, wenn vorhanden, Seriennummer
erkannt. Ohne USB-Seriennummer gehört die Zuordnung zum physischen USB-Port:
nach Umstecken gegebenenfalls neu zuordnen. Mehrere gleichartige Geräte bleiben
an unterschiedlichen Ports unterscheidbar. Stream Decks ohne USB-Seriennummer
werden zusätzlich über ihren aktuellen libusb-Bus-/Adresspfad geöffnet.

### 3. Taste belegen

**Tasten & Anzeigen** öffnen, am Gerät drücken und neben dem passenden Ereignis
**Übernehmen** wählen. Die Ereignistabelle zeigt nur freigegebene Eingabegeräte.
Beispiele:

| Steuerelement | Bedeutung |
|---|---|
| `KEY_PLAYPAUSE` | Wiedergabe / Pause |
| `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN` | Lautstärke |
| `KEY_MUTE` | Stumm |
| `KEY_NEXTSONG`, `KEY_PREVIOUSSONG`, `KEY_STOPCD` | Mediensteuerung |
| `key:0` | Erste Stream-Deck-Taste, Zählung beginnt bei null |
| `dial:0` | Erster Stream-Deck-Drehregler, sofern unterstützt |
| `touchscreen` | Touch-Ereignis eines unterstützten Stream Decks |

**Drücken** und **Gedrückt halten** sind getrennte Ereignisse; Halten löst nach
0,7 Sekunden zusätzlich zum ersten Drücken aus. Wiederholungen werden auf etwa
sechs pro Sekunde begrenzt. Es gibt derzeit keine Doppelklick-Erkennung.

Normalerweise die Geräteziele übernehmen. Alternativ die Checkbox ausschalten
und einzelne Zielbroker ankreuzen. Ein eigenes Topic und eine feste Payload sind
optional. Die tatsächlichen Zielbroker und vollständigen Sende-Topics werden direkt
in der Belegung angezeigt. Für Tastaturen heißen die Steuerelemente beispielsweise
`KEY_TAB`. Die Schreibweisen `key:tab` und `key_tab` werden beim Speichern
vereinheitlicht. Bei Stream Decks bleibt die erste Taste `key:0`.

Ohne Vorgabe sendet der Dienst ein JSON-Ereignis auf:

```text
<Topic-Präfix>/event/<Geräte-ID>/<Belegungs-ID>
```

```json
{"device":"Geräte-ID","control":"key:0","event_type":"press","value":1}
```

Eingaben verwenden QoS 0, niemals retained. Bei nicht verbundenem Broker wird
keine Eingabe für später gespeichert. Das ist keine Exactly-once-Zustellung.
Zwei vorhandene Brokerverbindungen arbeiten weiter, wenn die dritte ausfällt.

In der Ereignistabelle zeigt die Spalte **MQTT** den Sendestatus und die Ziele.
Bei **Keine passende gespeicherte Belegung** die passende Eingabe übernehmen und
speichern. Bei **Kein MQTT-Ziel ausgewählt** mindestens einen Broker ankreuzen.
Bei **Ziel deaktiviert oder nicht verbunden** die Brokerverbindung prüfen.
**An MQTT übergeben** bestätigt die lokale Übergabe an den MQTT-Client (QoS 0);
ein Empfang im MQTT Explorer bestätigt zusätzlich die Ankunft am Broker.

### 4. Mit Home Assistant verbinden

Home Assistant muss über seine MQTT-Integration mit dem gewünschten Broker
verbunden sein. Bei aktivierter Discovery erscheinen die gespeicherten
Tastenbelegungen als MQTT-Geräteauslöser. In einer HA-Automation das USB-Gerät
und die passende Taste wählen und die gewünschte HA-Aktion ergänzen.

Alternativ einen MQTT-Auslöser mit dem in der Belegung festgelegten Topic benutzen.
Der Extender benötigt keinen Home-Assistant-Zugriffstoken. Er führt selbst keine
frei eingegebenen Shellbefehle aus und verändert keine HA-Systemdateien.

## Stream-Deck-Icons und Zustände

Unter **Iconbibliothek** eigene Dateien oder ein lokal vorliegendes Paket importieren.
Unterstützt: PNG, JPG/JPEG, SVG, GIF und WebP. Animationen werden momentan als
erstes Einzelbild importiert. Die Bilder werden als lokale 256×256-PNGs normalisiert;
der Stream-Deck-Treiber passt sie an das konkrete Gerät an.

Für einen Ordner auf dem Pi zum Beispiel:

```bash
sudo mkdir -p /var/lib/ugso-usbhub/import/meine-icons
# Bilder dorthin kopieren und für das Dienstkonto lesbar machen:
sudo chown -R ugso-usbhub:ugso-usbhub /var/lib/ugso-usbhub/import
sudo usb-extender icons /var/lib/ugso-usbhub/import/meine-icons
```

Oder den Ordnerpfad in der Weboberfläche eintragen. Ein privater Home-Ordner ist
gegebenenfalls für das Dienstkonto nicht lesbar; dann den obigen Importordner nutzen.
Die Dateien werden in die verwaltete Bibliothek kopiert. Der Ursprungsordner muss
danach nicht dauerhaft verfügbar sein.

### Elgato-Iconpacks

Lokale `.streamDeckIconPack`-Archive bzw. ZIP-Dateien können importiert werden.
Der Import liest `manifest.json`, `icons.json`, `icons/` und gegebenenfalls
`license.txt`. Eigene Bild-ZIPs benötigen diese Metadaten nicht. Archive werden
nicht ungeprüft entpackt oder ausgeführt; Pfadwechsel und Symlinks werden abgewiesen.
Grenzen: 32 MB Upload, 96 MB entpackt, 10.000 Einträge und 8 MB je Datei.

SVGs mit Skripten, externen Ressourcen oder eingebetteten Stylesheets werden
abgewiesen. Solche SVGs vorher lokal nach PNG konvertieren. Ein Importbericht
zeigt übersprungene Dateien. Ein proprietäres Nicht-ZIP-Paket wird nicht unterstützt.

Es gibt keine Marketplace-Anmeldung und keinen automatischen Download.
Packs selbst rechtmäßig herunterladen bzw. aus der lokalen Stream-Deck-Installation
übernehmen und deren Lizenz beachten. Kein gekauftes Drittanbieter-Pack liegt
diesem Projekt bei. Die Prüfung erfolgte zunächst mit eigenen Icons und einem
Testpaket im dokumentierten Elgato-Format, nicht mit jedem Marketplace-Pack.

### Anzeige einrichten

In einer Stream-Deck-Belegung Icon und Text wählen. Am Gerät einen
**Broker für Display-Rückmeldungen** auswählen. Eine Zustandsbelegung kann zum
Beispiel auf `haus/licht/state` hören, bei `ON` ein aktives Icon anzeigen und sonst
das normale Icon. Für JSON-Antworten kann ein Feldpfad wie `light.state` angegeben
werden. Hier sind exakte Topics vorgesehen, keine Wildcard-Zustandsfilter.
Home Assistant muss den Zustand ausdrücklich auf dieses MQTT-Topic veröffentlichen.

Ein direkter Displayauftrag hat das Topic:

```text
<Topic-Präfix>/display/<Geräte-ID>/set
```

```json
{"key":0,"text":"Licht an","icon":"Icon-ID aus der Bibliothek","brightness":40}
```

Nur der am Gerät eingestellte Empfangsbroker darf die Anzeige ändern. Andere
Broker werden für dieses Gerät ignoriert. MQTT darf keine beliebigen Datei-/URL-
oder Befehlszugriffe auslösen. Gespeicherte Grundbelegungen werden beim Wiederanstecken
geladen; aktuelle Zustände sollte HA retained veröffentlichen, damit sie nach einem
Neustart wieder eintreffen.

## Weboberfläche abschalten

```bash
sudo usb-extender web start      # jetzt starten
sudo usb-extender web stop       # jetzt stoppen: HTTP-Listener beendet
sudo usb-extender web status     # systemd-Status
sudo usb-extender web enable     # jetzt starten und bei jedem Boot
sudo usb-extender web disable    # jetzt stoppen und Autostart entfernen
```

Das Schließen des Browserfensters beendet den Webdienst nicht. `web stop` beendet
nur die Weboberfläche, nicht USB und MQTT. Status und die letzten 100 Eingaben
liegen im regulären Dienstbetrieb im RAM unter `/run/ugso-usbhub/status.json`.
Der zyklische Status erzeugt dadurch keine dauerhaften Schreibzugriffe auf die SD-Karte.

## Status, Sicherung und Update

```bash
sudo usb-extender status
sudo usb-extender devices
sudo usb-extender backup
sudo journalctl -u ugso-usbhub -n 50
sudo systemctl restart ugso-usbhub
```

`backup` erstellt eine geschützte TAR.GZ unter `/var/lib/ugso-usbhub/exports/` mit
Einstellungen, Zugangsdaten, Icons und Konfigurationssicherungen. Diese Datei
vertraulich behandeln. Vor einer Wiederherstellung beide Dienste stoppen, Archiv
kontrolliert nach `/var/lib/` zurückspielen und den Eigentümer `ugso-usbhub` erhalten.

Für ein Update das neue ZIP separat entpacken und wieder `sudo bash install.sh`
ausführen. Installationssicherungen werden nicht automatisch gelöscht. Die letzten
zehn automatischen **Konfigurations**sicherungen werden rollierend aufbewahrt.

Die internen Python-, Dienst- und Datenordnernamen `ugso_usbhub` / `ugso-usbhub`
bleiben technische Kennungen. Der sichtbare Produktname ist
**USB Extender für Home Assistant**; der Bedienbefehl lautet **usb-extender**.

## Sicherheit und Grenzen

- Oberfläche mit Passwort und einstündiger Sitzung, keine Standardzugangsdaten
  in der Installation. Neu setzen mit `sudo usb-extender password`.
- HTTP im vertrauenswürdigen lokalen Netz; nicht öffentlich weiterleiten.
  Für fremde Netze VPN oder HTTPS-Reverse-Proxy vorsehen.
- Das Dienstkonto ist Mitglied der Standardgruppe `input` für Linux-Eingabegeräte
  und erhält udev-Zugriff auf Elgato-HID-Geräte.
  Die Anwendung liest Eingaben erst nach Freigabe. Das ist eine Softwarefreigabe,
  keine zusätzliche kernelbasierte Trennung einzelner Tastaturen.
- MQTT-Passwörter müssen zum Verbinden lokal lesbar gespeichert sein; Datei und
  Backups sind geschützt. Das Webpasswort liegt nur als PBKDF2-SHA256-Hash vor.
- Linux kann beliebige USB-Geräte auflisten. Proprietäre Protokolle von Kameras,
  Druckern, Audiointerfaces, seriellen Geräten oder anderen Makropads benötigen
  jeweils eigene Adapter; allein die Erkennung bedeutet keine Steuerbarkeit.
- Stream-Deck-Unterstützung basiert auf `python-elgato-streamdeck` 0.10.0
  (u. a. Original/MK.2, Mini, XL, Neo, Pedal, Plus und weitere dort unterstützte
  Modelle). Physische Geräte sind in diesem Projekt noch nicht praktisch geprüft.
  Der Touchscreen wird als Ereignisquelle angebunden, nicht als frei gestaltbarer
  Displaybereich. Es gibt zunächst eine feste Belegung ohne Profil-/Seitenwechsel.
- Stream Deck Mobile lässt sich nicht wie ein USB-Stream-Deck direkt mit dem Pi
  koppeln. Ein eigenständiges Tablet-Deck ist in dieser Version nicht enthalten.
- Mehrere Geräte mit LCD benötigen gegebenenfalls einen aktiven USB-Hub mit
  eigener Stromversorgung. Ein Pi-Netzteil ersetzt keine Hub-Stromversorgung.

## Entwicklung und Prüfung

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -v
```

Siehe [TESTBERICHT.md](TESTBERICHT.md), [STAND.md](STAND.md),
[ROADMAP.md](ROADMAP.md) und [CHANGELOG.md](CHANGELOG.md).

Die Screenshots in `docs/screenshots/` zeigen **lokale Beispieldaten**, keine
bestätigten Raspberry-Pi-Hardwareverbindungen.

## Verwendete Schnittstellen

- [Python Elgato Stream Deck](https://github.com/abcminiuser/python-elgato-streamdeck)
- [Elgato Iconpack-Format](https://docs.elgato.com/stream-deck/icons/getting-started/)
- [Paho MQTT Python](https://eclipse.dev/paho/files/paho.mqtt.python/html/)
- [Linux evdev](https://python-evdev.readthedocs.io/)
- [Home Assistant MQTT-Geräteauslöser](https://www.home-assistant.io/integrations/device_trigger.mqtt/)

Abhängigkeiten behalten ihre jeweiligen Lizenzen. Keine fremden Marketplace-Inhalte
oder vertraulichen Einstellungen werden im Repository oder Installations-ZIP mitgeliefert.
