import copy
import sys
import time
import types
import json
from unittest.mock import Mock,patch
from tests.test_hub import TemporaryHome
from tests.broker import Broker,wait_for
from ugso_usbhub.gamepad import Gamepad,AXES,PROFILE,BUTTON_NAMES
from ugso_usbhub.storage import load_config,save_config,validate,home
from ugso_usbhub.hardware import Hardware
from ugso_usbhub.mqtt import Brokers
from ugso_usbhub.core import Core


def settings():
    return {'name':'Generic USB Joystick','enabled':True,'gamepad_profile':PROFILE,
        'gamepad_axes_enabled':True,'targets':['broker1','broker2','broker3']}


class GamepadTests(TemporaryHome):
    def test_four_axes_endpoints_center_and_abs_z_ignored(self):
        events=[];pad=Gamepad(lambda *e:events.append(e),{name:(0,255,15) for name in AXES},settings())
        for n,(name,(code,_)) in enumerate(AXES.items()):
            for moment,value,expected in ((1,0,0),(2,128,50),(3,255,100)):
                pad.feed(3,code,value,moment+n*4);pad.feed(0,0,0,moment+n*4)
                self.assertEqual(events[-1],('_gamepad_axis',name,expected))
        count=len(events)
        for value in (0,135,255):pad.feed(3,2,value,20);pad.feed(0,0,0,20)
        self.assertEqual(len(events),count)

    def test_deadzone_clamping_rate_dedupe_and_pending_cancel(self):
        events=[];opts=settings();opts['gamepad_rate']=5
        pad=Gamepad(lambda *e:events.append(e),{'left_x':(0,255,15)},opts)
        for now,value in ((1,128),(1.3,129),(1.6,140),(1.9,113)):
            pad.feed(3,0,value,now);pad.feed(0,0,0,now)
        self.assertEqual(events,[('_gamepad_axis','left_x',50)])
        pad.feed(3,0,255,2);pad.feed(0,0,0,2)
        pad.feed(3,0,-30,2.01);pad.feed(0,0,0,2.01);self.assertEqual(len(events),2)
        pad.tick(2.21);self.assertEqual(events[-1][2],0)
        pad.feed(3,0,255,2.22);pad.feed(0,3,0,2.23);pad.tick(3)
        self.assertEqual(len(events),3)
        pad.feed(3,0,255,3.1);opts['gamepad_axes_enabled']=False;pad.configure(opts);pad.tick(5)
        self.assertEqual(len(events),3)

    def test_per_axis_opt_out_missing_range_and_invalid_range(self):
        events=[];opts=settings();opts['gamepad_axes']={'left_x':{'enabled':False}}
        pad=Gamepad(lambda *e:events.append(e),{'left_x':(0,255,0),'left_y':(0,0,0)},opts)
        for code in (0,1,3,5,2):pad.feed(3,code,255,1);pad.feed(0,0,0,1)
        self.assertFalse(events)

    def test_config_saved_topics_existing_keys_and_validation(self):
        config=load_config();config['devices']['pad']=settings();save_config(config)
        device=config['devices']['pad'];self.assertEqual(len(device['gamepad_axes']),4)
        self.assertEqual(device['gamepad_axes']['left_x']['topic'],'generic-usb-joystick-gamepad/left-x/value')
        device['gamepad_axes']['left_x']['topic']='custom/lx';save_config(config)
        device['gamepad_axes_enabled']=False;save_config(config);device['gamepad_axes_enabled']=True;save_config(config)
        self.assertEqual(load_config()['devices']['pad']['gamepad_axes']['left_x']['topic'],'custom/lx')
        for change in ({'gamepad_axes_enabled':'yes'},{'gamepad_profile':'unknown'},{'gamepad_rate':0},
            {'gamepad_rate':31},{'gamepad_axes':{'ABS_Z':{}}},{'gamepad_axes':{'left_x':{'topic':'bad/#'}}},
            {'gamepad_axes':{'left_x':{'enabled':'yes'}}},{'gamepad_axes':{'left_x':{'topic':'same'},'left_y':{'topic':'same'}}}):
            invalid=copy.deepcopy(config);invalid['devices']['pad'].update(change)
            with self.assertRaises(ValueError):validate(invalid)

    def test_hardware_scan_poll_buttons_axis_z_ignore_and_opt_out(self):
        events=[];hw=Hardware(lambda *e:events.append(e));device=Mock();device.fd=15
        device.capabilities.return_value={3:[0,1,2,3,5]}
        device.absinfo.return_value=types.SimpleNamespace(min=0,max=255,flat=15)
        config=load_config();config['devices']['pad']=settings();validate(config)
        found=[{'id':'pad','vendor':'0079','product_id':'0006','kind':'input','inputs':['/dev/input/event15']}]
        ecodes=types.SimpleNamespace(EV_ABS=3,EV_KEY=1,EV_REL=2,KEY={},BTN={294:'BTN_BASE'},REL={})
        evdev=types.SimpleNamespace(InputDevice=Mock(return_value=device),ecodes=ecodes)
        raw=[types.SimpleNamespace(type=t,code=c,value=v) for t,c,v in ((3,2,255),(3,0,255),(0,0,0),(1,294,1),(1,294,0))]
        device.read.side_effect=lambda:iter(raw)
        with patch.object(sys,'platform','linux'),patch.dict('sys.modules',{'evdev':evdev}),patch('ugso_usbhub.hardware.inventory',return_value=found),patch('ugso_usbhub.hardware.select.select',return_value=([15],[],[])),patch.object(hw,'_scan_decks'):
            hw.scan(config);self.assertIn('/dev/input/event15',hw.gamepads);hw.poll()
            self.assertIn(('pad','_gamepad_axis','left_x',100),events)
            self.assertIn(('pad','BTN_BASE','press',1),events);self.assertIn(('pad','BTN_BASE','release',0),events)
            self.assertEqual(len([e for e in events if e[1]=='_gamepad_axis']),1)
            config['devices']['pad']['gamepad_axes_enabled']=False;hw.scan(config);self.assertFalse(hw.gamepads)
            config['devices']['pad']['gamepad_axes_enabled']=True;found[0]['product_id']='9999';hw.scan(config);self.assertFalse(hw.gamepads)
        hw.close()


