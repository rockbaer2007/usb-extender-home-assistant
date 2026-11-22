from collections import deque
import json
import logging
import queue
import re
import signal
import time
from . import __version__
from .hardware import Hardware
from .mqtt import Brokers
from .storage import atomic_json, home, load_config, validate, status_path, canonical_control, read_json
from .learning import current as learning_lease
from .keymap import VOLUME_KEYS, STEP_KEYS, button_enabled
from .gestures import Buttons

LOG = logging.getLogger(__name__)


class Core:
    def __init__(self):
        self.config = validate(load_config())
        self.events = deque(maxlen=100)
        self.queue = queue.Queue(maxsize=512)
        self.hardware = Hardware(self.enqueue)
        self.hardware.config = self.config
        from .mobile import MobileServer
        self.mobile = MobileServer(self.enqueue)
        self.mobile.current_page = self.hardware.active_page
        self.hardware.mobile = self.mobile
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
        self.deck_routes = {}
        self.navigation_down = set()
        self.deck_ignored_releases = set()
        self.step_counts = {}
        self.step_cycles = {}

    def step_pass(self, key, row):
        every = row.get("step_every", 1) if key[1] in STEP_KEYS else 1
        old_every, count = self.step_counts.get(key, (every, 0))
        count = (count if old_every == every else 0) + 1
        self.step_counts[key] = (every, count % every)
        return count % every == 0

    def change_page(self, device, target):
        from .deck import page_count
        current = self.hardware.active_page(device)
        target = max(0, min(target, page_count(self.config, device)-1))
        if target == current:
            return False
        self.release_all(device)
        return self.hardware.set_page(device, target)

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
            from .deck import logical_key, page_count, page_slot
            target_page = command.get("page", 1)
            if type(target_page) is not int or not 1 <= target_page <= page_count(self.config, ident):
                raise ValueError("Ungültige Displayseite")
            key = command.get("key", 0)
            if type(key) is not int or not 0 <= key < 128:
                raise ValueError("Ungültige Displaytaste")
            self.hardware.display_logical(ident, logical_key(key, page_slot(self.config,ident,target_page-1)), command.get("icon", ""), command.get("text", ""), command.get("brightness"))
        else:
            for b in self.config["bindings"]:
                from .deck import binding_allowed
                if not binding_allowed(self.config,b['device'],b['control']):
                    continue
                if b.get("state_topic") != topic or self.config["devices"].get(b["device"], {}).get("receive_broker") != broker_id:
                    continue
                value = payload
                if b.get("state_path"):
                    value = json.loads(payload)
                    for part in b["state_path"].split("."):
                        value = value[part]
                if b["control"].startswith("key:"):
                    from .deck import artwork, page_slots
                    key = int(b["control"].split(":")[1])
                    slots=page_slots(self.config,b["device"])
                    if key // 128 not in slots:
                        continue
                    style = artwork(self.config, b["device"], key % 128, slots.index(key // 128))
                    base_icon = style.get("icon", b.get("icon", ""))
                    icon = (b.get("on_icon") or base_icon) if str(value) == str(b.get("on_value", "ON")) else base_icon
                    self.hardware.display_logical(b["device"], key, icon or "", str(value))

    def event(self, device, control, gesture, value):
        if control == "_mobile_disconnect":
            self.release_all(device, disconnected=True)
            return
        if not self.config["devices"].get(device, {}).get("enabled"):
            return
        if control=='_touchpad_position':
            learning=self.learning if self.learning.get('expires',0)>time.time() else {}
            if learning.get('device')==device:return
            if not isinstance(value,(list,tuple)) or len(value)!=2 or any(type(v) is not int or not 0<=v<=100 for v in value):return
            report=self.brokers.send_position(device,*value)
            self.record(device,'TOUCHPAD_XY','position',list(value),report)
            return
        if control == '_deck_page':
            self.hardware.config=self.config
            current=self.hardware.active_page(device)
            if not (self.learning.get('device')==device and self.learning.get('expires',0)>time.time()):
                target={'next':current+1,'previous':current-1,'home':0,'index':int(value)}.get(gesture,current)
                self.change_page(device,target)
                self.record(device,control,'navigation',self.hardware.active_page(device)+1,{'delivered':0,'matched':1,'reason':'navigation','transmissions':[]})
            self.mobile.page_changed(device,force=True)
            return
        now = time.monotonic()
        control = canonical_control(control)
        self.hardware.config = self.config
        if re.fullmatch(r"key:\d+", control) and int(control[4:]) < 128:
            from .deck import artwork, logical_key, page_count, page_slot
            physical = int(control[4:])
            token = (device, control)
            if token in self.deck_ignored_releases or token in self.navigation_down:
                if gesture == "release":
                    self.deck_ignored_releases.discard(token)
                    self.navigation_down.discard(token)
                return
            current = self.hardware.active_page(device) if page_count(self.config, device) > 1 else 0
            mapped = self.deck_routes.get(token, f"key:{logical_key(physical,page_slot(self.config,device,current))}")
            learning_now = self.learning.get("device") == device and self.learning.get("expires",0) > time.time()
            if gesture == "press" and token not in self.deck_routes:
                style = artwork(self.config, device, physical, current)
                action = style.get("action", "mqtt")
                if action != "mqtt" and not learning_now:
                    target = {"next":current+1,"previous":current-1,"home":0,"goto":style.get("target_page",1)-1}[action]
                    self.change_page(device, target)
                    self.navigation_down.add(token)
                    report = {"delivered":0,"matched":1,"reason":"navigation","transmissions":[]}
                    self.record(device, mapped, "navigation", self.hardware.active_page(device)+1, report)
                    return
                self.deck_routes[token] = mapped
            elif gesture == "release":
                self.deck_routes.pop(token, None)
            control = mapped
        if control.startswith("key:") and gesture in ("press", "release"):
            self.hardware.set_pressed(device, int(control.split(":")[1]) % 128, gesture == "press")
        key = (device, control)
        was_down = key in self.pressed
        row = next((k for k in self.config.get("keys", []) if (k["device"], k["control"]) == key and k.get("enabled", True)), {})
        learning = self.learning if self.learning.get("expires", 0) > time.time() else {}
        suppressed = learning.get("device") == device or key in self.learning_releases
        if gesture == "press" and not was_down and not suppressed:
            self.step_cycles[key] = self.step_pass(key, row)
        skipped = not self.step_cycles.get(key, True)
        blocked = suppressed or skipped
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
        if skipped and not suppressed:
            self.buttons.cancel(key=key)
            report = {"delivered":0,"matched":0,"reason":"step_filter","transmissions":[]}
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
        if not blocked and gesture == "press" and not was_down and row.get("switch", True) and row and row.get("switch_mode", "toggle") == "toggle":
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
        if not blocked and button_enabled(row):
            for button_key, action in self.buttons.feed(key, gesture, now, row):
                self.button_event(button_key, action)
        if gesture == "release":
            self.step_cycles.pop(key, None)

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
                if self.step_pass(key, row):
                    self.brokers.send_report(*key, "press", 1, repeat_key=True)
                self.repeat_due[key] = now + row.get("repeat_interval", 150) / 1000

    def release_key(self, key):
        # Clear momentary state, not the latched toggle. Do not invent physical
        # release actions for existing individual bindings.
        if self.step_cycles.get(key, True):
            self.brokers.send_report(*key, "release", 0, switch_only=True)
        self.step_cycles.pop(key, None)
        if key[1].startswith("key:"):
            self.hardware.set_pressed(key[0], int(key[1].split(":")[1]) % 128, False)
        self.buttons.cancel(key=key)
        self.pressed.pop(key, None)
        self.repeat_due.pop(key, None)
        self.repeats.pop(key, None)

    def release_all(self, device=None, disconnected=False):
        self.buttons.cancel(device=device)
        if disconnected:
            self.step_counts = {key:value for key,value in self.step_counts.items() if device is not None and key[0]!=device}
        for key in list(self.pressed):
            if device is None or key[0] == device:
                self.release_key(key)
        held = {token for token in {*self.deck_routes, *self.navigation_down} if device is None or token[0] == device}
        for token in held:
            self.learning_releases.discard((token[0],self.deck_routes.get(token,token[1])))
        self.deck_routes = {token:value for token,value in self.deck_routes.items() if token not in held}
        self.navigation_down.difference_update(held)
        if disconnected:
            self.deck_ignored_releases = {token for token in self.deck_ignored_releases if device is not None and token[0] != device}
        else:
            self.deck_ignored_releases.update(held)

    def status(self):
        return {"version": __version__, "pid": __import__("os").getpid(), "updated": time.time(),
                "started": self.started, "devices": [d for d in self.hardware.inventory if d.get("connection") != "mobile"] + self.mobile.inventory(),
                "mobile": self.mobile.status(),
                "deck_pages": {ident:{"page":self.hardware.active_page(ident)+1,"pages":settings.get("deck_page_count",1)} for ident,settings in self.config["devices"].items() if settings.get("deck_info") or settings.get("deck_page_count",1)>1},
                "brokers": dict(self.brokers.states),
                "errors": {**self.hardware.errors, **{"Discovery " + key: value for key, value in self.brokers.discovery_errors.items()}},
                "events": list(self.events)}

    def run(self):
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda *_: setattr(self, "running", False))
        scan_at = status_at = reload_at = 0
        try:
            self.mobile.configure(self.config)
            while self.running:
                now = time.monotonic()
                lease = learning_lease()
                if lease.get("id") != self.learning.get("id") and lease:
                    self.release_all(lease["device"])
                self.learning = lease
                if now >= reload_at:
                    reload_at = now + 1
                    try:
                        self.mobile.synchronize_storage()
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
                            from .deck import page_slots
                            old_slots={ident:page_slots(old,ident)[self.hardware.active_page(ident)] for ident in old['devices']}
                            self.hardware.config = updated
                            for ident,slot in old_slots.items():
                                slots=page_slots(updated,ident)
                                self.hardware.page_states[ident]=slots.index(slot) if slot in slots else 0
                            self.hardware.page_feedback.clear()
                            self.mobile.configure(updated)
                            self.hardware.refresh_decks()
                            scan_at = 0
                    except Exception:
                        LOG.exception("Konfiguration konnte nicht übernommen werden")
                if now >= scan_at:
                    scan_at = now + 5
                    try:
                        self.hardware.scan(self.config)
                        present = {d["id"] for d in self.hardware.inventory}
                        for device in {key[0] for key in [*self.pressed, *self.buttons.keys, *self.deck_routes, *self.navigation_down, *self.deck_ignored_releases] if key[0] not in present}:
                            self.release_all(device, disconnected=True)
                        self.pressed = {key: value for key, value in self.pressed.items() if key[0] in present}
                    except Exception:
                        LOG.exception("USB-Erkennung fehlgeschlagen")
                self.hardware.poll()
                if self.mobile.refresh_required.is_set():
                    self.mobile.refresh_required.clear()
                    self.hardware.refresh_decks()
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
                self.hardware.animate()
                if now >= status_at:
                    status_at = now + 2
                    atomic_json(status_path(), self.status())
        finally:
            self.release_all()
            self.mobile.close()
            self.hardware.close()
            self.brokers.close()
            snapshot = self.status()
            snapshot["stopped"] = True
            atomic_json(status_path(), snapshot)
