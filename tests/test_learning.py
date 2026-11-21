import copy
import json
import time
import unittest
import urllib.error
import urllib.request
import http.cookiejar
import threading
from unittest.mock import patch
from tests import test_hub as fixtures
from tests.broker import Broker, wait_for
from ugso_usbhub.core import Core
from ugso_usbhub.keymap import all_bindings, device_topic_names, topic_slug
from ugso_usbhub.learning import command, current
from ugso_usbhub.mqtt import Brokers
from ugso_usbhub.storage import defaults, validate, save_config, load_config, merge_public, public_config
from ugso_usbhub.storage import password_hash
from ugso_usbhub.web import Server


def row(control="KEY_VOLUMEUP"):
    return {"id": "volume", "device": "keyboard", "control": control, "name": "Lauter",
            "enabled": True, "press": True, "release": True, "switch": True, "switch_mode": "momentary",
            "press_plus": True, "release_plus": True, "repeat": True,
            "repeat_delay": 500, "repeat_interval": 150, "targets": None}


class LearnedConfigTests(fixtures.TemporaryHome):
    def test_readable_names_with_umlauts_collisions_and_frozen_namespace(self):
        config = defaults()
        config["devices"] = {"a": {"name": "Büro-Tastatur"}, "b": {"name": "Büro Tastatur"}}
        self.assertEqual(device_topic_names(config), {"a": "buero-tastatur", "b": "buero-tastatur-2"})
        self.assertEqual(topic_slug("KEY_VOLUMEUP"), "key-volumeup")
        config["keys"] = [{**row(), "device": "a", "device_topic": "buero-tastatur", "topic_version": 2}]
        config["devices"]["a"]["name"] = "Neuer Name"
        self.assertEqual(device_topic_names(config)["a"], "buero-tastatur")
        self.assertTrue(all(b["topic"].startswith("buero-tastatur-key-volumeup/") for b in all_bindings(config)))

    def test_existing_settings_and_credentials_survive_save_restart(self):
        config = load_config()
        config["brokers"][1].update(password="preserved-secret", discovery=False)
        config["bindings"] = [{"id": "old", "device": "keyboard", "control": "KEY_TAB", "gesture": "press", "topic": "keep/me"}]
        config["keys"] = [row()]
        save_config(config)
        result = load_config()
        self.assertEqual(result, config)
        self.assertEqual(merge_public(public_config(result), result), config)
        self.assertEqual(all_bindings(result)[0], config["bindings"][0])

    def test_duplicate_keys_bad_topics_and_unbounded_repeat_rejected(self):
        config = defaults()
        for changes in ({"repeat_interval": 0}, {"repeat_delay": 99999}, {"press_topic": "bad/#"}, {"control": "KEY_A"}):
            bad = copy.deepcopy(config)
            bad["keys"] = [{**row(), **changes}]
            with self.assertRaises(ValueError):
                validate(bad)
        config["keys"] = [row(), {**row(), "id": "second"}]
        with self.assertRaises(ValueError):
            validate(config)

    def test_learning_lease_requires_enabled_device_and_session(self):
        config = defaults()
        with self.assertRaises(ValueError):
            command({"action": "start", "device": "keyboard"}, config)
        config["devices"]["keyboard"] = {"enabled": True}
        with patch("ugso_usbhub.learning.time.time", return_value=100):
            lease = command({"action": "start", "device": "keyboard"}, config)
            self.assertEqual(current()["device"], "keyboard")
            with self.assertRaises(ValueError):
                command({"action": "stop", "id": "foreign"}, config)
            with self.assertRaises(ValueError):
                command({"action": "start", "device": "keyboard"}, config)
        with patch("ugso_usbhub.learning.time.time", return_value=116):
            self.assertFalse(current())
            command({"action": "stop", "id": lease["id"]}, config)
            self.assertFalse(current())


