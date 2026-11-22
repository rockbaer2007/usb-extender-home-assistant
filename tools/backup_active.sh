#!/usr/bin/env bash
# Active release + all application data. Older releases are not changed.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Bitte mit sudo bash tools/backup_active.sh starten.'; exit 1; }
active_release=$(readlink -f /opt/ugso-usbhub/current)
case "$active_release" in /opt/ugso-usbhub/releases/*) ;; *) echo 'Unerwarteter Programmpfad'; exit 1 ;; esac
mkdir -p /var/backups
needed=$(du -sk "$active_release/" /var/lib/ugso-usbhub | awk '{s+=$1} END {print s}')
available=$(df -Pk /var/backups | awk 'NR==2 {print $4}')
if (( available < needed + 131072 )); then
  echo 'Zu wenig freier Speicher fuer aktive Sicherung plus Reserve.'; df -h /var/backups; exit 1
fi
core_active=0; web_active=0
systemctl is-active --quiet ugso-usbhub && core_active=1
systemctl is-active --quiet ugso-usbhub-web && web_active=1
restore_services() {
  if (( core_active )); then systemctl start ugso-usbhub; fi
  if (( web_active )); then systemctl start ugso-usbhub-web; fi
}
trap restore_services EXIT
systemctl stop ugso-usbhub-web ugso-usbhub
target_backup="/var/backups/usbextender-active-before-diagonal-$(date +%Y%m%d-%H%M%S).tar.gz"
umask 077
printf 'Sichere aktiven Programmstand und alle Nutzdaten: %s\n' "$target_backup"
tar -czf "$target_backup" -C / var/lib/ugso-usbhub "${active_release#/}" opt/ugso-usbhub/current \
  etc/systemd/system/ugso-usbhub.service etc/systemd/system/ugso-usbhub-web.service
gzip -t "$target_backup"
tar -tzf "$target_backup" >/dev/null
sha256sum "$target_backup"
printf 'Sicherung geprueft. Dienste werden in ihren vorherigen Laufzustand versetzt.\n'
