import copy
import json
import sys
import time
import types
from unittest.mock import Mock,patch
from tests.test_hub import TemporaryHome
from tests.broker import Broker,wait_for
from ugso_usbhub.scanner import Scanner,US,DE,ALTGR,MAX_BYTES,tag_value
from ugso_usbhub.storage import load_config,save_config,validate,home,public_config,merge_public
from ugso_usbhub.hardware import Hardware
from ugso_usbhub.mqtt import Brokers,numeric_channels
from ugso_usbhub.core import Core
from ugso_usbhub.keymap import all_bindings
from ugso_usbhub.learning import command


def settings(**values):
    return dict(name='Scanner',enabled=True,scanner_enabled=True,targets=['broker1','broker2','broker3'],**values)


def type_text(scanner,text,start=1,layout='de',terminator='KEY_ENTER'):
    now=start
    for char in text:
        key=next(((k,shift) for k,pair in (DE if layout=='de' else US).items() for shift,v in enumerate(pair) if v==char),None)
        modifier='KEY_LEFTSHIFT'
        if key is None and layout=='de':key=next(((k,1) for k,v in ALTGR.items() if v==char),None);modifier='KEY_RIGHTALT'
        assert key,char
        if key[1]:scanner.feed(modifier,1,now)
        scanner.feed(key[0],1,now);scanner.feed(key[0],0,now+.001)
        if key[1]:scanner.feed(modifier,0,now+.002)
        now+=.005
    if terminator:scanner.feed(terminator,1,now);scanner.feed(terminator,0,now+.001)
    return now


