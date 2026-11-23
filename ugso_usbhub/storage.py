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


def canonical_control(value):
    """evdev can return alias tuples/lists; store a single actual key name."""
    if isinstance(value, str):
        import re
        value = value.strip()
        if re.fullmatch(r"key:[a-zA-Z_][a-zA-Z_0-9]*", value, re.I):
            return "KEY_" + value.split(":", 1)[1].upper()
        if value.upper().startswith(("KEY_", "BTN_", "REL_")):
            return value.upper()
        return value
    if isinstance(value, (tuple, list)) and value and all(isinstance(x, str) for x in value):
        return next((x for x in value if x not in {"KEY_MIN_INTERESTING", "KEY_MAX", "KEY_CNT", "BTN_MISC", "BTN_MOUSE", "BTN_GAMEPAD"}), value[0])
    raise ValueError("Taste muss ein Name sein")


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
                         "discovery": False} for i in range(1, 4)],
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
    from .mobile import validate_options
    validate_options(c)
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
        if device.get('device_view','normal') not in ('normal','system','hidden'):
            raise ValueError('Geräteansicht: normal, system oder hidden')
        for flag in ('scanner_enabled','scanner_ha_urls'):
            if type(device.get(flag,flag=='scanner_ha_urls')) is not bool:raise ValueError('Scanner-Option muss ein/aus sein')
        if device.get('scanner_layout','de') not in ('de','us'):raise ValueError('Scanner-Tastaturlayout: de oder us')
        if device.get('scanner_terminator','enter') not in ('enter','tab','timeout'):raise ValueError('Scanner-Abschluss: Enter, Tab oder Scanpause')
        timeout=device.get('scanner_timeout_ms',500)
        if type(timeout) is not int or not 100<=timeout<=3000:raise ValueError('Scanner-Pause: 100–3000 ms')
        topic=device.get('scanner_topic','')
        if not isinstance(topic,str) or len(topic.encode('utf-8'))>512 or any(c in topic for c in ('#','+','\x00')):raise ValueError('Ungültiges Scanner-Topic')
        from .gamepad import AXES,PROFILE
        if type(device.get('gamepad_axes_enabled',False)) is not bool:raise ValueError('Gamepad-Achsen müssen ein/aus sein')
        if device.get('gamepad_axes_enabled') and device.get('gamepad_profile')!=PROFILE:raise ValueError('Gamepad: geprüftes DragonRise-Profil erforderlich')
        rate=device.get('gamepad_rate',10)
        if type(rate) is not int or not 1<=rate<=30:raise ValueError('Gamepad-Senderate: 1–30/s')
        axes=device.get('gamepad_axes',{})
        if not isinstance(axes,dict) or any(name not in AXES for name in axes):raise ValueError('Unbekannte Gamepad-Achse; ABS_Z ist ausgeschlossen')
        for value in axes.values():
            if not isinstance(value,dict) or type(value.get('enabled',True)) is not bool:raise ValueError('Gamepad-Achse muss ein/aus sein')
            topic=value.get('topic','')
            if not isinstance(topic,str) or len(topic.encode('utf-8'))>512 or any(c in topic for c in ('#','+','\x00')):raise ValueError('Ungültiges Gamepad-Topic')
        if device.get('touchpad_mode','directions') not in ('directions','faders'):
            raise ValueError('Touchpad-Modus: directions oder faders')
        faders=device.get('touchpad_faders',{})
        if not isinstance(faders,dict) or any(key not in ('1','2','3','4','5') for key in faders):
            raise ValueError('Touchpad: fünf Reglerplätze 1–5')
        for value in faders.values():
            if not isinstance(value,dict) or type(value.get('enabled',True)) is not bool:
                raise ValueError('Regler müssen ein/aus sein')
            topic=value.get('topic','')
            if not isinstance(topic,str) or len(topic.encode('utf-8'))>512 or any(c in topic for c in ('#','+','\x00')):
                raise ValueError('Ungültiges Regler-Topic')
        from .touchpad import SLIDE_DIRECTIONS
        values=device.get('touchpad_slide_values',{})
        if not isinstance(values,dict) or any(key not in SLIDE_DIRECTIONS for key in values):
            raise ValueError('Unbekannte Slide-Richtung')
        for value in values.values():
            if not isinstance(value,dict) or type(value.get('enabled',False)) is not bool:
                raise ValueError('Slide-Werte müssen ein/aus sein')
            topic=value.get('topic','')
            if not isinstance(topic,str) or len(topic.encode('utf-8'))>512 or any(c in topic for c in ('#','+','\x00')):
                raise ValueError('Ungültiges Slide-Wert-Topic')
        if 'touchpad_gestures' in device and type(device['touchpad_gestures']) is not bool:
            raise ValueError('Touchpad-Gesten müssen ein/aus sein')
        if 'touchpad_xy' in device and type(device['touchpad_xy']) is not bool:
            raise ValueError('Touchpad-X/Y muss ein/aus sein')
        for name,default,low,high in [('touchpad_sensitivity',5,1,10),('touchpad_rate',10,1,30)]:
            value=device.get(name,default)
            if type(value) is not int or not low<=value<=high:
                raise ValueError('Touchpad: Empfindlichkeit 1–10, Senderate 1–30 pro Sekunde')
        for name in ('touchpad_x_topic','touchpad_y_topic'):
            topic=device.get(name,'')
            if not isinstance(topic,str) or len(topic.encode('utf-8'))>512 or any(c in topic for c in ('#','+','\x00')):
                raise ValueError('Ungültiges Touchpad-X/Y-Topic')
        hardware=device.get('hardware',{})
        if not isinstance(hardware,dict) or any(not isinstance(v,str) or len(v)>512 for v in hardware.values()):
            raise ValueError('Ungültige Hardwarezuordnung')
        targets(device.get("targets", []))
        if device.get("receive_broker", "") not in ["", *ids]:
            raise ValueError("Ungültiger Empfangsbroker")
        if not 0 <= int(device.get("brightness", 30)) <= 100:
            raise ValueError("Helligkeit muss zwischen 0 und 100 liegen")
        from .deck import validate_artwork
        layout=device.get("mobile_layout")
        if layout is not None and (not isinstance(layout,dict) or any(type(layout.get(axis)) is not int or not 1<=layout[axis]<=8 for axis in ("rows","columns"))):
            raise ValueError("Mobile-Raster: 1–8 Spalten und Zeilen")
        pages = device.get("deck_page_count", 1)
        if type(pages) is not int or not 1 <= pages <= 8:
            raise ValueError("Deck-Seiten: 1 bis 8")
        order = device.get("deck_page_order", list(range(pages)))
        if not isinstance(order, list) or len(order) != pages or any(type(n) is not int or not 0 <= n < 8 for n in order) or len(set(order)) != pages or order[0] != 0:
            raise ValueError("Ungültige Seitenreihenfolge; Seite 1 muss erhalten bleiben")
        deck_keys = device.get("deck_keys", {})
        if not isinstance(deck_keys, dict) or len(deck_keys) > 1024:
            raise ValueError("Maximal 8 Seiten mit je 128 gestalteten Tasten")
        for key, style in deck_keys.items():
            if not isinstance(key, str) or not key.isascii() or not key.isdecimal() or str(int(key)) != key or not 0 <= int(key) < 1024:
                raise ValueError("Ungültige Stream-Deck-Taste")
            validate_artwork(style)
    seen = set()
    for b in c.get("bindings", []):
        if not b.get("id") or b["id"] in seen or not b.get("device") or not b.get("control"):
            raise ValueError("Jede Belegung benötigt eindeutige ID, Gerät und Taste")
        seen.add(b["id"])
        b["control"] = canonical_control(b["control"])
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
    from .keymap import validate_keys, device_topic_names
    validate_keys(c)
    names=device_topic_names(c)
    for ident,device in c.get('devices',{}).items():
        value_topics=[]
        if device.get('scanner_enabled') and not device.get('scanner_topic'):
            device['scanner_topic']=names[ident]+'-scanner/tag_scanned'
        if device.get('gamepad_axes_enabled'):
            from .gamepad import AXES
            axes=device.setdefault('gamepad_axes',{})
            for name in AXES:
                value=axes.setdefault(name,{'enabled':True,'topic':''})
                if value.get('enabled',True):
                    if not value.get('topic'):value['topic']=names[ident]+'-gamepad/'+name.replace('_','-')+'/value'
                    value_topics.append(value['topic'])
        fader_mode=device.get('touchpad_mode','directions')=='faders'
        if fader_mode:
            faders=device.setdefault('touchpad_faders',{})
            for lane in ('1','2','3','4','5'):
                value=faders.setdefault(lane,{'enabled':True,'topic':''})
                if value.get('enabled',True):
                    if not value.get('topic'):value['topic']=names[ident]+'-touchpad/fader-'+lane+'/value'
                    value_topics.append(value['topic'])
        for direction,value in device.get('touchpad_slide_values',{}).items():
            if value.get('enabled'):
                if not value.get('topic'):value['topic']=names[ident]+'-touchpad/slide-'+direction.lower().replace('_','-')+'/value'
                if not fader_mode:value_topics.append(value['topic'])
        if device.get('touchpad_xy'):
            for axis in ('x','y'):
                if not device.get('touchpad_'+axis+'_topic'):
                    device['touchpad_'+axis+'_topic']=names[ident]+'-touchpad/'+axis
            if device['touchpad_x_topic']==device['touchpad_y_topic']:
                raise ValueError('Touchpad-X und -Y benötigen unterschiedliche Topics')
            value_topics.extend((device['touchpad_x_topic'],device['touchpad_y_topic']))
        if len(value_topics)!=len(set(value_topics)):
            raise ValueError('Zahlenwerte benötigen unterschiedliche Topics')
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
    for binding in result.get("bindings", []):
        binding["control"] = canonical_control(binding["control"])
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
