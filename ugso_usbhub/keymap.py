"""Learned key rows, kept separate from existing individual bindings."""
import re
import unicodedata
from .storage import canonical_control

VOLUME_KEYS = {"KEY_VOLUMEUP", "KEY_VOLUMEDOWN"}


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
        for mode in ("press", "release", "switch", "press_plus", "release_plus"):
            topic = key.get(mode + "_topic", "")
            if not isinstance(topic, str) or any(x in topic for x in ("#", "+", "\x00")):
                raise ValueError("Sende-Topic darf keine Wildcards enthalten")
        for name in ("enabled", "press", "release", "switch", "press_plus", "release_plus", "repeat"):
            if name in key and not isinstance(key[name], bool):
                raise ValueError("Tastenoptionen müssen ein/aus sein")
        for name, default, low, high in (("repeat_delay", 500, 200, 5000), ("repeat_interval", 150, 100, 2000)):
            value = key.get(name, default)
            if type(value) is not int or not low <= value <= high:
                raise ValueError("Wiederholung: Start 200–5000 ms, Abstand 100–2000 ms")
        if key.get("repeat") and key["control"] not in VOLUME_KEYS:
            raise ValueError("Wiederholung beim Halten ist für Lauter/Leiser vorgesehen")
    return config


def key_bindings(config):
    result = []
    for key in config.get("keys", []):
        if not key.get("enabled", True):
            continue
        named = key.get("topic_version") == 2
        modes = ("press", "press_plus", "release", "release_plus", "switch") if named else ("press", "release", "switch")
        for mode in modes:
            if not key.get(mode, True):
                continue
            gestures = ("press", "release") if mode == "switch" else (mode.removesuffix("_plus"),)
            for gesture in gestures:
                suffix = mode.replace("_", "-")
                readable_topic = key.get("device_topic", "") + "-" + topic_slug(key["control"]) + "/" + suffix
                result.append({"id": key["id"] + "-" + mode + "-" + gesture,
                               "device": key["device"], "control": key["control"],
                               "gesture": gesture, "targets": key.get("targets"),
                               "topic": key.get(mode + "_topic", "") or (readable_topic if named else ""),
                               "key_topic": key["device"] + "/" + re.sub(r"[^a-z0-9_-]", "-", key["control"].lower()) + "/" + mode,
                               "payload": ("ON" if gesture == "press" else "OFF") if mode == "switch" else gesture,
                               "reset": mode.endswith("_plus") if named else mode != "switch" and key.get(mode + "_plus", False),
                               "key_mode": mode, "key_id": key["id"],
                               "icon": key.get("icon", ""), "text": key.get("name", "")})
    return result


def all_bindings(config):
    return config.get("bindings", []) + key_bindings(config)