class ScannerTests(TemporaryHome):
    def test_layouts_printable_qr_leading_zeroes_and_repeated_identical_scans(self):
        for layout,text in [('de','001234567890 äÖüß zY @€ {}[]\\|~ https://www.home-assistant.io/tag/test-1'),('us','000123 zY @{}[]\\|~ https://example.org/?a=1&b=2')]:
            events=[];scanner=Scanner(lambda *e:events.append(e),settings(scanner_layout=layout))
            end=type_text(scanner,text,layout=layout)
            type_text(scanner,text,start=end+.1,layout=layout)
            self.assertEqual(events,[('_scanner_scan','scan',text)]*2)

    def test_boundaries_tab_timeout_partial_discard_and_no_repeats(self):
        events=[];scanner=Scanner(lambda *e:events.append(e),settings(scanner_terminator='tab'))
        type_text(scanner,'0012',terminator='KEY_TAB');self.assertEqual(events[-1][2],'0012')
        scanner.configure(settings(scanner_terminator='timeout',scanner_timeout_ms=200))
        end=type_text(scanner,'123',start=2,terminator=None);scanner.tick(end+.19);self.assertEqual(len(events),1)
        scanner.tick(end+.21);self.assertEqual(events[-1][2],'123')
        end=type_text(scanner,'4',start=3,terminator=None)
        type_text(scanner,'5',start=end+.3,terminator=None);scanner.tick(4)
        self.assertEqual([e[2] for e in events],['0012','123','4','5'])
        scanner.configure(settings())
        type_text(scanner,'incomplete',start=5,terminator=None);scanner.tick(6);scanner.feed('KEY_ENTER',1,6)
        scanner.feed('KEY_1',1,7);scanner.feed('KEY_1',2,7.01);scanner.feed('KEY_ENTER',1,7.02)
        self.assertEqual(events[-1][2],'1');self.assertEqual(len(events),5)
        type_text(scanner,'prefix',start=8,terminator=None);scanner.tick(9)
        type_text(scanner,'delayed-tail',start=9.1);self.assertEqual(len(events),5)
        type_text(scanner,'next',start=10);self.assertEqual(events[-1][2],'next')

    def test_invalid_overlong_scans_no_truncated_publication_and_recovery(self):
        events=[];scanner=Scanner(lambda *e:events.append(e),settings())
        for _ in range(MAX_BYTES+1):scanner.feed('KEY_1',1,1)
        scanner.feed('KEY_ENTER',1,1.1);self.assertFalse(events)
        type_text(scanner,'ok',start=2);self.assertEqual(events[-1][2],'ok')
        for bad in ('KEY_F1','BTN_LEFT','KEY_TAB','KEY_ESC'):
            type_text(scanner,'part',start=3,terminator=None);scanner.feed(bad,1,3.1)
            type_text(scanner,'tail',start=3.2);self.assertEqual(len(events),1)
        scanner.feed('KEY_LEFTCTRL',1,4);type_text(scanner,'bad',start=4.01);self.assertEqual(len(events),1)
        type_text(scanner,'partial',start=5,terminator=None);scanner.invalidate();scanner.feed('KEY_ENTER',1,5.2)
        self.assertEqual(len(events),1)
        type_text(scanner,'good',start=6);self.assertEqual(events[-1][2],'good')

    def test_caps_backspace_cancel_and_config_reset(self):
        events=[];scanner=Scanner(lambda *e:events.append(e),settings())
        scanner.feed('KEY_CAPSLOCK',1,1);scanner.feed('KEY_A',1,1.1);scanner.feed('KEY_BACKSPACE',1,1.2)
        scanner.feed('KEY_B',1,1.3);scanner.feed('KEY_ENTER',1,1.4);self.assertEqual(events[-1][2],'B')
        type_text(scanner,'partial',start=2,terminator=None)
        scanner.configure(settings(scanner_layout='us'));scanner.feed('KEY_ENTER',1,2.2);self.assertEqual(len(events),1)
        scanner.configure({'scanner_enabled':False})
        type_text(scanner,'ignored',start=3);self.assertEqual(len(events),1)

    def test_ha_url_exact_host_opt_out_and_plain_codes(self):
        for text in ('000123','https://example.org/test','https://www.home-assistant.io.evil/tag/test','https://www.home-assistant.io/tag/id?x=1'):
            self.assertEqual(tag_value(text,{}),text)
        self.assertEqual(tag_value('https://www.home-assistant.io/tag/a%20b',{}),'a b')
        url='https://www.home-assistant.io/tag/abc'
        self.assertEqual(tag_value(url,{}),'abc');self.assertEqual(tag_value(url,{'scanner_ha_urls':False}),url)
        for text in ('','line\nother','a\x00b','x'*(MAX_BYTES+1),123):
            with self.assertRaises(ValueError):tag_value(text,{})

    def test_config_topics_public_roundtrip_preserves_settings_and_existing_keys(self):
        config=load_config();config['password_hash']='retained-test-hash';config['devices']['scan']=settings();config['bindings']=[{'id':'old','device':'scan','control':'KEY_A','gesture':'press'}]
        config['devices']['other']={'name':'Other','enabled':False,'custom':'preserved'}
        save_config(config);self.assertEqual(config['devices']['scan']['scanner_topic'],'scanner-scanner/tag_scanned')
        self.assertFalse(all_bindings(config));self.assertFalse(numeric_channels(config['devices']['scan']))
        with self.assertRaises(ValueError):command({'action':'start','device':'scan'},config)
        updated=merge_public(public_config(config),config);validate(updated)
        self.assertEqual(updated['password_hash'],'retained-test-hash')
        self.assertEqual(updated['devices']['other']['custom'],'preserved')
        config['devices']['scan']['scanner_topic']='my/custom/tag';config['devices']['scan']['scanner_enabled']=False;save_config(config)
        self.assertEqual(len(all_bindings(config)),1);config['devices']['scan']['scanner_enabled']=True;save_config(config)
        self.assertEqual(load_config()['devices']['scan']['scanner_topic'],'my/custom/tag')
        for change in ({'scanner_enabled':1},{'scanner_layout':'fr'},{'scanner_terminator':'space'},{'scanner_timeout_ms':99},{'scanner_timeout_ms':3001},{'scanner_timeout_ms':True},{'scanner_topic':'bad/#'},{'scanner_ha_urls':'yes'}):
            bad=copy.deepcopy(config);bad['devices']['scan'].update(change)
            with self.assertRaises(ValueError):validate(bad)

    def test_hardware_raw_keys_isolated_disconnect_and_regular_mode_restored(self):
        events=[];hw=Hardware(lambda *e:events.append(e));device=Mock();device.fd=15
        config=load_config();config['devices']['scan']=settings();validate(config)
        found=[{'id':'scan','vendor':'1234','product_id':'5678','kind':'input','inputs':['/dev/input/event15']}]
        codes=types.SimpleNamespace(EV_ABS=3,EV_KEY=1,EV_REL=2,KEY={2:'KEY_1',28:'KEY_ENTER'},BTN={},REL={})
        evdev=types.SimpleNamespace(InputDevice=Mock(return_value=device),ecodes=codes)
        raw=[types.SimpleNamespace(type=t,code=c,value=v) for t,c,v in ((1,2,1),(1,2,0),(1,28,1),(1,28,0))]
        device.read.side_effect=lambda:iter(raw)
        with patch.object(sys,'platform','linux'),patch.dict('sys.modules',{'evdev':evdev}),patch('ugso_usbhub.hardware.inventory',return_value=found),patch('ugso_usbhub.hardware.select.select',return_value=([15],[],[])),patch.object(hw,'_scan_decks'):
            hw.scan(config);hw.poll();self.assertEqual(events,[('scan','_scanner_scan','scan','1')])
            hw.scanners['/dev/input/event15'].feed('KEY_2',1,time.monotonic())
            found.clear();hw.scan(config);self.assertFalse(hw.scanners)
            found.append({'id':'scan','kind':'input','inputs':['/dev/input/event15']})
            hw.scan(config);self.assertEqual(hw.scanners['/dev/input/event15'].text,'')
            config['devices']['scan']['scanner_enabled']=False;hw.scan(config);hw.poll()
            self.assertIn(('scan','KEY_1','press',1),events);self.assertFalse(hw.scanners)
        hw.close()


