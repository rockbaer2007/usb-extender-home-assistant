import copy
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request
import http.cookiejar
import zipfile
from PIL import Image
from ugso_usbhub import icons
from ugso_usbhub.storage import defaults, home, atomic_json, load_config, save_config, validate, public_config, merge_public, password_hash, check_password, canonical_control
from ugso_usbhub.mqtt import Brokers, resolve_targets
from ugso_usbhub.hardware import identity, match_transport, Hardware
from ugso_usbhub.web import Server
from tests.broker import Broker, wait_for


class TemporaryHome(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"UGSO_USB_HOME": self.temp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()


class ConfigTests(TemporaryHome):
    def test_three_slots_and_validation(self):
        c = defaults()
        validate(c)
        self.assertFalse(any(b["discovery"] for b in c["brokers"]))
        c["brokers"].append(copy.deepcopy(c["brokers"][0]))
        with self.assertRaises(ValueError):
            validate(c)

    def test_credentials_not_returned_and_preserved(self):
        c = defaults()
        c["brokers"][0]["password"] = "mqtt-secret"
        c["password_hash"] = password_hash("long-test-password")
        public = public_config(c)
        self.assertNotIn("mqtt-secret", json.dumps(public))
        self.assertNotIn("password_hash", public)
        self.assertEqual(merge_public(public, c)["brokers"][0]["password"], "mqtt-secret")
        public["brokers"][0]["clear_password"] = True
        self.assertEqual(merge_public(public, c)["brokers"][0]["password"], "")

    def test_atomic_persistence_and_ten_backups(self):
        c = load_config()
        for i in range(13):
            c["devices"]["demo"] = {"name": str(i), "targets": ["broker2"]}
            save_config(c)
        self.assertEqual(load_config()["devices"]["demo"]["name"], "12")
        self.assertEqual(len(list((home() / "backups").glob("*.json"))), 10)

    def test_password(self):
        value = password_hash("test-password-123")
        self.assertTrue(check_password("test-password-123", value))
        self.assertFalse(check_password("wrong", value))

    def test_routing_precedence(self):
        c = defaults()
        c["devices"]["a"] = {"targets": ["broker2"]}
        self.assertEqual(resolve_targets(c, "unknown", {}), ["broker1"])
        self.assertEqual(resolve_targets(c, "a", {}), ["broker2"])
        self.assertEqual(resolve_targets(c, "a", {"targets": ["broker3"]}), ["broker3"])
        self.assertEqual(resolve_targets(c, "a", {"targets": []}), [])

    def test_stable_identity_and_port_fallback(self):
        self.assertEqual(identity("0fd9", "1", "serial", "port1"), identity("0fd9", "1", "serial", "port2"))
        self.assertNotEqual(identity("1", "2", "", "port1"), identity("1", "2", "", "port2"))

    def test_streamdeck_transport_without_usb_serial(self):
        devices = {"a": {"kind": "streamdeck", "bus": 1, "address": 10}, "b": {"kind": "streamdeck", "bus": 1, "address": 11}}
        self.assertEqual(match_transport("0001:000a:00", devices), "a")
        self.assertEqual(match_transport("0001:000b:00", devices), "b")
        self.assertIsNone(match_transport("0001:000c:00", devices))

    def test_evdev_aliases_and_existing_mapping_are_canonical(self):
        for value in (("KEY_MIN_INTERESTING", "KEY_MUTE"), ["KEY_MIN_INTERESTING", "KEY_MUTE"], "KEY_MUTE"):
            self.assertEqual(canonical_control(value), "KEY_MUTE")
        config = defaults()
        config["bindings"] = [{"id": "mute", "device": "demo", "control": ["KEY_MIN_INTERESTING", "KEY_MUTE"], "gesture": "press"}]
        self.assertEqual(validate(config)["bindings"][0]["control"], "KEY_MUTE")
        with self.assertRaises(ValueError):
            canonical_control({"not": "a key"})

    def test_keyboard_spelling_and_streamdeck_number(self):
        self.assertEqual(canonical_control("key:tab"), "KEY_TAB")
        self.assertEqual(canonical_control("key:volumeup"), "KEY_VOLUMEUP")
        self.assertEqual(canonical_control("key_tab"), "KEY_TAB")
        self.assertEqual(canonical_control("key:0"), "key:0")
        config = defaults()
        config["bindings"] = [{"id": "tab", "device": "keyboard", "control": "key:tab", "gesture": "press"}]
        self.assertEqual(public_config(config)["bindings"][0]["control"], "KEY_TAB")
        self.assertEqual(validate(config)["bindings"][0]["control"], "KEY_TAB")


def png():
    out = io.BytesIO()
    Image.new("RGB", (72, 72), "#11aa88").save(out, "PNG")
    return out.getvalue()


class IconTests(TemporaryHome):
    def test_folder_and_dedup(self):
        folder = home() / "source"
        folder.mkdir()
        (folder / "lamp.png").write_bytes(png())
        self.assertEqual(icons.import_folder(folder)["imported"], 1)
        icons.import_folder(folder)
        self.assertEqual(len(icons.library()), 1)
        with Image.open(icons.cached_path(icons.library()[0]["id"])) as image:
            self.assertEqual(image.size, (256, 256))

    def test_official_pack_structure_and_license(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("demo.sdIconPack/manifest.json", json.dumps({"Name": "Example pack", "Author": "Test author"}))
            z.writestr("demo.sdIconPack/icons.json", json.dumps([{"path": "icons/lamp.png", "name": "Lampe", "tags": ["light"]}]))
            z.writestr("demo.sdIconPack/license.txt", "Test license")
            z.writestr("demo.sdIconPack/icons/lamp.png", png())
        result = icons.import_archive(out.getvalue(), "example.streamDeckIconPack")
        self.assertEqual(result["imported"], 1)
        item = icons.library()[0]
        self.assertEqual((item["name"], item["author"], item["license"], item["tags"]), ("Lampe", "Test author", "Test license", ["light"]))

    def test_traversal_rejected(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr("../outside.png", png())
        with self.assertRaises(ValueError):
            icons.import_archive(out.getvalue(), "bad.zip")

    def test_svg_external_and_active_rejected(self):
        for body in ('<image href="https://example.org/x.png"/>', '<script>alert(1)</script>', '<rect style="fill:url(http://example.org)"/>', '<style>@import "http://example.org"</style>'):
            with self.assertRaises(ValueError):
                icons.raster(('<svg xmlns="http://www.w3.org/2000/svg">' + body + '</svg>').encode(), ".svg")

    def test_animation_uses_first_frame(self):
        out = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(out, "GIF", save_all=True, append_images=[Image.new("RGB", (10, 10), "blue")])
        rendered = icons.raster(out.getvalue(), ".gif")
        with Image.open(io.BytesIO(rendered)) as image:
            self.assertEqual(image.getpixel((128, 128))[:3], (255, 0, 0))


class MqttTests(TemporaryHome):
    def setUp(self):
        super().setUp()
        self.servers = [Broker() for _ in range(3)]
        c = self.config = defaults()
        for b, server in zip(c["brokers"], self.servers):
            b.update(enabled=True, host="127.0.0.1", port=server.port, discovery=True)
        c["default_targets"] = [b["id"] for b in c["brokers"]]
        c["devices"]["deck"] = {"enabled": True, "receive_broker": "broker2"}
        c["bindings"] = [{"id": "lamp", "device": "deck", "control": "key:0", "gesture": "press", "state_topic": "test/state"}]
        self.received = []
        self.pool = Brokers(c, lambda *x: self.received.append(x))
        wait_for(lambda: len(self.pool.states) == 3 and all(s == "online" for s in self.pool.states.values()))

    def tearDown(self):
        self.pool.close()
        for server in self.servers:
            server.close()
        super().tearDown()

    def test_three_real_paho_connections_and_no_retained_presses(self):
        self.assertEqual(self.pool.send("deck", "key:0", "press"), 3)
        wait_for(lambda: all(any("/event/" in m[0] for m in s.messages) for s in self.servers))
        for server in self.servers:
            event = next(m for m in server.messages if "/event/" in m[0])
            self.assertFalse(event[2])
            self.assertEqual(json.loads(event[1])["event_type"], "press")
            self.assertTrue(any(m[0].startswith("homeassistant/device_automation/") for m in server.messages))

    def test_identical_topic_and_payload_on_all_brokers(self):
        self.config["bindings"][0]["topic"] = "haus/usb/taste"
        self.assertEqual(self.pool.send("deck", "key:0", "press"), 3)
        wait_for(lambda: all(any(m[0] == "haus/usb/taste" for m in s.messages) for s in self.servers))
        copies = [next(m for m in s.messages if m[0] == "haus/usb/taste") for s in self.servers]
        self.assertEqual(copies[0], copies[1])
        self.assertEqual(copies[1], copies[2])
        self.assertFalse(copies[0][2])

    def test_one_broker_down_others_continue(self):
        self.servers[0].close()
        wait_for(lambda: self.pool.states["broker1"] == "offline")
        self.assertEqual(self.pool.send("deck", "key:0", "press"), 2)
        self.assertEqual(self.pool.send("deck", "key:1", "press"), 0)

    def test_state_subscription_and_ha_birth(self):
        wait_for(lambda: "test/state" in self.servers[1].subscriptions)
        self.assertNotIn("test/state", self.servers[0].subscriptions)
        self.servers[1].publish("test/state", "ON")
        wait_for(lambda: ("broker2", "test/state", "ON") in self.received)
        before = len([m for m in self.servers[1].messages if m[0].startswith("homeassistant/")])
        self.servers[1].publish("homeassistant/status", "online")
        wait_for(lambda: len([m for m in self.servers[1].messages if m[0].startswith("homeassistant/")]) > before)

    def test_missing_ca_does_not_block_other_brokers(self):
        self.pool.close()
        self.config["brokers"][0].update(tls=True, ca_file="/file-that-does-not-exist/ca.pem")
        self.pool = Brokers(self.config, lambda *x: None)
        wait_for(lambda: self.pool.states["broker2"] == "online" and self.pool.states["broker3"] == "online")
        self.assertIn("Konfigurationsfehler", self.pool.states["broker1"])
        self.assertEqual(self.pool.send("deck", "key:0", "press"), 2)

    def test_deleted_binding_discovery_is_removed(self):
        wait_for(lambda: all(any(m[0].startswith("homeassistant/") for m in s.messages) for s in self.servers))
        replacement = copy.deepcopy(self.config)
        replacement["bindings"] = []
        self.pool.cleanup_removed(replacement)
        wait_for(lambda: all(any(m[0].startswith("homeassistant/") and m[1] == b"" and m[2] for m in s.messages) for s in self.servers))

    def restart_without_discovery(self, fresh=False, legacy=False):
        wait_for(lambda: all(any(m[0].startswith("homeassistant/") for m in s.messages) for s in self.servers))
        self.pool.close()
        if legacy:
            atomic_json(home() / "backups" / "legacy.json", copy.deepcopy(self.config))
        if fresh or legacy:
            (home() / "discovery.json").unlink(missing_ok=True)
        for server in self.servers:
            server.messages.clear()
            server.subscriptions.clear()
        for broker in self.config["brokers"]:
            broker["discovery"] = False
        self.pool = Brokers(self.config, lambda *x: None)
        wait_for(lambda: all(s == "online" for s in self.pool.states.values()))
        self.assertEqual(self.pool.send("deck", "key:0", "press"), 3)
        wait_for(lambda: all(any("/event/" in m[0] for m in s.messages) for s in self.servers))

    def test_discovery_off_sends_data_without_ha_announcements(self):
        self.restart_without_discovery(fresh=True)
        for server in self.servers:
            self.assertFalse(any(m[0].startswith("homeassistant/") for m in server.messages))
            self.assertNotIn("homeassistant/status", server.subscriptions)

    def test_discovery_error_does_not_stop_mqtt_data(self):
        self.pool.close()
        for server in self.servers:
            server.messages.clear()
        with patch.object(Brokers, "discovery", side_effect=ValueError("Simulierter Discovery-Fehler")):
            with self.assertLogs("ugso_usbhub.mqtt", level="ERROR"):
                self.pool = Brokers(self.config, lambda *x: None)
                wait_for(lambda: len(self.pool.discovery_errors) == 3)
            self.assertEqual(self.pool.send("deck", "key:0", "press"), 3)
            wait_for(lambda: all(any("/event/" in m[0] for m in server.messages) for server in self.servers))

    def test_discovery_off_removes_own_retained_configs_after_reconnect(self):
        self.restart_without_discovery()
        for server in self.servers:
            cleanup = [m for m in server.messages if m[0].startswith("homeassistant/")]
            self.assertTrue(cleanup)
            self.assertTrue(all(m[1] == b"" and m[2] for m in cleanup))
            self.assertTrue(all(f"ugso_{self.config['hub_id']}_lamp" in m[0] for m in cleanup))

    def test_legacy_discovery_is_cleaned_from_config_backup(self):
        self.restart_without_discovery(legacy=True)
        for server in self.servers:
            cleanup = [m for m in server.messages if m[0].startswith("homeassistant/")]
            self.assertTrue(cleanup)
            self.assertTrue(all(m[1] == b"" and m[2] for m in cleanup))

    def test_turning_off_discovery_cleans_connected_broker(self):
        replacement = copy.deepcopy(self.config)
        replacement["brokers"][0]["discovery"] = False
        self.pool.cleanup_removed(replacement)
        wait_for(lambda: any(m[0].startswith("homeassistant/") and m[1] == b"" for m in self.servers[0].messages))
        self.assertFalse(any(m[0].startswith("homeassistant/") and m[1] == b"" for m in self.servers[1].messages))

    def test_delivery_diagnostics_and_keyboard_alias(self):
        self.config["bindings"][0]["control"] = "key:tab"
        report = self.pool.send_report("deck", "KEY_TAB", "press")
        self.assertEqual((report["reason"], report["delivered"]), ("sent", 3))
        self.assertTrue(all(tx["state"] == "sent" and "/event/deck/lamp" in tx["topic"] for tx in report["transmissions"]))
        self.assertEqual(self.pool.send_report("deck", "KEY_A", "press")["reason"], "no_binding")
        self.config["bindings"][0]["targets"] = []
        self.assertEqual(self.pool.send_report("deck", "KEY_TAB", "press")["reason"], "no_targets")
        self.config["bindings"][0]["targets"] = ["broker1"]
        self.pool.clients["broker1"].disconnect()
        wait_for(lambda: self.pool.states["broker1"] == "offline")
        report = self.pool.send_report("deck", "KEY_TAB", "press")
        self.assertEqual(report["reason"], "not_connected")
        self.assertEqual(report["transmissions"][0]["state"], "offline")


class WebTests(TemporaryHome):
    def setUp(self):
        super().setUp()
        c = load_config()
        c["password_hash"] = password_hash("test-password-123")
        save_config(c)
        self.server = Server(("127.0.0.1", 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = "http://127.0.0.1:" + str(self.server.server_port)
        self.client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        super().tearDown()

    def request(self, path, data=None, extra=None):
        req = urllib.request.Request(self.url + path, data=None if data is None else json.dumps(data).encode(), headers={"Content-Type": "application/json", "X-UGSo-Request": "1", **(extra or {})})
        return self.client.open(req, timeout=3)

    def login(self):
        with self.request("/api/login", {"password": "test-password-123"}) as r:
            self.assertEqual(r.status, 200)

    def test_auth_required_and_no_secrets(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/config")
        self.assertEqual(error.exception.code, 401)
        self.login()
        with self.request("/api/config") as r:
            value = json.load(r)
        self.assertNotIn("password_hash", value)
        value["brokers"][0]["name"] = "Test MQTT"
        with self.request("/api/config", value) as r:
            self.assertEqual(r.status, 200)
        self.assertEqual(load_config()["brokers"][0]["name"], "Test MQTT")

    def test_cross_origin_rejected(self):
        self.login()
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/config", public_config(load_config()), {"Origin": "http://other-host:99"})
        self.assertEqual(error.exception.code, 403)

    def test_service_liveness_uses_server_clock(self):
        self.login()
        snapshot = {"updated": 995, "devices": [], "events": [], "errors": {}, "brokers": {}}
        atomic_json(home() / "status.json", snapshot)
        with patch("ugso_usbhub.web.time.time", return_value=1000):
            with self.request("/api/status") as r:
                result = json.load(r)
            self.assertTrue(result["active"])
            self.assertEqual(result["age_seconds"], 5)
        snapshot["updated"] = 980
        atomic_json(home() / "status.json", snapshot)
        with patch("ugso_usbhub.web.time.time", return_value=1000):
            with self.request("/api/status") as r:
                self.assertFalse(json.load(r)["active"])
        snapshot.update(updated=999, stopped=True)
        atomic_json(home() / "status.json", snapshot)
        with patch("ugso_usbhub.web.time.time", return_value=1000):
            with self.request("/api/status") as r:
                self.assertFalse(json.load(r)["active"])

    def test_icon_http_upload(self):
        self.login()
        import base64
        before = copy.deepcopy(load_config())
        with self.request("/api/icons/upload", {"name": "test.png", "data": base64.b64encode(png()).decode()}) as r:
            ident = json.load(r)["id"]
        with self.request("/icons/" + ident + ".png") as r:
            self.assertEqual(r.headers["Content-Type"], "image/png")
            self.assertTrue(r.read().startswith(b"\x89PNG"))
        upload = {"name": "subfolder.png", "data": base64.b64encode(png()).decode(), "collection": "Meine Icons"}
        for _ in range(2):
            with self.request("/api/icons/upload", upload) as r:
                self.assertEqual(json.load(r)["id"], ident)
        self.assertEqual(len([i for i in icons.library() if i["collection"] == "Meine Icons"]), 1)
        self.assertEqual(load_config(), before)
        upload["collection"] = {"invalid": True}
        with self.assertRaises(urllib.error.HTTPError) as err:
            self.request("/api/icons/upload", upload)
        self.assertEqual(err.exception.code, 400)

    def test_logout_invalidates_session(self):
        self.login()
        with self.request("/api/logout", {}):
            pass
        with self.assertRaises(urllib.error.HTTPError):
            self.request("/api/status")


class CoreTests(TemporaryHome):
    def test_streamdeck_native_image_and_text_rendering(self):
        hardware = Hardware(lambda *x: None)
        deck = Mock()
        deck.key_count.return_value = 15
        deck.is_visual.return_value = True
        deck.key_image_format.return_value = {"size": (72, 72), "format": "JPEG", "rotation": 0, "flip": (False, False)}
        hardware.decks["demo"] = deck
        ident = icons.add(png(), "test.png")
        hardware.display("demo", 0, ident, "Volume +", 40)
        deck.set_brightness.assert_called_once_with(40)
        args = deck.set_key_image.call_args.args
        self.assertEqual(args[0], 0)
        with Image.open(io.BytesIO(args[1])) as rendered:
            self.assertEqual(rendered.size, (72, 72))
        deck.set_key_image.reset_mock()
        hardware.display("demo", 99, ident, "invalid")
        deck.set_key_image.assert_not_called()

    def test_disabled_device_and_hold(self):
        from ugso_usbhub.core import Core
        c = Core()
        try:
            c.event("demo", "KEY_PLAYPAUSE", "press", 1)
            self.assertEqual(len(c.events), 0)
            c.config["devices"]["demo"] = {"enabled": True}
            c.event("demo", "KEY_PLAYPAUSE", "press", 1)
            self.assertIn(("demo", "KEY_PLAYPAUSE"), c.pressed)
            c.event("demo", "KEY_PLAYPAUSE", "release", 0)
            self.assertFalse(c.pressed)
            self.assertEqual(len(c.events), 2)
        finally:
            c.brokers.close()

    def test_only_selected_receive_broker_can_change_display(self):
        from ugso_usbhub.core import Core
        c = Core()
        c.hardware = Mock()
        c.config["devices"]["deck"] = {"receive_broker": "broker2"}
        try:
            c.display_message("broker1", "ugso/usbhub/1/display/deck/set", '{"text":"wrong"}')
            c.hardware.display.assert_not_called()
            c.display_message("broker2", "ugso/usbhub/2/display/deck/set", '{"text":"right"}')
            c.hardware.display.assert_called_once_with("deck", 0, "", "right", None)
        finally:
            c.brokers.close()

    def test_separate_processes_and_core_restart_persistence(self):
        c = load_config()
        c["password_hash"] = password_hash("test-password-123")
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        c["web"] = {"host": "127.0.0.1", "port": s.getsockname()[1]}
        s.close()
        c["devices"]["persist"] = {"name": "Saved device", "targets": ["broker3"]}
        save_config(c)
        commands = [sys.executable, "-m", "ugso_usbhub.cli"]
        core = subprocess.Popen(commands + ["daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        web = subprocess.Popen(commands + ["serve-web"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            def online():
                try:
                    return urllib.request.urlopen(f"http://127.0.0.1:{c['web']['port']}/", timeout=.3).status == 200
                except OSError:
                    return False
            wait_for(online)
            wait_for(lambda: (home() / "status.json").exists())
            timestamp = json.loads((home() / "status.json").read_text())["updated"]
            web.terminate()
            web.wait(timeout=4)
            wait_for(lambda: json.loads((home() / "status.json").read_text())["updated"] > timestamp)
            self.assertIsNone(core.poll())
            with socket.socket() as probe:
                self.assertNotEqual(probe.connect_ex(("127.0.0.1", c["web"]["port"])), 0)
            core.terminate()
            core.wait(timeout=4)
            core = subprocess.Popen(commands + ["daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            wait_for(lambda: json.loads((home() / "status.json").read_text())["started"] > timestamp)
            self.assertEqual(load_config()["devices"]["persist"]["name"], "Saved device")
        finally:
            for process in (web, core):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
