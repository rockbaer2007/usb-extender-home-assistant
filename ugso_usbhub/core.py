from collections import deque
import json
import logging
import queue
import signal
import time
from . import __version__
from .hardware import Hardware
from .mqtt import Brokers
from .storage import atomic_json, home, load_config, validate, status_path, canonical_control, read_json
from .learning import current as learning_lease
from .keymap import VOLUME_KEYS, button_enabled
from .gestures import Buttons

LOG = logging.getLogger(__name__)


class Core:
    def __init__(self):
        self.config = validate(load_config())
        self.events = deque(maxlen=100)
        self.queue = queue.Queue(maxsize=512)
        self.hardware = Hardware(self.enqueue)
        self.brokers = Brokers(self.config, self.receive)
        self.running = True
        self.pressed = {}
        self.repeats = {}
        self.repeat_due = {}
        self.learning = {}
        self.learning_releases = set()
        self.sequence = 0
        self.buttons = Buttons()
        stored = read_json(home() / "switches.json", {})
        self.toggle_states = stored if isinstance(stored, dict) else {}
        self.started = time.time()

    def enqueue(self, device, control, gesture, value=1):
        try:
            self.queue.put_nowait((device, control, gesture, value))
        except queue.Full:
            LOG.warning("Eingabewarteschlange voll; Ereignis verworfen")

    def receive(self, broker_id, topic, payload):
        try:
            self.queue.put_nowait(("_mqtt", broker_id, topic, payload))
        except queue.Full:
            LOG.warning("Anzeigeauftrag verworfen: Warteschlange voll")

    def display_message(self, broker_id, topic, payload):
        broker = next(b for b in self.config["brokers"] if b["id"] == broker_id)
        prefix = broker["prefix"] + "/display/"
        if topic.startswith(prefix) and topic.endswith("/set"):
            ident = topic[len(prefix):-4]
            if self.config["devices"].get(ident, {}).get("receive_broker") != broker_id:
                return
            command = json.loads(payload)
            self.hardware.display(ident, int(command.get("key", 0)), command.get("icon", ""), command.get("text", ""), command.get("brightness"))
        else:
            for b in self.config["bindings"]:
                if b.get("state_topic") != topic or self.config["devices"].get(b["device"], {}).get("receive_broker") != broker_id:
                    continue
                value = payload
                if b.get("state_path"):
                    value = json.loads(payload)
                    for part in b["state_path"].split("."):
                        value = value[part]
                icon = b.get("on_icon") if str(value) == str(b.get("on_value", "ON")) else b.get("icon")
                if b["control"].startswith("key:"):
                    self.hardware.display(b["device"], int(b["control"].split(":")[1]), icon or "", str(value))

    def event(self, device, control, gesture, value):
        if not self.config["devices"].get(device, {}).get("enabled"):
            return
        now = time.monotonic()
        control = canonical_control(control)
        key = (device, control)
        was_down = key in self.pressed
        row = next((k for k in self.config.get("keys", []) if (k["device"], k["control"]) == key and k.get("enabled", True)), {})
        learning = self.learning if self.learning.get("expires", 0) > time.time() else {}
        suppressed = learning.get("device") == device or key in self.learning_releases
        if suppressed:
            self.buttons.cancel(key=key)
            self.pressed.pop(key, None)
            self.repeat_due.pop(key, None)
            if gesture == "press":
                self.learning_releases.add(key)
            elif gesture == "release":
                self.learning_releases.discard(key)
            report = {"delivered": 0, "matched": 0, "reason": "learning", "transmissions": []}
        else:
            report = None
        if gesture == "repeat":
            if now - self.repeats.get(key, 0) < 0.15:
                return
            self.repeats[key] = now
        if gesture == "press" and not suppressed and not was_down:
            self.pressed[key] = (now, False)
            if row.get("repeat") and control in VOLUME_KEYS:
                self.repeat_due[key] = now + row.get("repeat_delay", 500) / 1000
        elif gesture == "release":
            self.pressed.pop(key, None)
            self.repeats.pop(key, None)
            self.repeat_due.pop(key, None)
        report = report or self.brokers.send_report(device, control, gesture, value)
        if not suppressed and gesture == "press" and not was_down and row.get("switch", True) and row and row.get("switch_mode", "toggle") == "toggle":
            ident = row["id"]
            state = not (self.toggle_states.get(ident) is True)
            updated = {k: v for k, v in self.toggle_states.items() if k in {r["id"] for r in self.config.get("keys", [])}}
            updated[ident] = state
            atomic_json(home() / "switches.json", updated)
            self.toggle_states = updated
            switched = self.brokers.send_report(device, control, "toggle_on" if state else "toggle_off", int(state))
            report = {"delivered": report["delivered"] + switched["delivered"],
                      "matched": report["matched"] + switched["matched"],
                      "reason": "sent" if report["delivered"] + switched["delivered"] else switched["reason"],
                      "transmissions": report["transmissions"] + switched["transmissions"]}
        self.record(device, control, gesture, value, report, learning.get("id") if suppressed else None)
        if not suppressed and button_enabled(row):
            for button_key, action in self.buttons.feed(key, gesture, now, row):
                self.button_event(button_key, action)

    def record(self, device, control, gesture, value, report, learning_id=None):
        self.sequence += 1
        self.events.appendleft({"time": time.time(), "device": device, "control": control,
                                "gesture": gesture, "value": value, "delivered": report["delivered"],
                                "delivery": report, "sequence": self.sequence,
                                "learning_id": learning_id})

    def button_event(self, key, action):
        report = self.brokers.send_report(*key, action, 1)
        self.record(*key, action.removeprefix("button_"), 1, report)

    def tick(self, now=None):
        now = time.monotonic() if now is None else now
        self.brokers.flush_resets(now)
        for key, action in self.buttons.tick(now):
            self.button_event(key, action)
        for key, due in list(self.repeat_due.items()):
            if key not in self.pressed:
                self.repeat_due.pop(key, None)
                continue
            if now - self.pressed[key][0] >= 30:
                self.release_key(key)
                continue
            if now >= due:
                row = next((k for k in self.config.get("keys", []) if (k["device"], k["control"]) == key), {})
                self.brokers.send_report(*key, "press", 1, repeat_key=True)
                self.repeat_due[key] = now + row.get("repeat_interval", 150) / 1000

    def release_key(self, key):
        # Clear momentary state, not the latched toggle. Do not invent physical
        # release actions for existing individual bindings.
        self.brokers.send_report(*key, "release", 0, switch_only=True)
        self.buttons.cancel(key=key)
        self.pressed.pop(key, None)
        self.repeat_due.pop(key, None)
        self.repeats.pop(key, None)

    def release_all(self, device=None):
        self.buttons.cancel(device=device)
        for key in list(self.pressed):
            if device is None or key[0] == device:
                self.release_key(key)

    def status(self):
        return {"version": __version__, "pid": __import__("os").getpid(), "updated": time.time(),
                "started": self.started, "devices": self.hardware.inventory,
                "brokers": dict(self.brokers.states),
                "errors": {**self.hardware.errors, **{"Discovery " + key: value for key, value in self.brokers.discovery_errors.items()}},
                "events": list(self.events)}

    def run(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: setattr(self, "running", False))
        scan_at = status_at = reload_at = 0
        try:
            while self.running:
                now = time.monotonic()
                lease = learning_lease()
                if lease.get("id") != self.learning.get("id") and lease:
                    self.release_all(lease["device"])
                self.learning = lease
                if now >= reload_at:
                    reload_at = now + 1
                    try:
                        updated = validate(load_config())
                        if updated != self.config:
                            old = self.config
                            # Validate native TLS setup before closing existing clients.
                            if updated["brokers"] != old["brokers"] or updated["bindings"] != old["bindings"] or updated.get("keys", []) != old.get("keys", []) or updated["devices"] != old["devices"] or updated["default_targets"] != old["default_targets"]:
                                replacement = Brokers(updated, self.receive, start=False)
                                self.release_all()
                                self.brokers.cleanup_removed(updated)
                                self.brokers.close()
                                self.brokers = replacement
                                self.brokers.start()
                            self.config = updated
                            self.pressed.clear()
                            self.repeat_due.clear()
                            self.hardware.config = updated
                            self.hardware.refresh_decks()
                            scan_at = 0
                    except Exception:
                        LOG.exception("Konfiguration konnte nicht übernommen werden")
                if now >= scan_at:
                    scan_at = now + 5
                    try:
                        self.hardware.scan(self.config)
                        present = {d["id"] for d in self.hardware.inventory}
                        for device in {key[0] for key in [*self.pressed, *self.buttons.keys] if key[0] not in present}:
                            self.release_all(device)
                        self.pressed = {key: value for key, value in self.pressed.items() if key[0] in present}
                    except Exception:
                        LOG.exception("USB-Erkennung fehlgeschlagen")
                self.hardware.poll()
                for _ in range(128):
                    try:
                        item = self.queue.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        if item[0] == "_mqtt":
                            self.display_message(*item[1:])
                        else:
                            self.event(*item)
                    except Exception:
                        LOG.exception("Eingabe oder Anzeigeauftrag fehlgeschlagen")
                for key, (since, fired) in list(self.pressed.items()):
                    if not fired and now - since >= 0.7:
                        self.pressed[key] = (since, True)
                        self.event(*key, "hold", 1)
                self.tick(now)
                if now >= status_at:
                    status_at = now + 2
                    atomic_json(status_path(), self.status())
        finally:
            self.release_all()
            self.hardware.close()
            self.brokers.close()
            snapshot = self.status()
            snapshot["stopped"] = True
            atomic_json(status_path(), snapshot)