class LearnedProtocolTests(fixtures.TemporaryHome):
    def setUp(self):
        super().setUp()
        self.servers = [Broker(), Broker()]
        self.config = defaults()
        self.config["devices"]["keyboard"] = {"enabled": True, "targets": ["broker1", "broker2"]}
        self.config["keys"] = [row()]
        for broker, server in zip(self.config["brokers"], self.servers):
            broker.update(enabled=True, host="127.0.0.1", port=server.port, discovery=True)
        validate(self.config)
        self.pool = Brokers(self.config, lambda *args: None)
        wait_for(lambda: all(self.pool.states.get(b["id"]) == "online" for b in self.config["brokers"][:2]))

    def tearDown(self):
        self.pool.close()
        for server in self.servers:
            server.close()
        super().tearDown()

    def messages(self, server):
        return [(t.rsplit("/", 1)[-1], p.decode(), retained) for t, p, retained in server.messages if "/keyboard/" in t]

    def test_press_release_plus_and_switch_on_both_real_connections(self):
        self.assertEqual(self.pool.send("keyboard", "KEY_VOLUMEUP", "press"), 4)
        self.pool.flush_resets(time.monotonic() + 1)
        self.assertEqual(self.pool.send("keyboard", "KEY_VOLUMEUP", "release"), 4)
        self.pool.flush_resets(time.monotonic() + 1)
        expected = [("press", "press", False), ("switch", "ON", False), ("press", "", False),
                    ("release", "release", False), ("switch", "OFF", False), ("release", "", False)]
        wait_for(lambda: all(len(self.messages(s)) == 6 for s in self.servers))
        for server in self.servers:
            self.assertEqual(self.messages(server), expected)
        self.assertFalse(self.pool.pending_resets)

    def test_fast_repeated_presses_have_empty_separator(self):
        self.pool.send("keyboard", "KEY_VOLUMEUP", "press")
        self.pool.send_report("keyboard", "KEY_VOLUMEUP", "press", repeat_key=True)
        self.pool.flush_resets(time.monotonic() + 1)
        wait_for(lambda: len(self.messages(self.servers[0])) >= 5)
        presses = [p for t, p, _ in self.messages(self.servers[0]) if t == "press"]
        self.assertEqual(presses, ["press", "", "press", ""])
        self.assertEqual([p for t, p, _ in self.messages(self.servers[0]) if t == "switch"], ["ON"])

    def test_disabled_channels_row_and_per_key_routes(self):
        key = self.config["keys"][0]
        key.update(press=False, release=False, targets=["broker2"])
        self.assertEqual(self.pool.send("keyboard", "KEY_VOLUMEUP", "press"), 1)
        wait_for(lambda: len(self.messages(self.servers[1])) == 1)
        self.assertFalse(self.messages(self.servers[0]))
        key["enabled"] = False
        self.assertEqual(self.pool.send("keyboard", "KEY_VOLUMEUP", "release"), 0)

    def test_ha_discovery_switch_and_action_payload_filter(self):
        wait_for(lambda: any(t.startswith("homeassistant/binary_sensor/") for t, _, _ in self.servers[0].messages))
        configs = [json.loads(p) for t, p, _ in self.servers[0].messages if t.startswith("homeassistant/") and p]
        sensor = next(c for c in configs if "state_topic" in c)
        self.assertEqual((sensor["payload_on"], sensor["payload_off"]), ("ON", "OFF"))
        self.assertTrue(sensor["state_topic"].endswith("/key_volumeup/switch"))
        self.assertEqual({c["payload"] for c in configs if "automation_type" in c}, {"press", "release"})

    def test_five_named_channels_and_plus_reset_on_both_brokers(self):
        self.config["keys"][0].update(topic_version=2, device_topic="trust-keyboard")
        self.assertEqual(self.pool.send("keyboard", "KEY_VOLUMEUP", "press"), 6)
        self.pool.flush_resets(time.monotonic() + 1)
        self.assertEqual(self.pool.send("keyboard", "KEY_VOLUMEUP", "release"), 6)
        self.pool.flush_resets(time.monotonic() + 1)
        expected = {"press": [b"press"], "press-plus": [b"press", b""],
                    "release": [b"release"], "release-plus": [b"release", b""],
                    "switch": [b"ON", b"OFF"]}
        wait_for(lambda: all(len([m for m in s.messages if m[0].startswith("trust-keyboard-")]) == 8 for s in self.servers))
        for server in self.servers:
            for mode, payloads in expected.items():
                topic = "trust-keyboard-key-volumeup/" + mode
                messages = [m for m in server.messages if m[0] == topic]
                self.assertEqual([m[1] for m in messages], payloads)
                self.assertTrue(all(not m[2] for m in messages))

    def test_discovery_all_keys_and_plus_channels_share_named_device(self):
        # "online" precedes queued initial discovery. Drain those three configs
        # before changing the device name and measuring the next publication.
        wait_for(lambda: len([m for m in self.servers[0].messages if m[0].startswith("homeassistant/") and m[1]]) >= 3)
        self.config["devices"]["keyboard"]["name"] = "Trust Keyboard"
        self.config["keys"][0].update(topic_version=2, device_topic="trust-keyboard")
        self.config["keys"].append({**self.config["keys"][0], "id": "tab", "control": "KEY_TAB", "name": "Tab", "repeat": False})
        before = len(self.servers[0].messages)
        self.pool.discovery(self.config["brokers"][0])
        wait_for(lambda: len([m for m in self.servers[0].messages[before:] if m[0].startswith("homeassistant/") and m[1]]) >= 10)
        configs = [json.loads(p) for t, p, _ in self.servers[0].messages[before:] if t.startswith("homeassistant/") and p]
        self.assertEqual({c["device"]["name"] for c in configs}, {"Trust Keyboard"})
        self.assertEqual(len({tuple(c["device"]["identifiers"]) for c in configs}), 1)
        triggers = [c for c in configs if "automation_type" in c]
        self.assertEqual(len(triggers), 8)
        self.assertEqual(len({(c["type"], c["subtype"]) for c in triggers}), 8)
        self.assertTrue(all(c["topic"].startswith("trust-keyboard-key-") for c in triggers))

    def test_volume_repeat_stops_on_release_and_learning_suppresses(self):
        save_config(self.config)
        core = Core.__new__(Core)
        # Real core state initialization, but use the already connected test brokers.
        with patch("ugso_usbhub.core.Brokers", return_value=self.pool):
            core = Core()
        try:
            with patch("ugso_usbhub.core.time.monotonic", return_value=10):
                core.event("keyboard", "KEY_VOLUMEUP", "press", 1)
            core.tick(10.49)
            self.assertEqual(core.repeat_due[("keyboard", "KEY_VOLUMEUP")], 10.5)
            core.tick(10.5)
            self.assertAlmostEqual(core.repeat_due[("keyboard", "KEY_VOLUMEUP")], 10.65)
            core.event("keyboard", "KEY_VOLUMEUP", "release", 0)
            core.tick(12)
            self.assertFalse(core.repeat_due)
            wait_for(lambda: any(p == "OFF" for _, p, _ in self.messages(self.servers[0])))
            baseline = self.pool.send_report
            with patch.object(self.pool, "send_report", wraps=baseline) as send:
                core.learning = {"id": "test-lease", "device": "keyboard", "expires": time.time() + 10}
                core.event("keyboard", "KEY_VOLUMEUP", "press", 1)
                self.assertEqual(core.events[0]["learning_id"], "test-lease")
                self.assertEqual(core.events[0]["delivery"]["reason"], "learning")
                self.assertFalse(core.repeat_due)
                core.learning = {}
                core.event("keyboard", "KEY_VOLUMEUP", "release", 0)
                send.assert_not_called()
                core.event("keyboard", "KEY_VOLUMEUP", "press", 1)
                send.assert_called_once()
            core.release_all()
            with patch("ugso_usbhub.core.time.monotonic", return_value=20):
                core.event("keyboard", "KEY_VOLUMEUP", "press", 1)
            core.tick(50.1)
            self.assertFalse(core.pressed)
            self.assertFalse(core.repeat_due)
        finally:
            core.hardware.close()


class LearningApiTests(fixtures.TemporaryHome):
    def setUp(self):
        super().setUp()
        config = load_config()
        config["password_hash"] = password_hash("test-password-123")
        save_config(config)
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

    request = fixtures.WebTests.request
    login = fixtures.WebTests.login
    def test_learning_api_does_not_change_saved_settings(self):
        self.login()
        config = load_config()
        config["devices"]["keyboard"] = {"enabled": True}
        save_config(config)
        with self.request("/api/learning", {"action": "start", "device": "keyboard"}) as response:
            lease = json.load(response)
        with self.request("/api/learning", {"action": "heartbeat", "id": lease["id"]}) as response:
            self.assertEqual(json.load(response)["id"], lease["id"])
        with self.request("/api/learning", {"action": "stop", "id": lease["id"]}):
            pass
        self.assertFalse(current())
        self.assertEqual(load_config(), config)


if __name__ == "__main__":
    unittest.main()
