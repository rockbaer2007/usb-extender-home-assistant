#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
# Public program files must remain readable by the unprivileged service user,
# even when invoked from a root shell with a restrictive inherited umask.
umask 022
TOTAL=9
STEP=0
BASE=/opt/ugso-usbhub
STATE=/var/lib/ugso-usbhub
SOURCE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RELEASE=""
PREVIOUS=""
SWITCHED=0
CORE_WAS_ACTIVE=0
WEB_WAS_ACTIVE=0

step() {
  STEP=$((STEP+1))
  printf '\n\033[1;36m[%d/%d] %s\033[0m\n' "$STEP" "$TOTAL" "$1"
  printf '  ['
  for ((j=1;j<=TOTAL;j++)); do if ((j<=STEP)); then printf '#'; else printf '.'; fi; done
  printf ']\n'
}
die() { printf '\nFEHLER: %s\n' "$*" >&2; exit 1; }
rollback() {
  local code=$?
  trap - ERR
  printf '\nInstallation fehlgeschlagen (Schritt %s, Code %s).\n' "$STEP" "$code" >&2
  if ((SWITCHED)); then
    systemctl stop ugso-usbhub-web.service ugso-usbhub.service || true
    if [[ -n "$PREVIOUS" && -d "$PREVIOUS" ]]; then
      ln -sfn "$PREVIOUS" "$BASE/current"
      printf 'Vorherige Programmversion wieder aktiviert.\n' >&2
    fi
  fi
  ((CORE_WAS_ACTIVE)) && systemctl start ugso-usbhub.service || true
  ((WEB_WAS_ACTIVE)) && systemctl start ugso-usbhub-web.service || true
  printf 'Einstellungen und Icons in %s bleiben erhalten.\n' "$STATE" >&2
  exit "$code"
}
trap rollback ERR

step 'System und Voraussetzungen prüfen'
[[ $EUID -eq 0 ]] || die 'Bitte mit sudo bash install.sh starten.'
[[ $(uname -s) == Linux ]] || die 'Der Installer ist für Linux.'
command -v apt-get >/dev/null || die 'Raspberry Pi OS / Debian mit apt wird benötigt.'
command -v systemctl >/dev/null || die 'systemd wird benötigt.'
[[ -d /run/systemd/system ]] || die 'systemd muss als Systemdienst laufen.'
ARCH=$(uname -m)
printf '  Architektur: %s\n' "$ARCH"
case "$ARCH" in aarch64|armv7l|armv8l|x86_64) ;; *) die "Nicht unterstützte Architektur: $ARCH" ;; esac
if [[ -r /proc/device-tree/model ]]; then printf '  Gerät: '; tr -d '\0' </proc/device-tree/model; printf '\n'; fi
[[ -f "$SOURCE/pyproject.toml" && -d "$SOURCE/ugso_usbhub" ]] || die 'Installationspaket unvollständig.'
if systemctl is-active --quiet ugso-usbhub.service; then CORE_WAS_ACTIVE=1; fi
if systemctl is-active --quiet ugso-usbhub-web.service; then WEB_WAS_ACTIVE=1; fi
if [[ -L "$BASE/current" ]]; then PREVIOUS=$(readlink -f "$BASE/current"); fi

step 'Benötigte Systempakete prüfen und Fehlendes installieren'
packages=(python3 python3-venv python3-dev build-essential libhidapi-libusb0 libusb-1.0-0 libcairo2 libffi-dev libjpeg-dev zlib1g-dev libwebp-dev libfreetype6-dev libopenjp2-7-dev pkg-config fonts-dejavu-core ca-certificates unzip)
missing=()
for package in "${packages[@]}"; do
  if [[ $(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true) == 'install ok installed' ]]; then
    printf '  OK       %s\n' "$package"
  else
    printf '  FEHLT    %s\n' "$package"
    missing+=("$package")
  fi
