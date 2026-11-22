"""Offline regression tests: identity, administration, steps and MT input."""
import copy
import json
import tarfile
import time
import urllib.error
import urllib.request
import http.cookiejar
import threading
import types
from unittest.mock import Mock, patch
from tests import test_hub as fixtures
from tests.test_hub import TemporaryHome
from tests.test_learning import row
from ugso_usbhub.storage import home, load_config, save_config, atomic_json, read_json, validate, password_hash
from ugso_usbhub.devices import resolve_inventory, remember_hardware, administer
from ugso_usbhub.hardware import identity, hardware_key, unique_id
from ugso_usbhub.core import Core
from ugso_usbhub.touchpad import Touchpad, EV_ABS, EV_SYN, EV_KEY, MT_SLOT, MT_ID, MT_X, MT_Y, SYN_REPORT, SYN_DROPPED, BTN_LEFT


def unit(serial='abc',port='1-2'):
    return dict(id=identity('046d','4101',serial,port),vendor='046d',product_id='4101',
                serial=serial,port=port,kind='input',inputs=['/dev/input/event4'],
                hardware_key=hardware_key('046d','4101',serial))


class DeviceTests(TemporaryHome):
    def setUp(self):
        super().setUp();self.config=load_config()
        self.config['devices']={'saved':{'name':'T650','enabled':True,'targets':['broker2']}}
        self.config['keys']=[{**row(),'device':'saved','repeat':False}]
        self.config['brokers'][1]['password']='keep-this-secret'
        save_config(self.config)

    def test_serial_survives_hub_and_port_changes_legacy_retained(self):
        first=unit();self.config['devices']['saved']['hardware']={**first,'observed_id':first['id']}
        changed=unit(port='2-7.4')
        self.assertEqual(resolve_inventory([changed],self.config)[0]['id'],'saved')
        plain=unit(serial='');legacy=copy.deepcopy(self.config)
        legacy['devices']={plain['id']:{'enabled':True}}
        self.assertEqual(resolve_inventory([plain],legacy)[0]['id'],plain['id'])
        self.assertEqual(unique_id('00:00:00:00:00:00'),'')
        self.assertEqual(unique_id('UNKNOWN'),'')

    def test_ambiguous_serials_never_choose_first_saved_device(self):
        a,b=unit(port='1-2'),unit(port='1-3')
        self.config['devices']['saved']['hardware']={**a,'observed_id':a['id']}
        found=resolve_inventory([a,b],self.config)
        self.assertEqual(len({d['id'] for d in found}),2)
        self.assertNotIn('saved',[d['id'] for d in found])
        self.assertNotEqual(found[0]['observed_id'],found[1]['observed_id'])
        remember_hardware(self.config,found)
        self.assertEqual(self.config['devices']['saved']['hardware']['port'],'1-2')

    def test_manual_assignment_preserves_topics_credentials_and_restart(self):
        new=unit(serial='',port='1-7.3');snapshot={'updated':time.time(),'devices':[new]}
        answer=administer({'action':'reassign','device':'saved','observed_id':new['id']},snapshot)
        saved=load_config()
        self.assertEqual(saved['keys'],self.config['keys'])
        self.assertEqual(saved['brokers'],self.config['brokers'])
        self.assertEqual(resolve_inventory([new],saved)[0]['id'],'saved')
        with tarfile.open(answer['backup']) as archive:
            original=json.load(archive.extractfile('config.json'))
        self.assertEqual(original,self.config)
        with self.assertRaises(ValueError):
            administer({'action':'reassign','device':'saved','observed_id':new['id']},{'devices':[new]})

    def test_remove_is_scoped_icons_and_trust_retained_rollback(self):
        self.config['devices']['other']={'enabled':True};save_config(self.config)
        atomic_json(home()/'switches.json',{'volume':True,'other':False})
        atomic_json(home()/'mobile-trust.json',{'client':{'key':'keep'}})
        icons=home()/'icons';icons.mkdir();(icons/'keep.png').write_bytes(b'icon')
        with patch('ugso_usbhub.devices.save_config',side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):administer({'action':'remove','device':'saved'},{})
        self.assertEqual(load_config(),self.config)
        self.assertEqual(read_json(home()/'switches.json',{}),{'volume':True,'other':False})
        administer({'action':'remove','device':'saved'},{})
        saved=load_config();self.assertNotIn('saved',saved['devices']);self.assertIn('other',saved['devices'])
        self.assertEqual(saved['keys'],[])
        self.assertEqual(read_json(home()/'switches.json',{}),{'other':False})
        self.assertEqual(read_json(home()/'mobile-trust.json',{}),{'client':{'key':'keep'}})
        self.assertEqual((icons/'keep.png').read_bytes(),b'icon')

    def test_mobile_remove_and_revoke_are_separate(self):
        atomic_json(home()/'mobile-devices.json',{'deck':{'name':'Tablet'},'other':{}})
        atomic_json(home()/'mobile-trust.json',{'owner':{'key':'abc'},'second':{'key':'def'}})
        administer({'action':'remove','device':'deck'},{})
        self.assertEqual(read_json(home()/'mobile-devices.json',{}),{'other':{}})
        self.assertIn('owner',read_json(home()/'mobile-trust.json',{}))
        administer({'action':'revoke','device':'owner'},{})
        self.assertEqual(read_json(home()/'mobile-trust.json',{}),{'second':{'key':'def'}})
        self.assertEqual(load_config(),self.config)

    def test_failure_after_config_replace_restores_all_metadata(self):
        atomic_json(home()/'switches.json',{'volume':True})
        def replace_then_fail(config):
            save_config(config)
            raise OSError('failure after replacement')
        with patch('ugso_usbhub.devices.save_config',side_effect=replace_then_fail):
            with self.assertRaises(OSError):administer({'action':'remove','device':'saved'},{})
        self.assertEqual(load_config(),self.config)
        self.assertEqual(read_json(home()/'switches.json',{}),{'volume':True})


