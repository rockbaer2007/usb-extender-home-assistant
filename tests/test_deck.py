"""Artwork persistence, real native key encoding and authenticated previews."""
import base64
import copy
import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest.mock import Mock, patch
from PIL import Image
from ugso_usbhub import icons
from ugso_usbhub.deck import key_image
from ugso_usbhub.hardware import Hardware
from ugso_usbhub.storage import load_config, save_config, validate, public_config, merge_public
from ugso_usbhub.keymap import ensure_deck_keys, key_bindings
from tests import test_hub as hub


class DeckTests(unittest.TestCase):
    def test_core_routes_key_edges_and_disconnect_to_artwork(self):
        from ugso_usbhub.core import Core
        core = Core()
        try:
            core.hardware = Mock()
            core.config["devices"]["deck"] = {"enabled": True}
            core.event("deck", "key:0", "press", 1)
            core.hardware.set_pressed.assert_called_with("deck", 0, True)
            core.event("deck", "key:0", "release", 0)
            core.hardware.set_pressed.assert_called_with("deck", 0, False)
            core.event("deck", "key:0", "press", 1)
            core.event("deck", "_mobile_disconnect", "release", 0)
            core.hardware.set_pressed.assert_called_with("deck", 0, False)
        finally:
            core.hardware.close()
            core.brokers.close()

    def test_pressed_artwork_persists_and_restores_feedback_on_release(self):
        out = io.BytesIO()
        Image.new("RGB", (20, 20), "red").save(out, format="PNG")
        icon = icons.add(out.getvalue(), "pressed.png")
        style = {"background": "#0000ff", "text_color": "#ffffff",
                 "pressed_icon": icon, "pressed_background": "#00ff00", "pressed_text_color": "#ffff00"}
        config = load_config()
        config["devices"]["deck"] = {"enabled": True, "deck_keys": {"0": style}}
        save_config(config)
        hardware = Hardware(lambda *args: None)
        hardware.config = load_config()
        deck = Mock()
        deck.key_count.return_value = 1
        deck.is_visual.return_value = True
        deck.key_image_format.return_value = {"size": (72, 72), "format": "BMP", "rotation": 0, "flip": (False, False)}
        hardware.decks["deck"] = deck
        hardware.display("deck", 0, "", "Feedback ON")
        normal = deck.set_key_image.call_args.args[1]
        hardware.set_pressed("deck", 0, True)
        pressed = deck.set_key_image.call_args.args[1]
        with Image.open(io.BytesIO(pressed)) as image:
            self.assertEqual(image.convert("RGB").getpixel((0, 0)), (0, 255, 0))
            self.assertEqual(image.convert("RGB").getpixel((36, 20)), (255, 0, 0))
        self.assertNotEqual(normal, pressed)
        count = deck.set_key_image.call_count
        hardware.set_pressed("deck", 0, True)
        self.assertEqual(deck.set_key_image.call_count, count)
        hardware.set_pressed("deck", 0, False)
        self.assertEqual(deck.set_key_image.call_args.args[1], normal)
        base = key_image((72, 72), {"background": "#123456"})
        self.assertEqual(base.tobytes(), key_image((72, 72), {"background": "#123456"}, pressed=True).tobytes())
        self.assertEqual(key_image((72,72), {"pressed_background":"#00ff00"}, pressed=True).getpixel((0,0)), (0,255,0))
        text_style = {"pressed_text_color":"#ffff00"}
        self.assertNotEqual(key_image((72,72), text_style, label="Test").tobytes(),
                            key_image((72,72), text_style, label="Test", pressed=True).tobytes())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"UGSO_USB_HOME": self.temp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_save_restart_credentials_and_existing_binding(self):
        c = load_config()
        c["brokers"][0]["password"] = "preserved-secret"
        c["bindings"] = [{"id": "old", "device": "deck", "control": "key:0", "gesture": "press", "topic": "original/topic"}]
        save_config(c)
        incoming = public_config(c)
        incoming["devices"]["deck"] = {"targets": ["broker2"], "deck_keys": {"0": {"background": "#123456", "text": "Licht", "text_color": "#ffffff"}}}
        save_config(merge_public(incoming, load_config()))
        restored = load_config()
        self.assertEqual(restored["devices"]["deck"]["deck_keys"]["0"]["text"], "Licht")
        self.assertEqual(restored["brokers"][0]["password"], "preserved-secret")
        self.assertEqual(restored["bindings"], c["bindings"])

    def test_background_composition_and_native_hardware_output(self):
        out = io.BytesIO()
        Image.new("RGBA", (72, 72), (255, 0, 0, 100)).save(out, format="PNG")
        icon = icons.add(out.getvalue(), "red.png")
        style = {"background": "#0000ff", "icon": icon, "text": "Hello"}
        expected = key_image((72, 72), style, icon, "Hello")
        self.assertNotEqual(expected.getpixel((30, 30)), (255, 0, 0))
        deck = Mock()
        deck.key_count.return_value = 6
        deck.is_visual.return_value = True
        deck.key_image_format.return_value = {"size": (72, 72), "format": "BMP", "rotation": 0, "flip": (False, False)}
        hardware = Hardware(lambda *a: None)
        hardware.decks["deck"] = deck
        hardware.config = {"devices": {"deck": {"deck_keys": {"0": style}}}, "bindings": []}
        hardware.refresh_decks()
        self.assertEqual(deck.set_key_image.call_count, 6)  # Clear formerly configured keys too.
        raw = deck.set_key_image.call_args_list[0].args[1]
        with Image.open(io.BytesIO(raw)) as actual:
            self.assertEqual(actual.convert("RGB").tobytes(), expected.tobytes())

    def test_invalid_artwork_rejected(self):
        for style in ({"pressed_background": "red"}, {"pressed_text_color": "bad"},
                      {"pressed_icon": "../icon"}, {"background": "url(http://host)"}, {"icon": "../../secret"},
                      {"text_position": "invalid"}, {"font_size": 500}, {"text": "x"*81}):
            c = load_config()
            c["devices"]["deck"] = {"deck_keys": {"0": style}}
            with self.assertRaises(ValueError):
                validate(c)

    def test_automatic_deck_channels_preserve_custom_rows_and_names(self):
        c=load_config()
        c['devices']={'tablet':{'name':'Stream Deck Mobile','enabled':True},'other':{'name':'Stream Deck Mobile','enabled':True},'off':{'enabled':False}}
        devices=[{'id':ident,'kind':'streamdeck','deck':{'keys':2}} for ident in c['devices']]
        self.assertEqual(ensure_deck_keys(c,devices),4)
        validate(c)
        self.assertEqual({k['device_topic'] for k in c['keys']},{'stream-deck-mobile','stream-deck-mobile-2'})
        bindings=[b for b in key_bindings(c) if b['device']=='tablet' and b['control']=='key:0']
        self.assertEqual({b['topic'].rsplit('/',1)[1] for b in bindings},{'press','release','press-plus','release-plus','switch','state','button','button-plus','click','double-click','hold'})
        row=c['keys'][0];row.update(press_topic='my/existing/press',hold=False)
        before=copy.deepcopy(c)
        c['devices']['tablet']['name']='Renamed'
        self.assertEqual(ensure_deck_keys(c,devices),0)
        self.assertEqual(c['keys'],before['keys'])
        save_config(c)
        self.assertEqual(load_config()['keys'],c['keys'])

    def test_top_bottom_text_reserves_space_only_for_foreground_icon(self):
        out = io.BytesIO()
        Image.new("RGB", (72, 72), "red").save(out, format="PNG")
        icon = icons.add(out.getvalue(), "red.png")
        out = io.BytesIO()
        Image.new("RGB", (72, 72), "blue").save(out, format="PNG")
        background = icons.add(out.getvalue(), "blue.png")
        for size in (32, 72, 144):
            for fit in ("contain", "cover"):
                for position in ("top", "bottom", "center"):
                    with self.subTest(size=size, fit=fit, position=position):
                        style = {"background_image":background, "text_position":position, "fit":fit}
                        image = key_image((size,size), style, icon, "Test")
                        red_rows = [y for y in range(size) if any(image.getpixel((x,y)) == (255,0,0) for x in range(size))]
                        self.assertTrue(red_rows)
                        if position == "top":
                            self.assertGreater(min(red_rows), size//8)
                            self.assertEqual(image.getpixel((0,0)), (0,0,255))
                        elif position == "bottom":
                            self.assertLess(max(red_rows), size-size//8)
                            self.assertEqual(image.getpixel((0,size-1)), (0,0,255))
                        else:
                            self.assertEqual((min(red_rows),max(red_rows)), (0,size-1))
                        no_text = key_image((size,size), style, icon, "")
                        self.assertEqual(no_text.getpixel((0,0)), (255,0,0))
                        self.assertEqual(no_text.getpixel((size-1,size-1)), (255,0,0))

    def test_mqtt_feedback_keeps_designed_base_icon(self):
        from ugso_usbhub.core import Core
        core = Core()
        try:
            core.hardware = Mock()
            core.config["devices"]["deck"] = {"receive_broker": "broker1", "deck_keys": {"0": {"icon": "a"*32}}}
            core.config["bindings"] = [{"id": "state", "device": "deck", "control": "key:0", "state_topic": "light/state", "on_icon": "b"*32}]
            core.display_message("broker1", "light/state", "ON")
            core.hardware.display_logical.assert_called_with("deck", 0, "b"*32, "ON")
            core.display_message("broker1", "light/state", "OFF")
            core.hardware.display_logical.assert_called_with("deck", 0, "a"*32, "OFF")
            core.hardware.reset_mock()
            core.display_message("broker2", "light/state", "ON")
            core.hardware.display_logical.assert_not_called()
        finally:
            core.brokers.close()

    def test_model_metadata_without_new_hardware_access(self):
        hardware = Hardware(lambda *a: None)
        deck = Mock()
        deck.deck_type.return_value = "Stream Deck Mini"
        deck.key_layout.return_value = (2, 3)
        deck.key_count.return_value = 6
        deck.is_visual.return_value = True
        deck.key_image_format.return_value = {"size": (80, 80)}
        hardware.decks["deck"] = deck
        with patch("ugso_usbhub.hardware.inventory", return_value=[{"id": "deck", "kind": "streamdeck", "inputs": []}]), patch.object(hardware, "_scan_decks"):
            hardware.scan({"devices": {"deck": {"enabled": True}}})
        self.assertEqual(hardware.inventory[0]["deck"]["layout"], [2, 3])
        self.assertEqual(hardware.inventory[0]["deck"]["keys"], 6)


class PreviewTests(hub.WebTests):
    def test_save_enabled_deck_adds_all_channels_and_keeps_secrets(self):
        import time
        from ugso_usbhub.storage import atomic_json, status_path
        c=load_config();c['brokers'][0]['password']='keep-secret';save_config(c)
        self.login()
        incoming=public_config(c)
        incoming['devices']['tablet']={'enabled':True,'name':'Stream Deck Mobile'}
        atomic_json(status_path(),{'updated':time.time(),'devices':[{'id':'tablet','kind':'streamdeck','deck':{'keys':15}}]})
        with self.request('/api/config',incoming):pass
        saved=load_config()
        self.assertEqual(len(saved['keys']),15)
        self.assertEqual(saved['keys'][0]['press_topic'],'stream-deck-mobile-key-0/press')
        self.assertEqual(saved['brokers'][0]['password'],'keep-secret')
        with self.request('/api/config',public_config(saved)):pass
        self.assertEqual(load_config()['keys'],saved['keys'])

    def test_authenticated_preview_is_read_only_and_matches_renderer(self):
        before = copy.deepcopy(load_config())
        request = {"style": {"background": "#123456", "text": "Licht"}, "size": [72, 72]}
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/deck/preview", request)
        self.assertEqual(error.exception.code, 401)
        self.login()
        with self.request("/api/deck/preview", request) as r:
            image = Image.open(io.BytesIO(base64.b64decode(json.load(r)["image"])))
            self.assertEqual(image.tobytes(), key_image((72, 72), request["style"], "", "Licht").tobytes())
        self.assertEqual(load_config(), before)
        request["size"] = [10000, 10000]
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/deck/preview", request)
        self.assertEqual(error.exception.code, 400)

    def test_save_and_delete_middle_page_keep_other_topics_and_page_one(self):
        import time
        from ugso_usbhub.storage import atomic_json,status_path,home
        config=load_config();config['brokers'][0]['password']='keep-secret';save_config(config)
        self.login()
        incoming=public_config(config)
        incoming['devices']['tablet']={'enabled':True,'name':'Tablet','deck_page_count':3,'deck_keys':{'0':{'text':'First'},'128':{'text':'Second'},'256':{'text':'Third','show_page':True}}}
        atomic_json(status_path(),{'updated':time.time(),'devices':[{'id':'tablet','kind':'streamdeck','deck':{'keys':6}}]})
        with self.request('/api/config',incoming):pass
        saved=load_config();third=next(k for k in saved['keys'] if k['control']=='key:256')
        incoming=public_config(saved);incoming['devices']['tablet']['deck_page_count']=2;incoming['devices']['tablet']['deck_page_order']=[0,2]
        del incoming['devices']['tablet']['deck_keys']['128']
        incoming['keys']=[k for k in incoming['keys'] if int(k['control'].split(':')[1])//128!=1]
        with self.request('/api/config',incoming):pass
        restored=load_config();newthird=next(k for k in restored['keys'] if k['control']=='key:256')
        self.assertEqual((newthird['id'],newthird['press_topic']),(third['id'],third['press_topic']))
        self.assertEqual(newthird['name'],'Taste 7');self.assertEqual(len(restored['keys']),12)
        self.assertEqual(restored['devices']['tablet']['deck_keys']['0']['text'],'First')
        self.assertEqual(restored['devices']['tablet']['deck_keys']['256']['text'],'Third')
        self.assertEqual(restored['brokers'][0]['password'],'keep-secret')
        before=(home()/'config.json').read_bytes()
        incoming['devices']['tablet']['deck_page_order']=[1,2]
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/config',incoming)
        self.assertEqual((home()/'config.json').read_bytes(),before)
