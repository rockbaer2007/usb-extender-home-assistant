import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
import uuid


def home():
    path = Path(os.environ.get("UGSO_USB_HOME", "/var/lib/ugso-usbhub"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def status_path():
    return Path(os.environ.get("UGSO_USB_STATUS", str(home() / "status.json")))


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(name, 0o600)
        if hasattr(os, "chown") and os.geteuid() == 0 and path.exists():
            previous = path.stat()
            os.chown(name, previous.st_uid, previous.st_gid)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 310000).hex()
    return salt + ":" + digest


def check_password(password, stored):
    try:
        return secrets.compare_digest(password_hash(password, stored.split(":")[0]), stored)
    except (ValueError, AttributeError):
        return False


def defaults():
    return {"schema": 1, "hub_id": uuid.uuid4().hex[:12], "password_hash": "",
            "web": {"host": "0.0.0.0", "port": 8098},
            "brokers": [{"id": f"broker{i}", "name": f"MQTT {i}", "enabled": False,
                         "host": "", "port": 1883, "username": "", "password": "",
                         "tls": False, "ca_file": "", "prefix": f"ugso/usbhub/{i}",
                         "discovery": True} for i in range(1, 4)],
            "default_targets": ["broker1"], "devices": {}, "bindings": []}


def load_config():
    value = read_json(home() / "config.json")
    if value is None:
        value = defaults()
        atomic_json(home() / "config.json", value)
    return value


def validate(c):
    if c.get("schema") != 1:
        raise ValueError("Unbekannte Konfigurationsversion")
    brokers = c.get("brokers", [])
    ids = [b.get("id") for b in brokers]
    if len(brokers) != 3 or set(ids) != {"broker1", "broker2", "broker3"}:
        raise ValueError("Genau drei Brokerplätze sind vorgesehen")
    for b in brokers:
        if not isinstance(b.get("port"), int) or not 1 <= b["port"] <= 65535:
            raise ValueError("Ungültiger MQTT-Port")
        if b.get("enabled") and not b.get("host", "").strip():
            raise ValueError("MQTT-Host fehlt")
        if not b.get("prefix") or any(x in b["prefix"] for x in ("#", "+", "\x00")):
            raise ValueError("Topic-Präfix darf keine Wildcards enthalten")
    def targets(values):
        if not isinstance(values, list) or any(v not in ids for v in values):
            raise ValueError("Unbekanntes MQTT-Ziel")
    targets(c.get("default_targets", []))
    for device in c.get("devices", {}).values():
        targets(device.get("targets", []))
        if device.get("receive_broker", "") not in ["", *ids]:
            raise ValueError("Ungültiger Empfangsbroker")
        if not 0 <= int(device.get("brightness", 30)) <= 100:
            raise ValueError("Helligkeit muss zwischen 0 und 100 liegen")
    seen = set()
    for b in c.get("bindings", []):
        if not b.get("id") or b["id"] in seen or not b.get("device") or not b.get("control"):
            raise ValueError("Jede Belegung benötigt eindeutige ID, Gerät und Taste")
        seen.add(b["id"])
        import re
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", b["id"]):
            raise ValueError("Belegungs-ID enthält ungültige Zeichen")
        if not isinstance(b.get("payload", ""), str):
            raise ValueError("Payload muss Text sein")
        if b.get("targets") is not None:
            targets(b["targets"])
        if b.get("gesture") not in ("press", "release", "hold", "repeat", "rotate_left", "rotate_right", "touch"):
            raise ValueError("Unbekannte Eingabeart")
        if any(x in b.get("topic", "") for x in ("#", "+", "\x00")):
            raise ValueError("Sende-Topic darf keine Wildcards enthalten")
    return c


def save_config(c):
    validate(c)
    old = load_config()
    if c != old:
        from datetime import datetime, timezone
        folder = home() / "backups"
        atomic_json(folder / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"), old)
        for path in sorted(folder.glob("*.json"))[:-10]:
            path.unlink()
        atomic_json(home() / "config.json", c)


def public_config(c):
    result = copy.deepcopy(c)
    result.pop("password_hash", None)
    for b in result["brokers"]:
        b["password_set"] = bool(b.get("password"))
        b["password"] = ""
    return result


def merge_public(incoming, current):
    result = copy.deepcopy(incoming)
    result["hub_id"] = current["hub_id"]
    result["password_hash"] = current["password_hash"]
    old = {b["id"]: b for b in current["brokers"]}
    for b in result["brokers"]:
        if not b.get("password") and not b.pop("clear_password", False):
            b["password"] = old[b["id"]]["password"]
        b.pop("password_set", None)
    return validate(result)
