#!/usr/bin/env bash
# Only run on the disposable CI runner after install.sh, never a user host.
set -euo pipefail
sudo runuser -u ugso-usbhub -- /opt/ugso-usbhub/current/.venv/bin/python - <<'PY'
from ugso_usbhub.web_control import request
before=request('status')
try:
    assert request('start')['running']
    assert not request('stop')['running']
    assert request('enable')=={'running':True,'autorun':True}
    assert request('disable')=={'running':False,'autorun':False}
    try: request('start ssh.service')
    except ValueError: pass
    else: raise AssertionError('Unapproved service operation accepted')
finally:
    request('enable' if before['autorun'] else 'disable')
    request('start' if before['running'] else 'stop')
print('Unprivileged web-control socket: start/stop, enable/disable, rejection and restore OK')
PY
