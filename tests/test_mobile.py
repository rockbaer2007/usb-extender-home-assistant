"""Real loopback WebSocket, NaCl, icon decoding and MQTT integration.

The peer uses PyNaCl Box rather than the server's framing helpers. It is a
protocol simulator, not a claim of successful operation with the Android app.
"""
import copy
import hashlib
import io
import json
import socket
import time
import threading
import unittest
from urllib.parse import urlsplit, parse_qs
import lz4.block
from PIL import Image
from nacl.public import PrivateKey, PublicKey, Box
from websockets.sync.client import connect, ClientConnection
from websockets.frames import Frame, OP_PING
from websockets.exceptions import ConnectionClosed
from ugso_usbhub.mobile import MobileServer, control, pairing_info, settings
from ugso_usbhub.mobile_protocol import ClientMessage, ServerMessage
from ugso_usbhub.storage import load_config, save_config, validate, home, read_json, atomic_json
from ugso_usbhub.hardware import Hardware
from ugso_usbhub import __version__
from tests import test_hub as hub
from tests.broker import Broker, wait_for


class Peer:
    def __init__(self, port, key=None, connection_class=None):
        self.private=key or PrivateKey.generate()
        self.ws=connect(f"ws://127.0.0.1:{port}/",compression=None,open_timeout=2,close_timeout=1,ping_interval=None,create_connection=connection_class)
        self.ws.send(ClientMessage(hello={"publicKey":bytes(self.private.public_key),"clientInformation":{"name":"Android probe","protocolVersion":2}}).SerializeToString())
        self.hello=ServerMessage.FromString(self.ws.recv(timeout=2)).hello
        self.box=Box(self.private,PublicKey(self.hello.publicKey))

    def send(self, **payload):
        self.ws.send(bytes(self.box.encrypt(ClientMessage(**payload).SerializeToString())))

    def recv(self):
        return ServerMessage.FromString(self.box.decrypt(self.ws.recv(timeout=3)))

    def close(self):self.ws.close()