done
if ((${#missing[@]})); then
  printf '\n  Paketlisten aktualisieren und %s fehlende Pakete installieren ...\n' "${#missing[@]}"
  apt-get update
  apt-get install -y --no-install-recommends "${missing[@]}"
else
  printf '  Alle Systempakete vorhanden. Keine Neuinstallation erforderlich.\n'
fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 oder neuer nötig (Raspberry Pi OS Bookworm/Trixie)"'

step 'Vorhandene Konfiguration und Iconbibliothek sichern'
systemctl stop ugso-usbhub-web.service ugso-usbhub.service 2>/dev/null || true
if [[ -d "$STATE" ]]; then
  BACKUP="/var/backups/ugso-usbhub-$(date +%Y%m%d-%H%M%S).tar.gz"
  mkdir -p /var/backups
  (umask 077; tar -czf "$BACKUP" -C /var/lib ugso-usbhub)
  chmod 600 "$BACKUP"
  printf '  Sicherung: %s\n' "$BACKUP"
else
  printf '  Neuinstallation: noch keine Daten vorhanden.\n'
fi

step 'Dienstkonto und Datenordner anlegen'
getent group ugso-usbhub >/dev/null || groupadd --system ugso-usbhub
getent group input >/dev/null || groupadd --system input
id ugso-usbhub >/dev/null 2>&1 || useradd --system --gid ugso-usbhub --home-dir "$STATE" --shell /usr/sbin/nologin ugso-usbhub
usermod -a -G input ugso-usbhub
install -d -o ugso-usbhub -g ugso-usbhub -m 750 "$STATE" "$STATE/import" "$STATE/icons" "$STATE/backups"
install -d -m 755 "$BASE/releases"

step 'Programm und Python-Pakete installieren'
VERSION=$(python3 -c 'import sys,tomllib; print(tomllib.load(open(sys.argv[1],"rb"))["project"]["version"])' "$SOURCE/pyproject.toml")
RELEASE="$BASE/releases/$VERSION-$(date +%Y%m%d-%H%M%S)"
install -d -m 755 "$RELEASE"
cp "$SOURCE/pyproject.toml" "$SOURCE/requirements.txt" "$SOURCE/README.md" "$RELEASE/"
cp -R "$SOURCE/ugso_usbhub" "$RELEASE/"
python3 -m venv "$RELEASE/.venv"
"$RELEASE/.venv/bin/python" -m pip install --upgrade pip
"$RELEASE/.venv/bin/python" -m pip install -r "$RELEASE/requirements.txt"
"$RELEASE/.venv/bin/python" -m pip install --no-deps "$RELEASE"

step 'Bibliotheken und Konfiguration prüfen'
"$RELEASE/.venv/bin/python" - <<'PY'
from PIL import Image
import paho.mqtt.client
import evdev
import cairosvg
from StreamDeck.DeviceManager import DeviceManager
DeviceManager().enumerate()
cairosvg.svg2png(bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10" fill="red"/></svg>')
print('  OK: MQTT, Bildverarbeitung, SVG, evdev und Stream-Deck-Treiber')
PY
runuser -u ugso-usbhub -- env UGSO_USB_HOME="$STATE" "$RELEASE/.venv/bin/ugso-usbhub" init
NEEDS_PASSWORD=$(UGSO_USB_HOME="$STATE" "$RELEASE/.venv/bin/python" -c 'from ugso_usbhub.storage import load_config; print(int(not bool(load_config()["password_hash"])))')
if [[ $NEEDS_PASSWORD == 1 ]]; then
  if [[ -t 0 ]]; then
    printf '\n  Ein Passwort schützt die Weboberfläche. Bitte jetzt festlegen.\n'
    UGSO_USB_HOME="$STATE" "$RELEASE/.venv/bin/ugso-usbhub" password
  else
    printf '  Ohne Terminal: Webpasswort später mit sudo ugso-usbhub password setzen.\n'
  fi
fi
chown -R ugso-usbhub:ugso-usbhub "$STATE"

step 'USB-Berechtigungen und getrennte systemd-Dienste einrichten'
install -m 644 "$SOURCE/systemd/70-ugso-usbhub.rules" /etc/udev/rules.d/70-ugso-usbhub.rules
udevadm control --reload-rules
udevadm trigger --subsystem-match=input
udevadm trigger --subsystem-match=usb
udevadm settle --timeout=15
printf '  Eingaberechte des Dienstkontos prüfen ...\n'
runuser -u ugso-usbhub -- env UGSO_USB_HOME="$STATE" "$RELEASE/.venv/bin/python" - <<'PY'
from ugso_usbhub.hardware import inventory
import os
bad = []
for device in inventory():
    if device['kind'] == 'input':
        for path in device['inputs']:
            readable = os.access(path, os.R_OK)
            print('  ' + ('OK       ' if readable else 'WARNUNG  ') + path)
            if not readable:
                bad.append(path)
if bad:
    print('  Einige Eingabegeräte sind nicht lesbar. Details unter System in der Weboberfläche.')
PY
install -m 644 "$SOURCE/systemd/ugso-usbhub.service" /etc/systemd/system/ugso-usbhub.service
install -m 644 "$SOURCE/systemd/ugso-usbhub-web.service" /etc/systemd/system/ugso-usbhub-web.service
install -m 644 "$SOURCE/systemd/ugso-usbhub-control.socket" /etc/systemd/system/ugso-usbhub-control.socket
install -m 644 "$SOURCE/systemd/ugso-usbhub-control@.service" /etc/systemd/system/ugso-usbhub-control@.service
install -m 755 "$SOURCE/scripts/ugso-usbhub" /usr/local/bin/ugso-usbhub
install -m 755 "$SOURCE/scripts/ugso-usbhub" /usr/local/bin/usb-extender
systemctl stop ugso-usbhub-web.service ugso-usbhub.service || true
ln -sfn "$RELEASE" "$BASE/current"
SWITCHED=1
systemctl daemon-reload
systemctl enable --now ugso-usbhub-control.socket

step 'USB-/MQTT-Dienst starten und Status prüfen'
systemctl enable --now ugso-usbhub.service
sleep 3
systemctl is-active --quiet ugso-usbhub.service
if ((WEB_WAS_ACTIVE)); then systemctl start ugso-usbhub-web.service; fi
printf '  USB-/MQTT-Dienst: aktiv\n'
if (( ! WEB_WAS_ACTIVE )); then printf '  Weboberfläche: aus (kein dauerhafter HTTP-Dienst)\n'; fi

step 'Installation abgeschlossen'
printf '\n  USB Extender für Home Assistant %s\n' "$VERSION"
printf '  Weboberfläche starten:  sudo ugso-usbhub web start\n'
printf '  Weboberfläche stoppen:  sudo ugso-usbhub web stop\n'
printf '  Ohne Web-Autostart:     sudo ugso-usbhub web disable\n'
printf '  Status:                 sudo ugso-usbhub status\n'
printf '  Browser:                http://<IP-des-Raspi>:8098\n'
printf '  Daten:                  %s\n' "$STATE"
printf '\n  USB-Geräte danach gegebenenfalls einmal abziehen und wieder einstecken.\n'
printf '  Mehrere Stream Decks: aktiven USB-Hub mit eigenem Netzteil verwenden.\n'
