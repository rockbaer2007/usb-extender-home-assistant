import copy
import time
from unittest.mock import patch
from tests import test_hub as fixtures
from tests.broker import Broker, wait_for
from ugso_usbhub.core import Core
from ugso_usbhub.gestures import Buttons
from ugso_usbhub.keymap import EXTRA_MODES
from ugso_usbhub.mqtt import Brokers
from ugso_usbhub.storage import defaults, save_config, load_config


class GestureTests(fixtures.TemporaryHome):
    def setUp(self):
        super().setUp()
        self.engine = Buttons()
        self.key = ("keyboard", "KEY_F1")
        self.row = {"double_ms": 300, "hold_ms": 700}

    def feed(self, kind, now):
        return self.engine.feed(self.key, kind, now, self.row)

    def test_single_click_waits_for_double_click_window(self):
        self.assertEqual(self.feed("press", 0), [])
        self.assertEqual(self.feed("release", .1), [])
        self.assertEqual(self.engine.tick(.399), [])
        self.assertEqual(self.engine.tick(.401), [(self.key, "button_click")])
        self.assertEqual(self.engine.tick(2), [])

    def test_double_click_has_no_single_click(self):
        self.feed("press", 0)
        self.feed("release", .05)
        self.feed("press", .2)
        self.assertEqual(self.feed("release", .25), [(self.key, "button_double_click")])
        self.assertEqual(self.engine.tick(2), [])

    def test_hold_once_no_click_on_release_or_native_repeat(self):
        self.feed("press", 0)
        self.assertEqual(self.feed("repeat", .71), [(self.key, "button_hold")])
        self.assertEqual(self.engine.tick(2), [])
        self.assertEqual(self.feed("release", 2.1), [])
        self.assertEqual(self.engine.tick(4), [])

    def test_release_after_hold_threshold_without_intermediate_tick(self):
        self.feed("press", 0)
        self.assertEqual(self.feed("release", .8), [(self.key, "button_hold")])
        self.assertEqual(self.engine.tick(2), [])

    def test_late_second_click_becomes_two_singles(self):
        self.feed("press", 0)
        self.feed("release", .05)
        self.assertEqual(self.feed("press", .5), [(self.key, "button_click")])
        self.feed("release", .55)
        self.assertEqual(self.engine.tick(.9), [(self.key, "button_click")])

    def test_second_press_held_does_not_emit_first_single(self):
        self.feed("press", 0)
        self.feed("release", .05)
        self.feed("press", .2)
        self.assertEqual(self.engine.tick(.91), [(self.key, "button_hold")])
        self.assertEqual(self.feed("release", 1), [])
        self.assertEqual(self.engine.tick(2), [])

    def test_cancel_pending_and_other_device_independent(self):
        self.feed("press", 0)
        self.feed("release", .05)
        other = ("other", "KEY_F1")
        self.engine.feed(other, "press", .1, self.row)
        self.engine.feed(other, "release", .15, self.row)
        self.engine.cancel(device="keyboard")
        self.assertEqual(self.engine.tick(.5), [(other, "button_click")])
        self.assertEqual(self.feed("release", 1), [])
        self.assertFalse(self.engine.keys)

    def test_custom_times(self):
        self.row.update(double_ms=600, hold_ms=1200)
        self.feed("press", 0)
        self.assertEqual(self.engine.tick(.8), [])
        self.assertEqual(self.engine.tick(1.21), [(self.key, "button_hold")])


