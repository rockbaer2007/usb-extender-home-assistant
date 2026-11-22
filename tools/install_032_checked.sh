#!/usr/bin/env bash
# Run from the extracted 0.1.32 package; preserve all live data and pairings.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Bitte mit sudo bash tools/install_032_checked.sh starten.'; exit 1; }
cd "$(dirname "$0")/.."
grep -q '__version__ = "0.1.32"' ugso_usbhub/__init__.py
sha256sum -c SHA256SUMS >/dev/null
bash tools/backup_active.sh
umask 077
checksums="/var/backups/usbextender-before-032-metadata-$(date +%Y%m%d-%H%M%S).sha256"
core_active=0;web_active=0
systemctl is-active --quiet ugso-usbhub && core_active=1
systemctl is-active --quiet ugso-usbhub-web && web_active=1
restore_services() {
  if (( core_active )); then systemctl start ugso-usbhub; fi
  if (( web_active )); then systemctl start ugso-usbhub-web; fi
}
trap restore_services EXIT
systemctl stop ugso-usbhub-web ugso-usbhub
for name in config.json switches.json mobile-identity.json mobile-trust.json mobile-devices.json; do
  if [[ -f /var/lib/ugso-usbhub/$name ]]; then sha256sum "/var/lib/ugso-usbhub/$name"; fi
done > "$checksums"
since=$(date '+%Y-%m-%d %H:%M:%S')
bash install.sh
restore_services
sleep 5
sha256sum -c "$checksums"
ugso-usbhub --version
systemctl show ugso-usbhub ugso-usbhub-web -p Id -p ActiveState -p SubState -p NRestarts --no-pager
python3 - <<'PY'
import json,time
s=json.load(open('/run/ugso-usbhub/status.json'))
assert s.get('version')=='0.1.32' and abs(time.time()-s.get('updated',0))<15,s.get('version')
print('Dienstversion:',s['version'],'Mobile aktiv:',s.get('mobile',{}).get('active'),'Fehler:',s.get('errors',{}))
PY
journalctl -u ugso-usbhub -u ugso-usbhub-web --since "$since" --no-pager -n 20
echo "Update geprüft; Metadaten-Prüfsummen: $checksums"
