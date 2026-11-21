import hashlib
import logging
from pathlib import Path
import re
import select
import sys
import threading
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .storage import home

LOG = logging.getLogger(__name__)


def text(path):
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def identity(vendor, product, serial, port):
    token = serial or port
    return vendor + "-" + product + "-" + hashlib.sha256(token.encode()).hexdigest()[:12]


def inventory():
    from StreamDeck.ProductIDs import USBProductIDs
    deck_products = {f"{value:04x}" for key, value in vars(USBProductIDs).items() if key.startswith("USB_PID_STREAMDECK_")}
    devices = []
    for path in sorted(Path("/sys/bus/usb/devices").glob("*")):
        if not (path / "idVendor").exists() or text(path / "bDeviceClass") == "09":
            continue
        vendor, product = text(path / "idVendor"), text(path / "idProduct")
        serial = text(path / "serial")
        real = path.resolve()
        inputs = []
        for event in Path("/sys/class/input").glob("event*"):
            if event.resolve().is_relative_to(real):
                inputs.append("/dev/input/" + event.name)
        devices.append({"id": identity(vendor, product, serial, path.name),
                        "vendor": vendor, "product_id": product, "serial": serial,
                        "bus": int(text(path / "busnum") or 0), "address": int(text(path / "devnum") or 0),
                        "port": path.name, "name": text(path / "product") or f"USB {vendor}:{product}",
                        "inputs": inputs, "kind": "streamdeck" if vendor == "0fd9" and product in deck_products else "input" if inputs else "inventory",
                        "identity_hint": "Seriennummer" if serial else "USB-Port (beim Umstecken neu zuordnen)"})
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

    def scan(self, config):
        self.config = config
        self.inventory = inventory()
        allowed = {d["id"]: d for d in self.inventory if config["devices"].get(d["id"], {}).get("enabled")}
        paths = {p: ident for ident, d in allowed.items() if d["kind"] == "input" for p in d["inputs"]}
        for path in list(self.inputs):
            if path not in paths:
                self.inputs.pop(path)[1].close()
        if sys.platform == "linux":
            import evdev
            for path, ident in paths.items():
                if path not in self.inputs:
                    try:
                        self.inputs[path] = (ident, evdev.InputDevice(path))
                        self.errors.pop(path, None)
                    except OSError as exc:
                        self.errors[path] = str(exc)
        self._scan_decks(allowed)

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

    def refresh_decks(self):
        for ident, deck in list(self.decks.items()):
            try:
                deck.set_brightness(int(self.config["devices"].get(ident, {}).get("brightness", 30)))
                for b in self.config["bindings"]:
                    if b["device"] == ident and b["control"].startswith("key:"):
                        self.display(ident, int(b["control"].split(":")[1]), b.get("icon", ""), b.get("text", ""))
            except Exception as exc:
                self.errors[ident] = str(exc)

    def display(self, ident, key, icon="", label="", brightness=None):
        with self.lock:
            deck = self.decks.get(ident)
            if not deck:
                return
            if brightness is not None:
                deck.set_brightness(max(0, min(100, int(brightness))))
            if not 0 <= key < deck.key_count() or not deck.is_visual():
                return
            from StreamDeck.ImageHelpers import PILHelper
            image = PILHelper.create_image(deck)
            if len(icon) == 32 and all(c in "0123456789abcdef" for c in icon):
                path = home() / "icons" / (icon + ".png")
                if path.exists():
                    with Image.open(path) as source:
                        tile = ImageOps.contain(source.convert("RGBA"), image.size)
                        image.paste(tile, ((image.width - tile.width) // 2, 0), tile)
            if label:
                draw = ImageDraw.Draw(image)
                font = ImageFont.load_default(size=max(10, image.width // 7))
                # Deliberately bounded text; no arbitrary font/file/URL access over MQTT.
                label = str(label)[:24]
                while label and draw.textbbox((0, 0), label, font=font)[2] > image.width - 4:
                    label = label[:-1]
                y = image.height - max(15, image.width // 5)
                draw.rectangle((0, y, image.width, image.height), fill="black")
                draw.text((image.width // 2, y), label, fill="white", anchor="mt", font=font)
            deck.set_key_image(key, PILHelper.to_native_format(deck, image))

    def poll(self, timeout=0.05):
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
                    if event.type == evdev.ecodes.EV_KEY:
                        control = evdev.ecodes.KEY.get(event.code, evdev.ecodes.BTN.get(event.code, str(event.code)))
                        if isinstance(control, list):
                            control = control[0]
                        self.emit(ident, control, {0: "release", 1: "press", 2: "repeat"}.get(event.value, "press"), event.value)
                    elif event.type == evdev.ecodes.EV_REL and event.value:
                        self.emit(ident, evdev.ecodes.REL.get(event.code, str(event.code)), "rotate_right" if event.value > 0 else "rotate_left", event.value)
            except OSError as exc:
                self.errors[path] = str(exc)
                self.inputs.pop(path, None)
                device.close()

    def close(self):
        for _, device in self.inputs.values():
            device.close()
        for deck in self.decks.values():
            deck.close()
