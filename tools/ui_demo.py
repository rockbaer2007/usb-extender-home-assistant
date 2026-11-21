"""Local UI test data only; does not open USB devices or connect to MQTT."""
import os
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["UGSO_USB_HOME"] = str(Path(__file__).resolve().parents[1] / ".state" / "ui-demo")
from ugso_usbhub.storage import load_config, save_config, password_hash, atomic_json, home
from ugso_usbhub.icons import add
from PIL import Image, ImageDraw
import io

c = load_config()
c["password_hash"] = password_hash("local-demo-only-123")
c["web"] = {"host": "127.0.0.1", "port": 8098}
c["devices"] = {"demo-deck": {"name": "Stream Deck · Arbeitszimmer", "enabled": True, "receive_broker": "broker1", "targets": ["broker1"], "brightness": 35}, "demo-keyboard": {"name": "Medientastatur", "enabled": True, "receive_broker": "", "targets": ["broker1", "broker2"], "brightness": 30}}
for index, b in enumerate(c["brokers"]):
    b.update(name=["Home Assistant", "Werkstatt", "Reserve"][index], host="mqtt.example.invalid", enabled=False)
icon_ids = []
for label, color in (("Licht", "#f5ce66"), ("Musik", "#6de1b9"), ("Heizung", "#e49c83")):
    image = Image.new("RGB", (144, 144), "#142131")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 26, 116, 118), radius=20, outline=color, width=7)
    draw.ellipse((56, 54, 88, 86), fill=color)
    data = io.BytesIO()
    image.save(data, "PNG")
    icon_ids.append(add(data.getvalue(), label + ".png", "Eigene Icons"))
c["bindings"] = [{"id": "light", "device": "demo-deck", "control": "key:0", "gesture": "press", "targets": None, "icon": icon_ids[0], "text": "Licht", "state_topic": "haus/licht/state", "on_value": "ON"}]
save_config(c)
atomic_json(home() / "status.json", {"version": "0.1.0", "updated": time.time(), "devices": [{"id": "demo-deck", "name": "Stream Deck MK.2", "kind": "streamdeck", "identity_hint": "Seriennummer · lokale Beispieldaten"}, {"id": "demo-keyboard", "name": "USB Multimedia Keyboard", "kind": "input", "identity_hint": "USB-Port · lokale Beispieldaten"}], "events": [{"time": time.time(), "device": "demo-deck", "control": "key:0", "gesture": "press", "value": 1, "delivered": 1}], "brokers": {"broker1": "online", "broker2": "offline"}, "errors": {}})
print("LOCAL UI DEMO ONLY: http://127.0.0.1:8098 / local-demo-only-123", flush=True)
from ugso_usbhub.web import run
run()