class GamepadMqttTests(TemporaryHome):
    def test_real_three_brokers_four_sensors_buttons_learning_and_cleanup(self):
        servers=[Broker() for _ in range(3)];pool=None;core=None
        try:
            config=load_config()
            for broker,server in zip(config['brokers'],servers):broker.update(enabled=True,host='127.0.0.1',port=server.port,discovery=broker['id']!='broker2')
            config['devices']['pad']=settings()
            config['keys']=[{'id':'button-'+str(n),'device':'pad','control':control,'name':name,'press':True,'release':True,'switch':False,
                'press_topic':'gamepad/'+control+'/press','release_topic':'gamepad/'+control+'/release'} for n,(control,name) in enumerate(BUTTON_NAMES.items())]
            save_config(config);before=(home()/'config.json').read_bytes();pool=Brokers(config,lambda *a:None)
            wait_for(lambda:all(pool.states.get(b['id'])=='online' for b in config['brokers']))
            wait_for(lambda:len([m for m in servers[0].messages if m[0].startswith('homeassistant/sensor/')])==4)
            sensors={t:json.loads(p) for t,p,r in servers[0].messages if t.startswith('homeassistant/sensor/')}
            self.assertEqual(len({v['unique_id'] for v in sensors.values()}),4)
            self.assertTrue(all(v['device']['identifiers']==[f"ugso_{config['hub_id']}_pad"] for v in sensors.values()))
            self.assertFalse(any(t.startswith('homeassistant/') for t,p,r in servers[1].messages))
            with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
            for name in AXES:core.event('pad','_gamepad_axis',name,75)
            for control in BUTTON_NAMES:
                core.event('pad',control,'press',1);core.event('pad',control,'release',0)
            wait_for(lambda:all(len([m for m in s.messages if '-gamepad/' in m[0]])==4 for s in servers))
            wait_for(lambda:all(len([m for m in s.messages if m[0].startswith('gamepad/')])==12 for s in servers))
            for s in servers:
                self.assertTrue(all(p==b'75' and not r for t,p,r in s.messages if '-gamepad/' in t))
            core.learning={'device':'pad','expires':time.time()+60};count=len(core.events)
            core.event('pad','_gamepad_axis','left_x',12);self.assertEqual(len(core.events),count)
            core.learning={};self.assertEqual((home()/'config.json').read_bytes(),before)
            replacement=copy.deepcopy(config);replacement['devices']['pad']['gamepad_axes_enabled']=False
            pool.cleanup_removed(replacement)
            wait_for(lambda:len([m for m in servers[0].messages if m[0].startswith('homeassistant/sensor/') and m[1]==b''])==4)
            pool.config=replacement;self.assertEqual(pool.send_gamepad_value('pad','left_x',30)['delivered'],0)
            pool.config=config;config['devices']['pad']['targets']=['broker3']
            self.assertEqual(pool.send_gamepad_value('pad','left_x',30)['delivered'],1)
            servers[2].close();wait_for(lambda:pool.states['broker3']=='offline')
            self.assertEqual(pool.send_gamepad_value('pad','left_x',70)['delivered'],0)
            with self.assertRaises(ValueError):pool.send_gamepad_value('pad','ABS_Z',70)
        finally:
            if pool:pool.close()
            if core:core.hardware.close();core.mobile.close()
            for server in servers:server.close()
