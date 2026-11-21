"""Learned key rows, kept separate from existing individual bindings."""
import re
import hashlib
import unicodedata
from .storage import canonical_control

VOLUME_KEYS = {"KEY_VOLUMEUP", "KEY_VOLUMEDOWN"}
EXTRA_MODES = ("state", "button", "button_plus", "click", "double_click", "hold")


def button_enabled(key):
    return key.get("enabled", True) and any(key.get(mode, False) for mode in EXTRA_MODES if mode != "state")


def topic_slug(name):
    name = str(name).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:64].rstrip("-") or "usb-device"


def device_topic_names(config):
    # Freeze a device's namespace once its first named key has been saved.
    saved = {key["device"]: key["device_topic"] for key in config.get("keys", []) if key.get("device_topic")}
    names, used = dict(saved), set(saved.values())
    for ident, device in config.get("devices", {}).items():
        if ident in names:
            continue
        stem = topic_slug(device.get("name") or "USB-Gerät")
        candidate, suffix = stem, 2
        while candidate in used:
            candidate = f"{stem}-{suffix}"
            suffix += 1
        names[ident] = candidate
        used.add(candidate)
    return names


def validate_keys(config):
    keys = config.get("keys", [])
    if not isinstance(keys, list) or len(keys) > 1000:
        raise ValueError("Maximal 1000 Tasten sind vorgesehen")
    seen, identities = set(), {b["id"] for b in config.get("bindings", [])}
    for key in keys:
        ident = key.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", ident):
            raise ValueError("Ungültige Tasten-ID")
        if ident in identities:
            raise ValueError("Doppelte Tasten-ID")
        identities.add(ident)
        key["control"] = canonical_control(key.get("control", ""))
        pair = (key.get("device"), key["control"])
        if not pair[0] or not pair[1] or pair in seen:
            raise ValueError("Gerät und Taste müssen eindeutig sein")
        seen.add(pair)
        if key.get("targets") is not None and (not isinstance(key["targets"], list) or
                any(t not in {"broker1", "broker2", "broker3"} for t in key["targets"])):
            raise ValueError("Unbekanntes MQTT-Ziel")
        if key.get("topic_version") == 2:
            if not re.fullmatch(r"[a-z0-9-]{1,80}", key.get("device_topic", "")):
                raise ValueError("Lesbarer Gerätename für MQTT fehlt")
        elif key.get("topic_version") is not None:
            raise ValueError("Unbekannte Topic-Version")
        if key.get("switch_mode", "toggle") not in ("toggle", "momentary"):
            raise ValueError("Ungültiger Switch-Modus")
        for mode in ("press", "release", "switch", "press_plus", "release_plus", *EXTRA_MODES):
            topic = key.get(mode + "_topic", "")
            if not isinstance(topic, str) or any(x in topic for x in ("#", "+", "\x00")):
                raise ValueError("Sende-Topic darf keine Wildcards enthalten")
        for name in ("enabled", "press", "release", "switch", "press_plus", "release_plus", "repeat", *EXTRA_MODES):
            if name in key and not isinstance(key[name], bool):
                raise ValueError("Tastenoptionen müssen ein/aus sein")
        for name, default, low, high in (("repeat_delay", 500, 200, 5000), ("repeat_interval", 150, 100, 2000),
                                       ("double_ms", 300, 150, 1000), ("hold_ms", 700, 400, 5000)):
            value = key.get(name, default)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("Ungültige Zeit: Wiederholung 200–5000/100–2000 ms, Doppelklick 150–1000 ms, Halten 400–5000 ms")
        if key.get("repeat") and key["control"] not in VOLUME_KEYS:
            raise ValueError("Wiederholung beim Halten ist für Lauter/Leiser vorgesehen")
    return config


def ensure_deck_keys(config, devices):
    """Fill missing key rows for enabled decks; never replace saved mappings."""
    names = device_topic_names(config)
    rows = config.setdefault("keys", [])
    known = {(k["device"], k["control"]) for k in rows}
    added = 0
    for device in devices:
        ident = device.get("id")
        if device.get("kind") != "streamdeck" or not config.get("devices", {}).get(ident, {}).get("enabled"):
            continue
        count = device.get("deck", {}).get("keys", 0)
        if type(count) is not int or not 1 <= count <= 128:
            continue
        info=device.get("deck", {})
        layout=info.get("layout", [])
        if len(layout)==2 and all(type(n) is int and 1<=n<=16 for n in layout) and layout[0]*layout[1]==count:
            config["devices"][ident]["deck_info"]={"model":str(info.get("model","Stream Deck"))[:100],"keys":count,"layout":list(layout),"visual":bool(info.get("visual",True)),"size":info.get("size",[72,72])}
            config["devices"][ident]["deck_connection"]=device.get("connection","usb")
        for index in range(count):
            control = f"key:{index}"
            if (ident, control) in known:
                continue
            token = hashlib.sha256(f"{ident}/{control}".encode()).hexdigest()[:24]
            row = {"id":"auto-deck-"+token, "device":ident, "control":control,
                   "name":f"Taste {index+1}", "enabled":True, "topic_version":2,
                   "device_topic":names[ident], "targets":None, "switch_mode":"toggle",
                   "repeat":False, "double_ms":300, "hold_ms":700}
            for mode in ("press", "release", "switch", "press_plus", "release_plus", *EXTRA_MODES):
                row[mode] = True
                row[mode+"_topic"] = names[ident]+"-"+topic_slug(control)+"/"+mode.replace("_", "-")
            rows.append(row)
            known.add((ident, control))
            added += 1
    return added


def key_bindings(config):
    result = []
    for key in config.get("keys", []):
        if not key.get("enabled", True):
            continue
        named = key.get("topic_version") == 2
        modes = ("press", "press_plus", "release", "release_plus", "switch", *EXTRA_MODES) if named else ("press", "release", "switch")
        for mode in modes:
            if not key.get(mode, mode not in EXTRA_MODES):
                continue
            toggle = mode == "switch" and key.get("switch_mode", "toggle") == "toggle"
            if toggle:
                gestures = ("toggle_on", "toggle_off")
            elif mode in ("switch", "state"):
                gestures = ("press", "release")
            elif mode in ("button", "button_plus"):
                gestures = ("button_click", "button_double_click", "button_hold")
            elif mode in ("click", "double_click", "hold"):
                gestures = ("button_" + mode,)
            else:
                gestures = (mode.removesuffix("_plus"),)
            for gesture in gestures:
                suffix = mode.replace("_", "-")
                readable_topic = key.get("device_topic", "") + "-" + topic_slug(key["control"]) + "/" + suffix
                result.append({"id": key["id"] + "-" + mode + "-" + gesture,
                               "device": key["device"], "control": key["control"],
                               "gesture": gesture, "targets": key.get("targets"),
                               "topic": key.get(mode + "_topic", "") or (readable_topic if named else ""),
                               "key_topic": key["device"] + "/" + re.sub(r"[^a-z0-9_-]", "-", key["control"].lower()) + "/" + mode,
                               "payload": ("ON" if gesture in ("press", "toggle_on") else "OFF") if mode in ("switch", "state") else gesture.removeprefix("button_"),
                               "reset": mode.endswith("_plus") if named else mode != "switch" and key.get(mode + "_plus", False),
                               "key_mode": mode, "key_id": key["id"],
                               "toggle": toggle,
                               "icon": key.get("icon", ""), "text": key.get("name", "")})
    return result


def all_bindings(config):
    return config.get("bindings", []) + key_bindings(config)
