"""Learned key rows, kept separate from existing individual bindings."""
import re
from .storage import canonical_control

VOLUME_KEYS = {"KEY_VOLUMEUP", "KEY_VOLUMEDOWN"}


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
        for mode in ("press", "release", "switch"):
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
        for mode in ("press", "release", "switch"):
            if not key.get(mode, True):
                continue
            gestures = ("press", "release") if mode == "switch" else (mode,)
            for gesture in gestures:
                result.append({"id": key["id"] + "-" + mode + "-" + gesture,
                               "device": key["device"], "control": key["control"],
                               "gesture": gesture, "targets": key.get("targets"),
                               "topic": key.get(mode + "_topic", ""),
                               "key_topic": key["device"] + "/" + re.sub(r"[^a-z0-9_-]", "-", key["control"].lower()) + "/" + mode,
                               "payload": ("ON" if gesture == "press" else "OFF") if mode == "switch" else gesture,
                               "reset": mode != "switch" and key.get(mode + "_plus", False),
                               "key_mode": mode, "key_id": key["id"],
                               "icon": key.get("icon", ""), "text": key.get("name", "")})
    return result


def all_bindings(config):
    return config.get("bindings", []) + key_bindings(config)