class ScannerMqttTests(TemporaryHome):
    def test_three_real_brokers_native_tag_discovery_repeated_scans_cleanup_and_no_key_actions(self):
        servers=[Broker() for _ in range(3)];pool=None;core=None
        try:
            config=load_config();config['devices']['scan']=settings()
            config['bindings']=[{'id':'old','device':'scan','control':'KEY_A','gesture':'press','topic':'must/not/send'}]
            for b,s in zip(config['brokers'],servers):b.update(enabled=True,host='127.0.0.1',port=s.port,discovery=b['id']!='broker2')
            save_config(config);before=(home()/'config.json').read_bytes();pool=Brokers(config,lambda *e:None)
            wait_for(lambda:all(pool.states.get(b['id'])=='online' for b in config['brokers']))
            tag=f"homeassistant/tag/ugso_{config['hub_id']}_scan/config"
            wait_for(lambda:any(t==tag for t,p,r in servers[0].messages))
            payload=json.loads(next(p for t,p,r in servers[0].messages if t==tag))
            self.assertEqual(payload['topic'],'scanner-scanner/tag_scanned');self.assertEqual(payload['device']['identifiers'],[f"ugso_{config['hub_id']}_scan"])
            self.assertFalse(any(t.startswith('homeassistant/') for t,p,r in servers[1].messages))
            with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
            core.event('scan','KEY_A','press',1)
            decoder=Scanner(lambda control,gesture,value:core.event('scan',control,gesture,value),config['devices']['scan'])
            for index,text in enumerate(('000123','000123','https://www.home-assistant.io/tag/alarm-test')):
                type_text(decoder,text,start=1+index)
            wait_for(lambda:all(len([m for m in s.messages if m[0]==payload['topic']])==3 for s in servers))
            for s in servers:
                messages=[m for m in s.messages if m[0]==payload['topic']]
                self.assertEqual([p for t,p,r in messages],[b'000123',b'000123',b'alarm-test']);self.assertTrue(all(not r for t,p,r in messages))
                self.assertFalse(any(t=='must/not/send' for t,p,r in s.messages))
            core.learning={'device':'scan','expires':time.time()+10};count=len(core.events)
            core.event('scan','_scanner_scan','scan','muted');self.assertEqual(len(core.events),count)
            core.learning={};core.event('scan','_scanner_scan','scan','bad\x00code');self.assertEqual(len(core.events),count)
            self.assertEqual((home()/'config.json').read_bytes(),before)
            replacement=copy.deepcopy(config);replacement['devices']['scan']['scanner_enabled']=False;pool.cleanup_removed(replacement)
            wait_for(lambda:any(t==tag and p==b'' for t,p,r in servers[0].messages))
            pool.config=replacement;self.assertEqual(pool.send_scan('scan','no')['delivered'],0)
            pool.config=config;pool.sync_discovery(config['brokers'][0])
            wait_for(lambda:len([m for m in servers[0].messages if m[0]==tag and m[1]])>=2)
            config['devices']['scan']['targets']=['broker3'];self.assertEqual(pool.send_scan('scan','one')['delivered'],1)
            servers[2].close();wait_for(lambda:pool.states['broker3']=='offline');self.assertEqual(pool.send_scan('scan','offline')['delivered'],0)
        finally:
            if pool:pool.close()
            if core:core.hardware.close();core.mobile.close()
            for s in servers:s.close()