class MobileTests(hub.TemporaryHome):
    def test_tablet_8x8_next_key7_previous_key0_roundtrips(self):
        from unittest.mock import patch
        from tests.test_pages import Recorder
        from ugso_usbhub.core import Core
        from ugso_usbhub.keymap import ensure_deck_keys
        peer=self.pair();ident=self.create(peer)
        peer.send(updateKeypadConfig={'layoutCrop':{'width':8,'height':8},'iconSize':{'width':144,'height':144}})
        wait_for(lambda:self.server.decks()[ident].key_count()==64 and self.server.decks()[ident].key_image_format()['size']==(144,144))
        self.config['devices'][ident]={'enabled':True,'name':'Tablet','targets':['broker1'],
            'deck_page_count':2,'deck_page_order':[0,1],'deck_keys':{
                '7':{'action':'next','show_page':True},
                '128':{'action':'previous','show_page':True},
                '0':{'text':'First page','background':'#ff0000'},
                '129':{'text':'Second page','background':'#0000ff'}}}
        ensure_deck_keys(self.config,self.server.inventory());save_config(self.config)
        pool=Recorder()
        with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
        core.mobile=self.server;core.hardware.mobile=self.server
        self.server.current_page=core.hardware.active_page;self.server.emit=core.enqueue
        listener=self.server.server;core.hardware.refresh_decks()
        def receive_context(target):
            for _ in range(200):
                message=peer.recv()
                if message.WhichOneof('payload')=='context' and message.context.currentPage==target:
                    self.assertEqual(message.context.totalPages,2)
                    self.assertEqual(len(message.context.actions),64)
                    return
            self.fail('Expected page context')
        def press(key,pressed):
            peer.send(keyPress={'index':key,'pressed':pressed})
            wait_for(lambda:not core.queue.empty())
            core.event(*core.queue.get_nowait())
        try:
            for _ in range(6):
                press(7,True);receive_context(1);press(7,False)
                press(0,True);receive_context(0);press(0,False)
            self.assertEqual(core.hardware.active_page(ident),0)
            self.assertEqual(pool.calls,[])
            self.assertIs(self.server.server,listener)
            self.assertFalse(self.server.status()['recent_disconnects'])
        finally:pool.close();core.hardware.close()

    def test_two_mobile_devices_page_navigation_images_and_context_without_reconnect(self):
        from unittest.mock import patch
        from tests.test_pages import Recorder
        from ugso_usbhub.core import Core
        from ugso_usbhub.keymap import ensure_deck_keys
        first=self.pair();tablet=self.create(first)
        second=self.pair();phone=self.create(second)
        for ident in [tablet,phone]:
            self.config['devices'][ident]={'enabled':True,'name':ident,'targets':['broker1'],'deck_page_count':3,'deck_keys':{}}
            for page in range(3):
                self.config['devices'][ident]['deck_keys'][str(page*128)]={'background':['#ff0000','#0000ff','#00ff00'][page]}
                self.config['devices'][ident]['deck_keys'][str(page*128+5)]={'action':'next','show_page':True}
        self.config['devices'][tablet]['deck_keys']['5']={'action':'goto','target_page':2,'show_page':True}
        self.config['devices'][tablet]['deck_keys']['133']={'action':'previous','show_page':True}
        ensure_deck_keys(self.config,self.server.inventory());save_config(self.config)
        pool=Recorder()
        with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
        core.mobile=self.server;core.hardware.mobile=self.server
        self.server.current_page=core.hardware.active_page;self.server.emit=core.enqueue
        listener=self.server.server;core.hardware.refresh_decks()
        def drain(peer,kind):
            for _ in range(30):
                message=peer.recv()
                if message.WhichOneof('payload')==kind:return message
            self.fail('Expected '+kind)
        def process(peer,payload):
            peer.send(**payload);wait_for(lambda:not core.queue.empty());core.event(*core.queue.get_nowait())
        try:
            for peer in [first,second]:
                for _ in range(6):drain(peer,'icon')
            process(first,{'keyPress':{'index':5,'pressed':True}})
            context=drain(first,'context').context
            self.assertEqual((context.currentPage,context.totalPages),(1,3))
            frames=[drain(first,'icon').icon for _ in range(2)]
            image=next(frame for frame in frames if frame.index==0)
            raw=lz4.block.decompress(image.image.image,uncompressed_size=72*72*4)
            self.assertEqual(Image.frombytes('RGBA',(72,72),raw,'raw','BGRA').getpixel((20,20)),(0,0,255,255))
            self.assertEqual(core.hardware.active_page(phone),0)
            self.assertEqual(pool.calls,[])
            process(first,{'keyPress':{'index':5,'pressed':False}})
            for _ in range(3):
                process(first,{'keyPress':{'index':5,'pressed':True}})
                self.assertEqual(drain(first,'context').context.currentPage,0)
                process(first,{'keyPress':{'index':5,'pressed':False}})
                process(first,{'keyPress':{'index':5,'pressed':True}})
                self.assertEqual(drain(first,'context').context.currentPage,1)
                process(first,{'keyPress':{'index':5,'pressed':False}})
            self.assertEqual(pool.calls,[])
            process(first,{'keyPress':{'index':0,'pressed':True}})
            self.assertTrue(all(args[1]=='key:128' for args,kwargs in pool.calls))
            process(first,{'keyPress':{'index':0,'pressed':False}})
            process(second,{'nextPage':{}})
            self.assertEqual(drain(second,'context').context.currentPage,1)
            process(second,{'pageByIndex':{'index':0}})
            self.assertEqual(drain(second,'context').context.currentPage,0)
            self.assertEqual(core.hardware.active_page(tablet),1)
            self.assertIs(self.server.server,listener)
            self.assertTrue(all(c['authorized'] for c in self.server.status()['clients']))
        finally:pool.close();core.hardware.close()

    def test_animation_frames_over_encrypted_mobile_connection(self):
        from ugso_usbhub import icons as library
        from tests.test_animated_icons import moving
        normal=library.add(moving(),"Normal.gif")
        out=io.BytesIO();Image.new("RGB",(24,24),"green").save(out,format="PNG")
        pressed=library.add(out.getvalue(),"Pressed.png")
        peer=self.pair();ident=self.create(peer)
        self.config["devices"][ident]={"enabled":True,"deck_keys":{"0":{"icon":normal,"pressed_icon":pressed}}}
        hardware=Hardware(lambda *a:None);hardware.mobile=self.server;hardware.config=self.config
        hardware.refresh_decks()
        for _ in range(6):self.assertEqual(peer.recv().WhichOneof("payload"),"icon")
        job=hardware.animations[(ident,0)]
        hardware.animate(job["start"]+.15)
        frame=peer.recv().icon
        raw=lz4.block.decompress(frame.image.image,uncompressed_size=72*72*4)
        self.assertEqual(Image.frombytes("RGBA",(72,72),raw,"raw","BGRA").getpixel((30,30)),(0,0,255,255))
        hardware.set_pressed(ident,0,True)
        frame=peer.recv().icon
        raw=lz4.block.decompress(frame.image.image,uncompressed_size=72*72*4)
        self.assertEqual(Image.frombytes("RGBA",(72,72),raw,"raw","BGRA").getpixel((30,30)),(0,128,0,255))
        self.assertNotIn((ident,0),hardware.animations)
        before=self.server.status()["clients"][0]["images_sent"]
        hardware.animate(job["start"]+10)
        time.sleep(.2)
        self.assertEqual(self.server.status()["clients"][0]["images_sent"],before)
        hardware.set_pressed(ident,0,False)
        self.assertEqual(peer.recv().WhichOneof("payload"),"icon")

    def setUp(self):
        super().setUp()
        self.config=load_config()
        self.config["password_hash"]="test-password-already-configured"
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
        self.config["mobile"]={"enabled":True,"host":"127.0.0.1","port":port,"advertise_host":"127.0.0.1","columns":3,"rows":2}
        self.events=[]
        self.server=MobileServer(lambda *args:self.events.append(args))
        self.server.configure(self.config)
        self.assertEqual(self.server.error,"")
        self.peers=[]

    def tearDown(self):
        for peer in self.peers:peer.close()
        self.server.close()
        wait_for(lambda:not self.server.sessions)
        super().tearDown()

    def pair(self, connection_class=None):
        control({"action":"open"},self.config)
        peer=Peer(self.config["mobile"]["port"],connection_class=connection_class);self.peers.append(peer)
        self.assertTrue(peer.hello.clientNeedsAuthentication)
        peer.send(authenticate={"requestID":1})
        wait_for(lambda:any(s.request==1 for s in self.server.sessions))
        pending=self.server.status()["pending"][0]
        expected=hashlib.blake2b(bytes(peer.private.public_key),digest_size=32).hexdigest()[:6].upper()
        self.assertEqual(pending["fingerprint"],expected)
        control({"action":"allow","token":pending["token"]},self.config)
        self.assertEqual(peer.recv().ok.requestID,1)
        self.assertEqual(peer.recv().WhichOneof("payload"),"virtualDeviceList")
        return peer

    def create(self, peer):
        peer.send(createVirtualDevice={"requestID":2,"name":"Probe","keypadConfig":{"supportedIconImageFormats":[2],"iconSize":{"width":72,"height":72}}})
        opened=peer.recv()
        self.assertEqual(opened.WhichOneof("payload"),"virtualDeviceOpened")
        self.assertEqual(peer.recv().WhichOneof("payload"),"context")
        return opened.virtualDeviceOpened.device.id

    def test_disabled_default_binds_no_port(self):
        self.server.close()
        self.config.pop("mobile")
        self.server.configure(self.config)
        self.assertFalse(self.server.status()["active"])
        self.assertFalse(settings(load_config())["enabled"])

    def test_removed_deck_closes_only_its_session_and_keeps_trust(self):
        first=self.pair();one=self.create(first)
        second=self.pair();two=self.create(second)
        from ugso_usbhub.devices import administer
        before=read_json(home()/'mobile-trust.json',{})
        administer({'action':'remove','device':one},{})
        self.server.synchronize_storage()
        wait_for(lambda:not any(s.device==one for s in self.server.sessions))
        self.assertTrue(any(s.device==two and not s.closed for s in self.server.sessions))
        self.assertEqual(read_json(home()/'mobile-trust.json',{}),before)

    def test_revoked_client_closes_session_but_retains_deck(self):
        peer=self.pair();ident=self.create(peer)
        session=next(s for s in self.server.sessions if s.device==ident)
        from ugso_usbhub.devices import administer
        administer({'action':'revoke','device':session.client_id},{})
        self.server.synchronize_storage()
        wait_for(lambda:not self.server.sessions)
        self.assertIn(ident,read_json(home()/'mobile-devices.json',{}))

    def test_qr_contains_static_endpoint_and_workstation(self):
        info=pairing_info(self.config)
        query=parse_qs(urlsplit(info["url"]).query)
        self.assertEqual(query["w"],["usb-extender-"+self.config["hub_id"]])
        self.assertEqual(query["av2"],["127.0.0.1:"+str(self.config["mobile"]["port"])])
        import base64
        with Image.open(io.BytesIO(base64.b64decode(info["qr"]))) as qr:self.assertGreater(qr.width,100)

    def test_default_and_reported_tablet_layout_are_five_by_three(self):
        self.assertEqual((settings({})["rows"],settings({})["columns"]),(3,5))
        peer=self.pair()
        peer.send(createVirtualDevice={"requestID":2,"name":"Tablet 15","keypadConfig":{"supportedIconImageFormats":[2],"iconSize":{"width":72,"height":72},"layoutCrop":{"width":5,"height":3}}})
        self.assertEqual(peer.recv().WhichOneof("payload"),"virtualDeviceOpened")
        self.assertEqual(len(peer.recv().context.actions),15)
        self.assertEqual(self.server.inventory()[0]["deck"]["layout"],[3,5])
        self.assertEqual(self.server.inventory()[0]["deck"]["keys"],15)
        self.assertEqual(self.server.decks()[self.server.inventory()[0]["id"]].key_layout(),(3,5))
        self.assertEqual((self.config["mobile"]["rows"],self.config["mobile"]["columns"]),(2,3))

    def test_android_minimum_desktop_version_and_text_edits_keep_connection(self):
        peer=self.pair();ident=self.create(peer)
        # Android interprets Hello.version as the desktop version, requiring >=6.3.
        self.assertGreaterEqual(tuple(map(int,peer.hello.version.split('.'))),(6,3,0))
        self.assertNotEqual(peer.hello.version,__version__)
        self.assertEqual(peer.hello.osVersion,"USB Extender "+__version__)
        listener=self.server.server
        trust=copy.deepcopy(read_json(home()/"mobile-trust.json",{}))
        hardware=Hardware(lambda *a:None);hardware.mobile=self.server;hardware.config=self.config
        hardware.refresh_decks()
        for _ in range(6):self.assertEqual(peer.recv().WhichOneof('payload'),'icon')
        for position in ('top','center','bottom'):
            for font_size in (8,32):
                self.config['devices'][ident]={'deck_keys':{'0':{'text':'Licht ÄÖÜ 42','text_position':position,'font_size':font_size}}}
                self.server.configure(self.config);hardware.refresh_decks()
                while True:
                    response=peer.recv()
                    if response.WhichOneof('payload')=='icon':
                        self.assertEqual(response.icon.index,0)
                        break
                self.assertIs(self.server.server,listener)
                self.assertEqual(self.server.inventory()[0]['id'],ident)
        peer.send(keyPress={'index':0,'pressed':True})
        wait_for(lambda:bool(self.events))
        self.assertEqual(self.events[-1],(ident,'key:0','press',1))
        self.assertEqual(read_json(home()/"mobile-trust.json",{}),trust)

    def test_real_encrypted_pair_icons_keys_and_disconnect(self):
        peer=self.pair();ident=self.create(peer)
        self.config["devices"][ident]={"enabled":True,"deck_keys":{"0":{"background":"#123456","text":"Probe"}}}
        self.server.configure(self.config)
        hardware=Hardware(lambda *a:None)
        hardware.config=self.config;hardware.mobile=self.server
        hardware.refresh_decks()
        icons=[]
        while len(icons)<6:
            response=peer.recv()
            if response.WhichOneof("payload")=="icon":icons.append(response.icon)
        first=next(i for i in icons if i.index==0)
        self.assertEqual(first.image.format,2)
        raw=lz4.block.decompress(first.image.image,uncompressed_size=72*72*4)
        self.assertEqual(tuple(raw[:4]),(0x56,0x34,0x12,255))  # Android BGRA buffer.
        self.assertEqual(Image.frombytes('RGBA',(72,72),raw,'raw','BGRA').getpixel((0,0)),(0x12,0x34,0x56,255))
        peer.send(keyPress={"index":0,"pressed":True})
        peer.send(keyPress={"index":0,"pressed":True})
        peer.send(keyPress={"index":0,"pressed":False})
        wait_for(lambda:len(self.events)>=2)
        self.assertEqual(self.events[:2],[(ident,"key:0","press",1),(ident,"key:0","release",0)])
        peer.close();wait_for(lambda:any(e[1]=="_mobile_disconnect" for e in self.events))

    def test_unchanged_images_and_size_reports_do_not_retransmit(self):
        peer=self.pair();ident=self.create(peer)
        hardware=Hardware(lambda *a:None)
        hardware.config=self.config;hardware.mobile=self.server
        hardware.refresh_decks()
        for _ in range(6):self.assertEqual(peer.recv().WhichOneof("payload"),"icon")
        self.server.refresh_required.clear()
        for _ in range(10):
            peer.send(updateKeypadConfig={"iconSize":{"width":72,"height":72}})
        peer.send(keyPress={"index":0,"pressed":True})
        wait_for(lambda:bool(self.events))
        self.assertFalse(self.server.refresh_required.is_set())
        hardware.refresh_decks()
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=0.3)
        self.config["devices"][ident]={"deck_keys":{"0":{"background":"#123456"}}}
        hardware.refresh_decks()
        icon=peer.recv().icon
        self.assertEqual(icon.index,0)
        raw=lz4.block.decompress(icon.image.image,uncompressed_size=72*72*4)
        self.assertEqual(tuple(raw[:4]),(0x56,0x34,0x12,255))
        hardware.refresh_decks()
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=0.3)
        before=self.server.status()['clients'][0]
        for _ in range(3):
            self.server.configure(self.config)
            hardware.refresh_decks()
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=0.3)
        after=self.server.status()['clients'][0]
        self.assertEqual((after['images_sent'],after['contexts_sent']),(before['images_sent'],before['contexts_sent']))
        peer.send(updateKeypadConfig={"iconSize":{"width":90,"height":90}})
        wait_for(lambda:self.server.refresh_required.is_set())
        hardware.refresh_decks()
        for _ in range(6):self.assertEqual(peer.recv().icon.image.size.width,90)
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=0.3)
        peer.send(openVirtualDevice={"requestID":3,"deviceID":ident,"keypadConfig":{"supportedIconImageFormats":[2],"iconSize":{"width":90,"height":90}}})
        self.assertEqual(peer.recv().WhichOneof("payload"),"virtualDeviceOpened")
        self.assertEqual(peer.recv().WhichOneof("payload"),"context")
        hardware.refresh_decks()
        for _ in range(6):self.assertEqual(peer.recv().WhichOneof("payload"),"icon")

    def test_trust_and_device_survive_restart(self):
        peer=self.pair();key=peer.private;ident=self.create(peer)
        public=peer.hello.publicKey
        peer.close();self.server.close();wait_for(lambda:not self.server.sessions)
        self.server=MobileServer(lambda *a:None);self.server.configure(self.config)
        control({"action":"close"},self.config)
        again=Peer(self.config["mobile"]["port"],key);self.peers.append(again)
        self.assertFalse(again.hello.clientNeedsAuthentication)
        self.assertEqual(again.hello.publicKey,public)
        self.assertEqual(again.recv().virtualDeviceList.devices[0].id,ident)

    def test_reject_unknown_when_window_closed(self):
        with self.assertRaises(ConnectionClosed):Peer(self.config["mobile"]["port"])
        self.assertFalse(self.server.inventory())

    def test_hello_only_waiting_tablet_can_be_confirmed_before_authenticate(self):
        control({"action":"open"},self.config)
        peer=Peer(self.config["mobile"]["port"]);self.peers.append(peer)
        wait_for(lambda:bool(self.server.status()["pending"]))
        pending=self.server.status()["pending"][0]
        self.assertIsNone(self.server.sessions[0].request)
        self.assertFalse(self.server.sessions[0].authorized)
        self.assertFalse(read_json(home()/"mobile-trust.json",{}))
        peer.send(clientCapabilities={"isUserPro":False})
        control({"action":"allow","token":pending["token"]},self.config)
        self.assertEqual(peer.recv().WhichOneof("payload"),"virtualDeviceList")
        self.assertFalse(self.server.status()["pending"])
        peer.send(authenticate={"requestID":42})
        self.assertEqual(peer.recv().ok.requestID,42)
        self.assertEqual(peer.recv().WhichOneof("payload"),"virtualDeviceList")
        self.create(peer)

    def test_hello_only_pending_denial_never_trusts_or_emits_keys(self):
        control({"action":"open"},self.config)
        peer=Peer(self.config["mobile"]["port"]);self.peers.append(peer)
        wait_for(lambda:bool(self.server.status()["pending"]))
        token=self.server.status()["pending"][0]["token"]
        control({"action":"deny","token":token},self.config)
        with self.assertRaises(ConnectionClosed):peer.recv()
        self.assertFalse(read_json(home()/"mobile-trust.json",{}))
        self.assertFalse(self.events)

    def test_capabilities_before_approval_do_not_authorize_input(self):
        control({"action":"open"},self.config)
        peer=Peer(self.config["mobile"]["port"]);self.peers.append(peer)
        peer.send(clientCapabilities={"isUserPro":False})
        peer.send(keyPress={"index":0,"pressed":True})
        with self.assertRaises(ConnectionClosed):peer.recv()
        self.assertFalse(read_json(home()/"mobile-trust.json",{}))
        self.assertFalse(self.events)

    def test_deny_and_tampering_cannot_emit_keys(self):
        control({"action":"open"},self.config)
        peer=Peer(self.config["mobile"]["port"]);self.peers.append(peer)
        peer.send(authenticate={"requestID":1})
        wait_for(lambda:any(s.request==1 for s in self.server.sessions))
        control({"action":"deny","token":self.server.status()["pending"][0]["token"]},self.config)
        self.assertEqual(peer.recv().error.code,3)
        self.assertFalse(self.events)
        peer=self.pair()
        peer.ws.send(b"x"*48)
        with self.assertRaises(ConnectionClosed):peer.recv()
        self.assertFalse(self.events)

    def test_more_than_six_keys_without_pro_flags(self):
        self.config["mobile"].update(columns=5,rows=3)
        self.server.configure(self.config)
        peer=self.pair();ident=self.create(peer)
        self.assertEqual(self.server.inventory()[0]["deck"]["keys"],15)
        peer.send(keyPress={"index":14,"pressed":True})
        wait_for(lambda:bool(self.events))
        self.assertEqual(self.events[0],(ident,"key:14","press",1))

    def test_grid_setting_changes_do_not_restart_listener_or_disconnect(self):
        peer=self.pair();self.create(peer)
        listener=self.server.server
        self.config["mobile"].update(columns=5,rows=3)
        self.server.configure(self.config)
        self.assertIs(self.server.server,listener)
        self.assertEqual(self.server.inventory()[0]["deck"]["layout"],[3,5])
        self.assertEqual(len(peer.recv().context.actions),15)
        peer.send(keyPress={"index":14,"pressed":True})
        wait_for(lambda:bool(self.events))
        self.assertEqual(self.events[-1][1],"key:14")

    def test_tablet_layout_wins_over_fallback_changes_without_disconnect(self):
        peer=self.pair()
        peer.send(createVirtualDevice={"requestID":2,"name":"Tablet raster","keypadConfig":{"supportedIconImageFormats":[2],"iconSize":{"width":72,"height":72},"layoutCrop":{"width":5,"height":3}}})
        peer.recv();peer.recv()
        listener=self.server.server
        self.config["mobile"].update(columns=4,rows=4)
        self.server.configure(self.config)
        self.assertIs(self.server.server,listener)
        self.assertEqual(self.server.inventory()[0]["deck"]["layout"],[3,5])
        self.assertEqual(self.server.inventory()[0]["deck"]["layout_source"],"tablet")
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=0.3)  # Identical context is not resent.
        peer.send(updateKeypadConfig={"layoutCrop":{"width":3,"height":5}})
        wait_for(lambda:self.server.inventory()[0]["deck"]["layout"]==[5,3])
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=0.3)  # Same 15 actions, different orientation.

    def test_socket_failure_does_not_change_existing_configuration(self):
        before=copy.deepcopy(load_config())
        conflict=MobileServer(lambda *a:None)
        conflict.configure(self.config)
        self.assertFalse(conflict.status()["active"])
        self.assertTrue(conflict.error)
        self.assertEqual(load_config(),before)

    def test_optional_commands_do_not_disconnect_or_refresh_the_deck(self):
        peer=self.pair();ident=self.create(peer)
        peer.send(assignShortcut={'profileID':ident,'shortcutID':'optional','index':0})
        peer.send(triggerShortcut={'deviceID':ident,'shortcutID':'optional'})
        peer.send(removeShortcut={'requestID':42,'shortcutID':'optional'})
        response=peer.recv()
        self.assertEqual(response.error.requestID,42)
        peer.ws.send(bytes(peer.box.encrypt(b'\xc2\x0c\x00')))  # Unknown future field 200.
        peer.send(keyPress={'index':0,'pressed':True})
        wait_for(lambda:bool(self.events))
        self.assertEqual(self.events[-1],(ident,'key:0','press',1))
        self.assertEqual(self.server.status()['clients'][0]['contexts_sent'],1)
        self.assertFalse(self.server.status()['recent_disconnects'])

    def test_per_device_grid_and_offline_metadata_survive_restart(self):
        from ugso_usbhub.keymap import ensure_deck_keys
        peer=self.pair();ident=self.create(peer)
        self.config['devices'][ident]={'name':'Tablet','enabled':True,'mobile_layout':{'rows':4,'columns':6}}
        listener=self.server.server;self.server.configure(self.config)
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=.3)
        self.assertIs(self.server.server,listener)
        peer.send(updateKeypadConfig={'layoutCrop':{'width':5,'height':3}})
        self.assertEqual(len(peer.recv().context.actions),15)
        self.assertEqual(self.server.inventory()[0]['deck']['layout'],[3,5])
        self.assertEqual(self.server.inventory()[0]['deck']['layout_source'],'tablet')
        peer.send(updateKeypadConfig={'layoutCrop':{'width':6,'height':4}})
        self.assertEqual(len(peer.recv().context.actions),24)
        self.assertIs(self.server.server,listener)
        peer.send(updateKeypadConfig={'layoutCrop':{'width':4,'height':6}})
        wait_for(lambda:self.server.inventory()[0]['deck']['layout']==[6,4])
        with self.assertRaises(TimeoutError):peer.ws.recv(timeout=.3)
        ensure_deck_keys(self.config,self.server.inventory());save_config(self.config)
        self.assertEqual(load_config()['devices'][ident]['deck_info']['layout'],[6,4])
        self.assertEqual(load_config()['devices'][ident]['mobile_layout'],{'rows':4,'columns':6})  # Preserved, ignored.
        private=peer.private;peer.close();wait_for(lambda:not self.server.status()['clients'])
        self.assertEqual(self.server.status()['known_decks'][0]['deck']['keys'],24)
        self.assertTrue(self.server.status()['recent_disconnects'])
        self.server.close();self.server=MobileServer(lambda *a:self.events.append(a));self.server.configure(load_config())
        self.assertEqual(self.server.status()['known_decks'][0]['deck']['layout'],[6,4])
        again=Peer(self.config['mobile']['port'],private);self.peers.append(again)
        self.assertFalse(again.hello.clientNeedsAuthentication);again.recv()
        again.send(openVirtualDevice={'requestID':3,'deviceID':ident,'keypadConfig':{'supportedIconImageFormats':[2],'iconSize':{'width':72,'height':72},'layoutCrop':{'width':5,'height':3}}})
        self.assertEqual(again.recv().virtualDeviceOpened.device.id,ident)
        self.assertEqual(len(again.recv().context.actions),15)
        c=load_config();c['devices'][ident]['mobile_layout']['rows']=0
        with self.assertRaises(ValueError):validate(c)

    def test_android_receive_watchdog_stays_alive_without_image_updates(self):
        class AndroidTransport(ClientConnection):
            def __init__(self,*args,**kwargs):
                self.last_frame=time.monotonic();self.ping_payloads=[]
                super().__init__(*args,**kwargs)
            def process_event(self,event):
                if isinstance(event,Frame):
                    self.last_frame=time.monotonic()
                    if event.opcode==OP_PING:self.ping_payloads.append(bytes(event.data))
                super().process_event(event)
        peer=self.pair(AndroidTransport);ident=self.create(peer)
        stop=threading.Event();expired=[]
        def watchdog():
            while not stop.wait(.05):
                if time.monotonic()-peer.ws.last_frame>10:
                    expired.append(True);peer.ws.close(1001,'receive timeout');return
        thread=threading.Thread(target=watchdog,daemon=True);thread.start()
        try:
            # Real wall time: cross the previous 15-second heartbeat and Android's
            # 10-second receive watchdog without sending Context/Icon messages.
            with self.assertRaises(TimeoutError):peer.ws.recv(timeout=16.2)
            self.assertFalse(expired)
            self.assertGreaterEqual(len(peer.ws.ping_payloads),3)
            self.assertEqual(set(peer.ws.ping_payloads),{b''})
            state=self.server.status()['clients'][0]
            self.assertEqual((state['images_sent'],state['contexts_sent']),(0,1))
            self.assertGreaterEqual(state['pongs_received'],3)
            peer.send(keyPress={'index':0,'pressed':True})
            wait_for(lambda:bool(self.events))
            self.assertEqual(self.events[-1],(ident,'key:0','press',1))
        finally:stop.set();thread.join(timeout=1)

    def test_automatic_channels_reach_real_mqtt_from_mobile_press_release(self):
        from ugso_usbhub.keymap import ensure_deck_keys
        from ugso_usbhub.core import Core
        peer=self.pair();ident=self.create(peer);broker=Broker()
        self.config['devices'][ident]={'enabled':True,'name':'Stream Deck Mobile','targets':['broker1']}
        self.config['brokers'][0].update(enabled=True,host='127.0.0.1',port=broker.port,discovery=False)
        ensure_deck_keys(self.config,self.server.inventory());save_config(self.config)
        core=Core();self.server.emit=core.enqueue
        try:
            wait_for(lambda:core.brokers.states.get('broker1')=='online')
            for pressed in (True,False):
                peer.send(keyPress={'index':0,'pressed':pressed})
                wait_for(lambda:not core.queue.empty())
                core.event(*core.queue.get_nowait())
            for key,action in core.buttons.tick(time.monotonic()+1):core.button_event(key,action)
            core.brokers.flush_resets(time.monotonic()+1)
            expected={'press':b'press','release':b'release','switch':b'ON','state':b'OFF','button':b'click','button-plus':b'click','click':b'click'}
            wait_for(lambda:all(any(t=='stream-deck-mobile-key-0/'+mode and p==payload for t,p,_ in broker.messages) for mode,payload in expected.items()))
            wait_for(lambda:any(t.endswith('/press-plus') and p==b'' for t,p,_ in broker.messages))
        finally:core.brokers.close();broker.close()

    def test_disabling_closes_connections_and_port_but_keeps_trust(self):
        peer=self.pair();self.create(peer)
        before=read_json(home()/"mobile-trust.json",{})
        self.config["mobile"]["enabled"]=False
        self.server.configure(self.config)
        with self.assertRaises(ConnectionClosed):peer.recv()
        with socket.socket() as sock:self.assertNotEqual(sock.connect_ex(("127.0.0.1",self.config["mobile"]["port"])),0)
        self.assertEqual(read_json(home()/"mobile-trust.json",{}),before)

    def test_encrypted_key_to_actual_mqtt_peer(self):
        from ugso_usbhub.core import Core
        peer=self.pair();ident=self.create(peer)
        broker=Broker()
        self.config["devices"][ident]={"enabled":True,"targets":["broker1"]}
        self.config["brokers"][0].update(enabled=True,host="127.0.0.1",port=broker.port)
        self.config["bindings"]=[{"id":"mobile-test","device":ident,"control":"key:0","gesture":"press","topic":"probe/mobile/press","payload":"ON"}]
        save_config(self.config)
        core=Core()
        self.server.emit=core.enqueue
        try:
            wait_for(lambda:core.brokers.states.get("broker1")=="online")
            peer.send(keyPress={"index":0,"pressed":True})
            wait_for(lambda:not core.queue.empty())
            core.event(*core.queue.get_nowait())
            wait_for(lambda:any(m[0]=="probe/mobile/press" for m in broker.messages))
            self.assertEqual(next(m[1] for m in broker.messages if m[0]=="probe/mobile/press"),b"ON")
        finally:core.brokers.close();broker.close()


