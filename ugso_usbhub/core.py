from collections import deque
import json
import logging
import queue
import signal
import time
from . import __version__
from .hardware import Hardware
from .mqtt import Brokers
from .storage import atomic_json, home, load_config, validate, status_path

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
        key = (device, control)
        if gesture == "repeat":
            if now - self.repeats.get(key, 0) < 0.15:
                return
            self.repeats[key] = now
        if gesture == "press":
            self.pressed[key] = (now, False)
        elif gesture == "release":
            self.pressed.pop(key, None)
            self.repeats.pop(key, None)
        sent = self.brokers.send(device, control, gesture, value)
        self.events.appendleft({"time": time.time(), "device": device, "control": control,
                                "gesture": gesture, "value": value, "delivered": sent})

    def status(self):
        return {"version": __version__, "pid": __import__("os").getpid(), "updated": time.time(),
                "started": self.started, "devices": self.hardware.inventory,
                "brokers": dict(self.brokers.states), "errors": dict(self.hardware.errors), "events": list(self.events)}

    def run(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: setattr(self, "running", False))
        scan_at = status_at = reload_at = 0
        try:
            while self.running:
                now = time.monotonic()
                if now >= reload_at:
                    reload_at = now + 1
                    try:
                        updated = validate(load_config())
                        if updated != self.config:
                            old = self.config
                            # Validate native TLS setup before closing existing clients.
                            if updated["brokers"] != old["brokers"] or updated["bindings"] != old["bindings"] or updated["devices"] != old["devices"] or updated["default_targets"] != old["default_targets"]:
                                replacement = Brokers(updated, self.receive, start=False)
                                self.brokers.cleanup_removed(updated)
                                self.brokers.close()
                                self.brokers = replacement
                                self.brokers.start()
                            self.config = updated
                            self.pressed.clear()
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
                if now >= status_at:
                    status_at = now + 2
                    atomic_json(status_path(), self.status())
        finally:
            self.hardware.close()
            self.brokers.close()
            snapshot = self.status()
            snapshot["stopped"] = True
            atomic_json(status_path(), snapshot)
