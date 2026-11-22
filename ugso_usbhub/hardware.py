import hashlib
import logging
from pathlib import Path
import re
import select
import sys
import threading
import time
from .deck import artwork, key_image, logical_key, page_count, page_slot
from .storage import canonical_control
from .keymap import all_bindings

LOG = logging.getLogger(__name__)


def text(path):
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def identity(vendor, product, serial, port):
    token = serial or port
    return vendor + "-" + product + "-" + hashlib.sha256(token.encode()).hexdigest()[:12]


def unique_id(value):
    value=value.strip()
    return value if value.lower() not in ('none','(null)','unknown') and value.replace(':','').replace('-','').strip('0 ') else ''


def hardware_key(vendor, product, serial):
    return vendor+'-'+product+'-'+hashlib.sha256(serial.encode()).hexdigest() if serial else ''


def inventory():
    from StreamDeck.ProductIDs import USBProductIDs
    deck_products = {f"{value:04x}" for key, value in vars(USBProductIDs).items() if key.startswith("USB_PID_STREAMDECK_")}
    devices = []
    for path in sorted(Path("/sys/bus/usb/devices").glob("*")):
        if not (path / "idVendor").exists() or text(path / "bDeviceClass") == "09":
            continue
        vendor, product = text(path / "idVendor"), text(path / "idProduct")
        serial = unique_id(text(path / "serial"))
        real = path.resolve()
        inputs = []
        for event in Path("/sys/class/input").glob("event*"):
            if event.resolve().is_relative_to(real):
                inputs.append("/dev/input/" + event.name)
        record={"id": identity(vendor, product, serial, path.name),
                        "vendor": vendor, "product_id": product, "serial": serial,
                        "bus": int(text(path / "busnum") or 0), "address": int(text(path / "devnum") or 0),
                        "port": path.name, "name": text(path / "product") or f"USB {vendor}:{product}",
                        "inputs": inputs, "kind": "streamdeck" if vendor == "0fd9" and product in deck_products else "input" if inputs else "inventory",
                        "identity_hint": "Seriennummer · portunabhängig" if serial else "Keine eindeutige Seriennummer · bei Umstecken vorhandenem Gerät zuordnen",
                        "hardware_key":hardware_key(vendor,product,serial)}
        devices.append(record)
        # Unifying/Bolt receivers can expose separate paired HID++ input units.
        # Preserve the receiver as a legacy input route; child routes are opt-in.
        units={}
        if vendor=='046d':
            for event_name in inputs:
                node=Path('/sys/class/input')/Path(event_name).name/'device'
                unit_vendor=text(node/'id/vendor');unit_product=text(node/'id/product')
                if unit_vendor!='046d' or not unit_product or unit_product==product:continue
                unit=unique_id(text(node/'uniq'))
                hid=next((p for p in node.resolve().parents if re.match(r'^\w{4}:\w{4}:\w{4}\.',p.name)),node.resolve())
                group=(unit_product,unit or str(hid))
                if group not in units:
                    units[group]={'id':identity(vendor,unit_product,unit,path.name+':'+hid.name),
                        'vendor':vendor,'product_id':unit_product,'serial':unit,'port':path.name+':'+hid.name,
                        'bus':record['bus'],'address':record['address'],'name':text(node/'name') or 'Logitech HID++',
                        'kind':'input','inputs':[],'receiver_id':record['id'],
                        'hardware_key':hardware_key(vendor,unit_product,unit),
                        'identity_hint':'Logitech-Gerätekennung · portunabhängig' if unit else 'Logitech-Gerät ohne eindeutige Kennung · manuelle Zuordnung möglich'}
                units[group]['inputs'].append(event_name)
        devices.extend(units.values())
    return devices


