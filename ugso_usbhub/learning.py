"""Short-lived learning lease. Browser loss cannot mute a device indefinitely."""
import secrets
import time
from .storage import atomic_json, home, read_json
from .keymap import device_topic_names


def current():
    lease = read_json(home() / "learning.json", {})
    return lease if lease.get("expires", 0) > time.time() else {}


def command(body, config):
    lease = current()
    action = body.get("action")
    if action == "start":
        device = body.get("device")
        if not config.get("devices", {}).get(device, {}).get("enabled"):
            raise ValueError("Gerät zuerst freigeben und speichern")
        if lease:
            raise ValueError("Es läuft bereits ein Anlernmodus. Erst beenden oder 15 Sekunden warten.")
        lease = {"id": secrets.token_hex(16), "device": device,
                 "topic_name": device_topic_names(config)[device]}
    elif action in ("heartbeat", "stop"):
        if action == "stop":
            lease = read_json(home() / "learning.json", {})
        if not lease or body.get("id") != lease.get("id"):
            raise ValueError("Anlernmodus abgelaufen; bitte neu starten")
    else:
        raise ValueError("Unbekannter Anlernbefehl")
    lease["expires"] = time.time() + 15 if action != "stop" else 0
    if action == "stop":
        lease["stopped_at"] = time.time()
    atomic_json(home() / "learning.json", lease)
    return lease