class MobileWebTests(hub.WebTests):
    def test_web_activation_qr_approval_and_configuration_preservation(self):
        import subprocess,sys
        from ugso_usbhub.storage import public_config
        before=load_config()
        before["brokers"][0]["password"]="existing-mqtt-password"
        save_config(before)
        with socket.socket() as sock:sock.bind(("127.0.0.1",0));port=sock.getsockname()[1]
        process=subprocess.Popen([sys.executable,"-m","ugso_usbhub.cli","daemon"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        peer=None
        try:
            with self.assertRaises(__import__('urllib').error.HTTPError):self.request("/api/mobile/qr",{})
            self.login()
            def active(value):
                with self.request("/api/status") as response:return json.load(response).get("mobile",{}).get("active") is value
            wait_for(lambda:active(False))
            incoming=public_config(before)
            incoming["mobile"]={"enabled":True,"host":"127.0.0.1","advertise_host":"127.0.0.1","port":port}
            with self.request("/api/config",incoming):pass
            wait_for(lambda:active(True))
            with self.request("/api/mobile/qr",{}) as response:self.assertIn("av2=",json.load(response)["url"])
            with self.request("/api/mobile/control",{"action":"open"}):pass
            peer=Peer(port)
            peer.send(authenticate={"requestID":1})
            pending=[]
            def awaiting():
                with self.request("/api/status") as response:
                    pending[:]=json.load(response).get("mobile",{}).get("pending",[])
                return bool(pending)
            wait_for(awaiting)
            with self.request("/api/mobile/control",{"action":"allow","token":pending[0]["token"]}):pass
            self.assertEqual(peer.recv().ok.requestID,1)
            self.assertEqual(peer.recv().WhichOneof("payload"),"virtualDeviceList")
            peer.close();peer=None
            incoming["mobile"]["enabled"]=False
            with self.request("/api/config",incoming):pass
            wait_for(lambda:active(False))
            self.assertEqual(load_config()["brokers"][0]["password"],"existing-mqtt-password")
            self.assertEqual(load_config()["hub_id"],before["hub_id"])
            self.assertIsNone(process.poll())  # USB/MQTT daemon survives Mobile shutdown.
        finally:
            if peer:peer.close()
            process.terminate();process.wait(timeout=5)