class StepTests(TemporaryHome):
    def setUp(self):
        super().setUp();config=load_config()
        config['devices']['keyboard']={'enabled':True}
        config['keys']=[{**row(),'repeat':False,'step_every':3,'state':True}]
        save_config(config)
        self.pool=Mock();self.pool.send_report.return_value={'delivered':1,'matched':1,'reason':'sent','transmissions':[]}
        with patch('ugso_usbhub.core.Brokers',return_value=self.pool):self.core=Core()

    def tearDown(self):
        self.core.hardware.close();self.core.mobile.close();super().tearDown()

    def tap(self,control='KEY_VOLUMEUP'):
        self.core.event('keyboard',control,'press',1);self.core.event('keyboard',control,'release',0)

    def test_every_third_full_cycle_release_and_independent_counters(self):
        self.tap();self.tap();self.assertEqual(self.pool.send_report.call_count,0)
        self.tap();self.assertEqual([c.args[2] for c in self.pool.send_report.call_args_list],['press','release'])
        self.assertFalse(self.core.pressed);self.assertFalse(self.core.repeat_due)
        self.core.config['keys'].append({**row('KEY_BRIGHTNESSUP'),'id':'bright','repeat':False,'step_every':2})
        self.pool.reset_mock();self.tap('KEY_BRIGHTNESSUP');self.tap()
        self.assertEqual(self.pool.send_report.call_count,0)
        self.tap('KEY_BRIGHTNESSUP');self.assertEqual(self.pool.send_report.call_count,2)
        self.core.config['devices']['other']={'enabled':True}
        self.core.config['keys'].append({**row(),'id':'other-volume','device':'other','repeat':False,'step_every':2})
        self.pool.reset_mock()
        self.core.event('other','KEY_VOLUMEUP','press',1);self.core.event('other','KEY_VOLUMEUP','release',0)
        self.assertEqual(self.pool.send_report.call_count,0)
        self.core.event('other','KEY_VOLUMEUP','press',1);self.core.event('other','KEY_VOLUMEUP','release',0)
        self.assertEqual(self.pool.send_report.call_count,2)

    def test_repeated_hold_filter_stops_on_release_and_disconnect(self):
        self.core.config['keys'][0]['repeat']=True
        self.core.event('keyboard','KEY_VOLUMEUP','press',1)
        key=('keyboard','KEY_VOLUMEUP');due=self.core.repeat_due[key]
        self.core.tick(due+.001);self.core.tick(due+.152)
        self.assertEqual(self.pool.send_report.call_count,1)
        self.assertTrue(self.pool.send_report.call_args.kwargs['repeat_key'])
        self.core.event(*key,'release',0);self.core.tick(due+1)
        self.assertEqual(self.pool.send_report.call_count,1)
        self.assertFalse(self.core.repeat_due)
        self.core.release_all(disconnected=True);self.assertFalse(self.core.step_counts)

    def test_learning_does_not_advance_filter_and_settings_validation(self):
        self.core.learning={'device':'keyboard','expires':time.time()+30}
        self.tap();self.assertFalse(self.core.step_counts)
        self.core.learning={};self.tap();self.assertEqual(self.pool.send_report.call_count,0)
        for value in [0,6,True,'2']:
            config=load_config();config['keys'][0]['step_every']=value
            with self.assertRaises(ValueError):validate(config)
        for control in ['KEY_VOLUMEDOWN','KEY_BRIGHTNESSUP','KEY_BRIGHTNESSDOWN','KEY_KBDILLUMUP','KEY_KBDILLUMDOWN','KEY_KBDILLUMTOGGLE']:
            config=load_config();config['keys'][0].update(control=control,step_every=5,repeat=False)
            validate(config)

    def test_all_five_intervals_and_default_compatibility(self):
        for every in range(1,6):
            self.core.step_counts.clear();self.pool.reset_mock()
            self.core.config['keys'][0]['step_every']=every
            for _ in range(10):self.tap()
            self.assertEqual(self.pool.send_report.call_count,2*(10//every))
        self.core.config['keys'][0].pop('step_every');self.pool.reset_mock();self.tap()
        self.assertEqual(self.pool.send_report.call_count,2)


class TouchpadTests(TemporaryHome):
    def setUp(self):
        super().setUp();self.events=[];self.pad=Touchpad(lambda *e:self.events.append(e),(0,1000),(0,1000));self.clock=1

    def frame(self,points):
        self.clock+=.05
        for slot in range(4):
            self.pad.feed(EV_ABS,MT_SLOT,slot,self.clock)
            self.pad.feed(EV_ABS,MT_ID,slot if slot<len(points) else -1,self.clock)
            if slot<len(points):
                self.pad.feed(EV_ABS,MT_X,points[slot][0],self.clock)
                self.pad.feed(EV_ABS,MT_Y,points[slot][1],self.clock)
        self.pad.feed(EV_SYN,SYN_REPORT,0,self.clock)

    def names(self):return [e[0] for e in self.events if e[1]=='press']

    def test_taps_holds_and_click_suppression(self):
        self.frame([(400,400)]);self.frame([])
        self.assertEqual(self.names(),['TOUCHPAD_TAP_1'])
        self.frame([(400,400),(600,400)]);self.frame([])
        self.assertEqual(self.names()[-1],'TOUCHPAD_TAP_2')
        self.frame([(400,400)]);self.pad.tick(self.clock+.71);self.frame([])
        self.assertEqual(self.names()[-1],'TOUCHPAD_HOLD_1')
        before=len(self.events);self.frame([(400,400)])
        self.pad.feed(EV_KEY,BTN_LEFT,1,self.clock);self.pad.feed(EV_KEY,BTN_LEFT,0,self.clock)
        self.frame([]);self.assertEqual(len(self.events),before)
        self.assertEqual([e[1] for e in self.events],['press','release']*3)

    def test_scroll_pinch_and_swipe_individual_finger_lift(self):
        self.frame([(400,400),(600,400)]);self.frame([(400,500),(600,500)])
        self.frame([]);self.assertIn('TOUCHPAD_SCROLL_DOWN',self.names())
        self.frame([(400,400),(600,400)]);self.frame([(300,400),(700,400)])
        self.frame([]);self.assertIn('TOUCHPAD_PINCH_OUT',self.names())
        self.frame([(100,300),(200,300),(300,300)])
        self.frame([(400,300),(500,300),(600,300)])
        self.frame([(400,300),(500,300)]);self.frame([(400,300)]);self.frame([])
        self.assertEqual(self.names()[-1],'TOUCHPAD_SWIPE_RIGHT_3')

    def test_drop_and_noise_do_not_publish_raw_events(self):
        self.frame([(400,400)]);self.frame([(402,399)])
        self.pad.feed(EV_SYN,SYN_DROPPED,0,self.clock);self.frame([])
        self.assertEqual(self.events,[])

    def test_each_scroll_direction_and_pinch_in(self):
        for dx,dy,name in [(100,0,'RIGHT'),(-100,0,'LEFT'),(0,100,'DOWN'),(0,-100,'UP')]:
            self.frame([(400,400),(600,400)]);self.frame([(400+dx,400+dy),(600+dx,400+dy)]);self.frame([])
            self.assertEqual(self.names()[-1],'TOUCHPAD_SCROLL_'+name)
        self.frame([(300,400),(700,400)]);self.frame([(400,400),(600,400)]);self.frame([])
        self.assertEqual(self.names()[-1],'TOUCHPAD_PINCH_IN')


class InputAdapterTests(TemporaryHome):
    def test_touchpad_opt_in_and_unplug_cleanup_with_linux_adapter(self):
        from ugso_usbhub.hardware import Hardware
        observed=unit();device=Mock();device.fd=8
        device.capabilities.return_value={3:[MT_SLOT,MT_X,MT_Y,MT_ID]}
        device.input_props.return_value=[]
        device.absinfo.return_value=types.SimpleNamespace(min=0,max=1000)
        evdev=types.SimpleNamespace(InputDevice=Mock(return_value=device),ecodes=types.SimpleNamespace(EV_ABS=3,INPUT_PROP_DIRECT=1))
        config=load_config();config['devices'][observed['id']]={'enabled':True,'touchpad_gestures':True}
        hardware=Hardware(lambda *args:None)
        with patch('ugso_usbhub.hardware.inventory',return_value=[observed]),patch('ugso_usbhub.hardware.sys.platform','linux'),patch.dict('sys.modules',{'evdev':evdev}),patch.object(hardware,'_scan_decks'):
            hardware.scan(config)
            self.assertIn('/dev/input/event4',hardware.touchpads)
            config['devices'][observed['id']]['touchpad_gestures']=False;hardware.scan(config)
            self.assertFalse(hardware.touchpads)
            config['devices'][observed['id']]['touchpad_gestures']=True;hardware.scan(config)
            device.read.side_effect=OSError('unplugged')
            with patch('ugso_usbhub.hardware.select.select',return_value=([8],[],[])):hardware.poll(0)
            self.assertFalse(hardware.touchpads);self.assertFalse(hardware.inputs)
        hardware.close()


class DeviceWebTests(TemporaryHome):
    def setUp(self):
        super().setUp()
        from ugso_usbhub.web import Server
        config=load_config();config['password_hash']=password_hash('test-password-123');save_config(config)
        self.server=Server(('127.0.0.1',0));self.url='http://127.0.0.1:'+str(self.server.server_port)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();super().tearDown()
    request=fixtures.WebTests.request
    login=fixtures.WebTests.login
    def test_administration_requires_auth_and_preserves_other_settings(self):
        body={'action':'remove','device':'kbd'}
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/devices',body)
        self.assertEqual(error.exception.code,401)
        self.login();config=load_config();config['devices']['kbd']={'name':'Keyboard'};save_config(config)
        with self.request('/api/devices',body) as response:
            self.assertTrue(json.load(response)['ok'])
        self.assertNotIn('kbd',load_config()['devices'])
        self.assertEqual(load_config()['brokers'],config['brokers'])