class ButtonProtocolTests(fixtures.TemporaryHome):
    def setUp(self):
        super().setUp()
        self.servers = [Broker(), Broker()]
        self.config = defaults()
        self.config["devices"]["keyboard"] = {"enabled": True, "name": "Trust Keyboard", "targets": ["broker1", "broker2"]}
        self.row = {"id": "f1", "device": "keyboard", "control": "KEY_F1", "name": "F1", "enabled": True,
                    "topic_version": 2, "device_topic": "trust-keyboard", "switch_mode": "toggle",
                    "press": True, "release": True, "switch": True, "press_plus": True, "release_plus": True,
                    **{mode: True for mode in EXTRA_MODES}}
        self.config["keys"] = [self.row]
        for b, server in zip(self.config["brokers"], self.servers):
            b.update(enabled=True, host="127.0.0.1", port=server.port)
        save_config(self.config)
        self.pool = Brokers(self.config, lambda *args: None)
        wait_for(lambda: all(any(t == "trust-keyboard-key-f1/switch" for t, _, _ in s.messages) for s in self.servers))
        self.make_core()
        for server in self.servers:
            server.messages.clear()

    def make_core(self):
        with patch("ugso_usbhub.core.Brokers", return_value=self.pool):
            self.core = Core()

    def tearDown(self):
        self.core.hardware.close()
        self.pool.close()
        for s in self.servers:
            s.close()
        super().tearDown()

    def event(self, gesture, now):
        with patch("ugso_usbhub.core.time.monotonic", return_value=now):
            self.core.event("keyboard", "KEY_F1", gesture, int(gesture != "release"))

    def values(self, mode, server=0):
        return [p.decode() for t, p, _ in self.servers[server].messages if t == "trust-keyboard-key-f1/" + mode]

    def test_switch_toggles_only_on_press_and_state_tracks_release(self):
        self.event("press", 1)
        self.event("release", 1.05)
        wait_for(lambda: self.values("state") == ["ON", "OFF"])
        self.assertEqual(self.values("switch"), ["ON"])
        self.event("press", 1.2)
        self.event("repeat", 1.21)
        self.event("release", 1.25)
        wait_for(lambda: all(self.values("switch", i) == ["ON", "OFF"] for i in (0, 1)))
        self.assertEqual(self.values("state"), ["ON", "OFF", "ON", "OFF"])

    def test_single_click_all_channels_plain_and_plus_reset(self):
        self.event("press", 1)
        self.event("release", 1.05)
        self.core.tick(1.36)
        self.pool.flush_resets(time.monotonic() + 1)
        wait_for(lambda: all(self.values("button-plus", i) == ["click", ""] for i in (0, 1)))
        for i in (0, 1):
            self.assertEqual(self.values("button", i), ["click"])
            self.assertEqual(self.values("click", i), ["click"])
            self.assertFalse(self.values("double-click", i))
            self.assertFalse(self.values("hold", i))
            self.assertTrue(all(not retained for t, _, retained in self.servers[i].messages if t.startswith("trust-keyboard-")))

    def test_double_and_hold_do_not_send_single_click(self):
        self.event("press", 1)
        self.event("release", 1.05)
        self.event("press", 1.2)
        self.event("release", 1.25)
        self.core.tick(2)
        wait_for(lambda: self.values("button") == ["double_click"])
        self.event("press", 3)
        self.core.tick(3.71)
        self.event("release", 4)
        self.core.tick(5)
        wait_for(lambda: self.values("button") == ["double_click", "hold"])
        self.assertEqual(self.values("double-click"), ["double_click"])
        self.assertEqual(self.values("hold"), ["hold"])
        self.assertFalse(self.values("click"))

    def test_restart_preserves_toggle_value_and_other_settings(self):
        previous = copy.deepcopy(load_config())
        self.event("press", 1)
        self.event("release", 1.05)
        wait_for(lambda: self.values("switch") == ["ON"])
        self.pool.close()
        for server in self.servers:
            server.messages.clear()
        self.pool = Brokers(self.config, lambda *args: None)
        wait_for(lambda: all(self.values("switch", i) == ["ON"] for i in (0, 1)))
        self.make_core()
        self.event("press", 2)
        self.event("release", 2.05)
        wait_for(lambda: self.values("switch") == ["ON", "OFF"])
        self.assertEqual(load_config(), previous)

    def test_learning_and_device_loss_cancel_button_and_preserve_switch(self):
        self.event("press", 1)
        self.event("release", 1.05)
        self.core.release_all("keyboard")
        self.core.tick(2)
        self.core.learning = {"id": "lease", "device": "keyboard", "expires": time.time() + 10}
        self.event("press", 3)
        self.event("release", 3.05)
        self.core.tick(4)
        wait_for(lambda: self.values("switch") == ["ON"])
        self.assertTrue(self.core.toggle_states["f1"])
        self.assertFalse(self.values("button"))

    def test_all_discovery_components_use_one_device(self):
        self.config["brokers"][0]["discovery"] = True
        self.pool.discovery(self.config["brokers"][0])
        import json
        wait_for(lambda: len([t for t, p, _ in self.servers[0].messages if t.startswith("homeassistant/") and p]) == 15)
        configs = [json.loads(p) for t, p, _ in self.servers[0].messages if t.startswith("homeassistant/") and p]
        self.assertEqual(len({tuple(c["device"]["identifiers"]) for c in configs}), 1)
        self.assertEqual({c["device"]["name"] for c in configs}, {"Trust Keyboard"})
        self.assertEqual(len([c for c in configs if "state_topic" in c]), 2)
        triggers = [c for c in configs if "automation_type" in c]
        self.assertEqual(len({(c["type"], c["subtype"]) for c in triggers}), len(triggers))
