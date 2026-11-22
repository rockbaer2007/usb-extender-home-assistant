#!/usr/bin/env bash
# Local shell regression: restrictive caller, readable code, private backups.
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
source <(awk '/^step '\''System und Voraussetzungen prüfen'\''/ {exit} {print}' install.sh)
trap - ERR
[[ $(umask) == 0022 ]]
test_root=$(mktemp -d)
trap 'rm -f "$test_root/archive" "$test_root/tar-umask"; rmdir "$test_root"' EXIT
tar() { umask > "$test_root/tar-umask"; touch "$test_root/archive"; }
BACKUP="$test_root/archive"
backup_command=$(awk '/^  \(umask 077; tar -czf/ {print}' install.sh)
[[ -n "$backup_command" ]]
eval "$backup_command"
[[ $(cat "$test_root/tar-umask") == 0077 ]]
[[ $(umask) == 0022 ]]
printf 'Installer umask: caller 077 -> code 022; backup 077; parent remains 022 OK\n'