def match_transport(path, devices):
    """hidapi-libusb uses hexadecimal bus:address:interface paths on Linux."""
    match = re.match(r"^([0-9a-fA-F]+):([0-9a-fA-F]+):", path)
    if match:
        bus, address = (int(x, 16) for x in match.groups())
        return next((ident for ident, d in devices.items() if d["kind"] == "streamdeck" and d.get("bus") == bus and d.get("address") == address), None)
    if path.startswith("/dev/hidraw"):
        node = (Path("/sys/class/hidraw") / Path(path).name).resolve()
        return next((ident for ident, d in devices.items() if d["kind"] == "streamdeck" and (Path("/sys/bus/usb/devices") / d["port"]).resolve() in node.parents), None)
    return None


class Hardware:
    def __init__(self, emit):
        self.emit = emit
        self.inputs = {}
        self.decks = {}
        self.inventory = []
        self.config = {"devices": {}, "bindings": []}
        self.lock = threading.RLock()
        self.errors = {}
        self.mobile = None
        self.pressed_keys = set()
        self.display_contents = {}
        self.animations = {}
        self.page_states = {}
        self.page_feedback = {}
        self.touchpads = {}

    def active_page(self, ident):
        return max(0, min(self.page_states.get(ident, 0), page_count(self.config, ident)-1))

    def set_page(self, ident, page):
        page = max(0, min(page, page_count(self.config, ident)-1))
        if page == self.active_page(ident):
            return False
        self.page_states[ident] = page
        self.pressed_keys = {token for token in self.pressed_keys if token[0] != ident}
        self.animations = {token:job for token,job in self.animations.items() if token[0] != ident}
        self.refresh_decks(ident)
        if self.mobile:
            self.mobile.page_changed(ident)
        return True

    def display_logical(self, ident, key, icon="", label="", brightness=None):
        self.page_feedback[(ident, key)] = (icon, label)
        if key // 128 == page_slot(self.config, ident, self.active_page(ident)):
            self.display(ident, key % 128, icon, label, brightness)

    def scan(self, config):
        self.config = config
        from .devices import resolve_inventory
        self.inventory = resolve_inventory(inventory(),config) + (self.mobile.inventory() if self.mobile else [])
        allowed = {d["id"]: d for d in self.inventory if config["devices"].get(d["id"], {}).get("enabled")}
        paths = {p: ident for ident, d in allowed.items() if d["kind"] == "input" for p in d["inputs"]}
        for path in list(self.inputs):
            if path not in paths or self.inputs[path][0]!=paths[path]:
                self.inputs.pop(path)[1].close()
                self.touchpads.pop(path,None)
        if sys.platform == "linux":
            import evdev
            for path, ident in paths.items():
                if path not in self.inputs:
                    try:
                        self.inputs[path] = (ident, evdev.InputDevice(path))
                        self.errors.pop(path, None)
                    except OSError as exc:
                        self.errors[path] = str(exc)
            for path,(ident,device) in self.inputs.items():
                if not config['devices'].get(ident,{}).get('touchpad_gestures'):
                    self.touchpads.pop(path,None);continue
                if path in self.touchpads:
                    self.touchpads[path].configure(config['devices'].get(ident,{}));continue
                try:
                    caps=device.capabilities()
                    codes=[c[0] if isinstance(c,tuple) else c for c in caps.get(evdev.ecodes.EV_ABS,[])]
                    if all(c in codes for c in (0x2f,0x35,0x36,0x39)) and evdev.ecodes.INPUT_PROP_DIRECT not in device.input_props():
                        from .touchpad import Touchpad
                        x,y=device.absinfo(0x35),device.absinfo(0x36)
                        self.touchpads[path]=Touchpad(lambda control,gesture,value,ident=ident:self.emit(ident,control,gesture,value),(x.min,x.max),(y.min,y.max),config['devices'].get(ident,{}))
                except (OSError,ValueError) as exc:
                    self.errors[path]=str(exc)
        self._scan_decks({ident:d for ident,d in allowed.items() if d.get("connection") != "mobile"})
        for device in self.inventory:
            deck = self.decks.get(device["id"])
            if deck:
                device["deck"] = {"model": deck.deck_type(), "keys": deck.key_count(),
                                  "layout": list(deck.key_layout()), "visual": deck.is_visual(),
                                  "size": list(deck.key_image_format()["size"]) if deck.is_visual() else [72, 72]}

    def _scan_decks(self, allowed):
        added = False
        for ident in list(self.decks):
            if ident not in allowed or not self.decks[ident].connected():
                try:
                    self.decks.pop(ident).close()
                except Exception:
                    LOG.warning("Stream Deck konnte nicht geschlossen werden")
        if not any(d["kind"] == "streamdeck" and ident not in self.decks for ident, d in allowed.items()):
            return
        try:
            from StreamDeck.DeviceManager import DeviceManager
            for deck in DeviceManager().enumerate():
                candidate = match_transport(deck.id(), allowed)
                if not candidate or candidate in self.decks:
                    continue
                deck.open()
                self.decks[candidate] = deck
                added = True
                deck.set_key_callback(lambda d, key, state, ident=candidate: self.emit(ident, f"key:{key}", "press" if state else "release", int(state)))
                if hasattr(deck, "set_dial_callback"):
                    def dial_callback(d, dial, event, value, ident=candidate):
                        from StreamDeck.Devices.StreamDeck import DialEventType
                        gesture = ("rotate_right" if value > 0 else "rotate_left") if event == DialEventType.TURN else ("press" if value else "release")
                        self.emit(ident, f"dial:{dial}", gesture, value)
                    deck.set_dial_callback(dial_callback)
                if hasattr(deck, "set_touchscreen_callback"):
                    deck.set_touchscreen_callback(lambda d, event, value, ident=candidate: self.emit(ident, "touchscreen", "touch", str(value)))
                self.errors.pop(candidate, None)
        except Exception as exc:
            self.errors["streamdeck"] = str(exc)
        if added:
            self.refresh_decks()

    def refresh_decks(self, only=None):
        decks = {**self.decks, **(self.mobile.decks() if self.mobile else {})}
        for ident, deck in list(decks.items()):
            if only is not None and ident != only:
                continue
            try:
                self.page_states[ident] = self.active_page(ident)
                deck.set_brightness(int(self.config["devices"].get(ident, {}).get("brightness", 30)))
                bindings = all_bindings(self.config)
                for key in range(deck.key_count()):
                    page = self.active_page(ident)
                    logical = logical_key(key, page_slot(self.config,ident,page))
                    style = artwork(self.config, ident, key, page)
                    b = next((b for b in bindings if b["device"] == ident and b["control"] == f"key:{logical}"), {})
                    icon, label = self.page_feedback.get((ident, logical), (style.get("icon", b.get("icon", "")), style.get("text", b.get("text", ""))))
                    self.display(ident, key, icon, label)
            except Exception as exc:
                self.errors[ident] = str(exc)

    def display(self, ident, key, icon="", label="", brightness=None):
        with self.lock:
            self.display_contents[(ident, key)] = (icon, label)
            deck = self.decks.get(ident) or (self.mobile.decks().get(ident) if self.mobile else None)
            if not deck:
                self.animations.pop((ident, key), None)
                return
            if brightness is not None:
                deck.set_brightness(max(0, min(100, int(brightness))))
            if not 0 <= key < deck.key_count() or not deck.is_visual():
                return
            from StreamDeck.ImageHelpers import PILHelper
            page = self.active_page(ident)
            style = artwork(self.config, ident, key, page)
            from .icons import animation
            pressed = (ident, key) in self.pressed_keys
            selected = (style.get("pressed_icon") or icon) if pressed else icon
            durations = animation(selected)
            if durations:
                self.animations[(ident, key)] = {"start":time.monotonic(), "durations":durations,
                                                "index":0, "icon":icon, "label":label}
            else:
                self.animations.pop((ident, key), None)
            image = key_image(deck.key_image_format()["size"], style, icon, label,
                              pressed=(ident, key) in self.pressed_keys, page=page, pages=page_count(self.config, ident))
            deck.set_key_image(key, PILHelper.to_native_format(deck, image))

    def animate(self, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            decks = {**self.decks, **(self.mobile.decks() if self.mobile else {})}
            for (ident, key), job in list(self.animations.items()):
                deck = decks.get(ident)
                if not deck or not deck.connected() or key >= deck.key_count():
                    self.animations.pop((ident, key), None)
                    continue
                elapsed = max(0, int((now-job["start"])*1000)) % sum(job["durations"])
                index = 0
                for duration in job["durations"]:
                    if elapsed < duration:
                        break
                    elapsed -= duration; index += 1
                if index == job["index"]:
                    continue
                try:
                    from StreamDeck.ImageHelpers import PILHelper
                    image = key_image(deck.key_image_format()["size"], artwork(self.config, ident, key, self.active_page(ident)),
                                      job["icon"], job["label"], pressed=(ident,key) in self.pressed_keys,
                                      frame_index=index, page=self.active_page(ident), pages=page_count(self.config, ident))
                    deck.set_key_image(key, PILHelper.to_native_format(deck, image))
                    job["index"] = index
                except Exception as exc:
                    self.animations.pop((ident, key), None)
                    self.errors[ident] = str(exc)

    def set_pressed(self, ident, key, pressed):
        with self.lock:
            token = (ident, key)
            if (token in self.pressed_keys) == pressed:
                return
            if pressed:
                self.pressed_keys.add(token)
            else:
                self.pressed_keys.discard(token)
            page = self.active_page(ident)
            style = artwork(self.config, ident, key, page)
            if not any(style.get(name) for name in ("pressed_icon", "pressed_background", "pressed_text_color")):
                return
            binding = next((b for b in all_bindings(self.config)
                            if b["device"] == ident and b["control"] == f"key:{logical_key(key,page_slot(self.config,ident,page))}"), {})
            icon, label = self.display_contents.get(token, (style.get("icon", binding.get("icon", "")),
                                                           style.get("text", binding.get("text", ""))))
            try:
                self.display(ident, key, icon, label)
            except Exception as exc:
                self.errors[ident] = str(exc)

    def poll(self, timeout=0.05):
        for pad in self.touchpads.values():pad.tick(time.monotonic())
        if not self.inputs:
            time.sleep(timeout)
            return
        import evdev
        handles = {device.fd: (path, ident, device) for path, (ident, device) in self.inputs.items()}
        try:
            ready, _, _ = select.select(list(handles), [], [], timeout)
        except OSError:
            return
        for fd in ready:
            path, ident, device = handles[fd]
            try:
                for event in device.read():
                    pad=self.touchpads.get(path)
                    if pad:pad.feed(event.type,event.code,event.value,time.monotonic())
                    if event.type == evdev.ecodes.EV_KEY:
                        control = evdev.ecodes.KEY.get(event.code, evdev.ecodes.BTN.get(event.code, str(event.code)))
                        control = canonical_control(control)
                        if pad and (control=='BTN_TOUCH' or control.startswith('BTN_TOOL_')):continue
                        self.emit(ident, control, {0: "release", 1: "press", 2: "repeat"}.get(event.value, "press"), event.value)
                    elif event.type == evdev.ecodes.EV_REL and event.value:
                        self.emit(ident, evdev.ecodes.REL.get(event.code, str(event.code)), "rotate_right" if event.value > 0 else "rotate_left", event.value)
            except OSError as exc:
                self.errors[path] = str(exc)
                self.inputs.pop(path, None)
                self.touchpads.pop(path, None)
                device.close()

    def close(self):
        self.animations.clear()
        self.touchpads.clear()
        for _, device in self.inputs.values():
            device.close()
        for deck in self.decks.values():
            deck.close()
