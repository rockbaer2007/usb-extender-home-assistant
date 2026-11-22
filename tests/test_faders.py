import copy
import json
import time
from unittest.mock import patch
from tests.test_hub import TemporaryHome
from tests.test_slide import Input
from tests.broker import Broker,wait_for
from ugso_usbhub.storage import load_config,save_config,home,validate
from ugso_usbhub.mqtt import Brokers
from ugso_usbhub.core import Core
from ugso_usbhub.touchpad import EV_KEY,EV_SYN,SYN_DROPPED,BTN_LEFT


class FaderInputTests(TemporaryHome):
    def test_five_locked_lanes_both_directions_and_no_slide_or_tap(self):
        for lane in range(1,6):
            for start,end,expected in ((1000,0,100),(0,1000,0)):
                source=Input({'touchpad_mode':'faders'})
                source.frame([((lane-1)*200+100,start)],1)
                source.frame([(1000 if lane<5 else 0,500)],1.2)
                source.frame([(0 if lane<5 else 1000,end)],1.4)
                source.frame([],1.5)
                values=[e[3] for e in source.events if e[1]=='_touchpad_fader_value']
                self.assertEqual(values,[[lane,50],[lane,expected]])
                self.assertFalse(source.positions());self.assertFalse(source.actions())

    def test_boundaries_retouch_and_vertical_activation(self):
        for x,lane in ((-30,1),(0,1),(199,1),(200,2),(400,3),(600,4),(800,5),(1000,5),(1020,5)):
            source=Input({'touchpad_mode':'faders'})
            source.frame([(x,500)],1);source.frame([(x,100)],1.2)
            self.assertEqual([e[3] for e in source.events if e[1]=='_touchpad_fader_value'],[[lane,90]])
        source=Input({'touchpad_mode':'faders'})
        source.frame([(100,500)],1);source.frame([(900,500)],1.2);source.frame([],1.3)
        self.assertFalse(source.events)
        source.frame([(900,800)],2);source.frame([(900,100)],2.2)
        self.assertEqual(source.events[-1][3],[5,90])

    def test_rate_final_coalescing_xy_optional_and_cancellations(self):
        for rate in (1,5,30):
            source=Input({'touchpad_mode':'faders','touchpad_xy':True,'touchpad_rate':rate,'touchpad_sensitivity':10})
            source.frame([(500,1000)],1)
            for n in range(1,101):source.frame([(500,1000-10*n)],1+n*.01)
            source.frame([],2.1);source.tick(3.2)
            rows=[e for e in source.events if e[1]=='_touchpad_fader_value']
            self.assertTrue(source.positions());self.assertEqual(rows[-1][3],[3,100])
            self.assertTrue(all(b[0]-a[0]>=1/rate-1e-8 for a,b in zip(rows,rows[1:])))
        for reason in ('multi','click','drop','mode'):
            source=Input({'touchpad_mode':'faders','touchpad_rate':1})
            source.frame([(500,900)],1);source.frame([(500,700)],1.1);source.frame([(500,500)],1.2)
            if reason=='multi':source.frame([(500,500),(600,500)],1.3)
            elif reason=='click':source.pad.feed(EV_KEY,BTN_LEFT,1,1.3)
            elif reason=='drop':source.pad.feed(EV_SYN,SYN_DROPPED,0,1.3)
            else:source.pad.configure({'touchpad_mode':'directions'})
            source.tick(4)
            self.assertEqual(len([e for e in source.events if e[1]=='_touchpad_fader_value']),1)

    def test_disabled_lane_and_back_to_directions(self):
        source=Input({'touchpad_mode':'faders','touchpad_faders':{'1':{'enabled':False}}})
        source.frame([(100,900)],1);source.frame([(100,100)],1.2);source.frame([],1.3)
        self.assertFalse(source.events)
        source.pad.configure({'touchpad_mode':'directions'})
        source.frame([(100,900)],2);source.frame([(900,900)],2.2)
        self.assertIn('TOUCHPAD_SLIDE_RIGHT',source.actions())
        self.assertFalse(any(e[1]=='_touchpad_fader_value' for e in source.events))

    def test_config_compatibility_topics_and_invalid_settings(self):
        config=load_config();config['devices']['pad']={'name':'T650','touchpad_mode':'faders',
            'touchpad_xy':True,'touchpad_x_topic':'T650-X','touchpad_y_topic':'T650-Y',
            'touchpad_slide_values':{'UP':{'enabled':True,'topic':'custom/up'}}}
        save_config(config);first=copy.deepcopy(config['devices']['pad'])
        self.assertEqual(len(first['touchpad_faders']),5)
        self.assertEqual(first['touchpad_faders']['3']['topic'],'t650-touchpad/fader-3/value')
        first['touchpad_faders']['3']['topic']='custom/fader/3'
        config['devices']['pad']=first;save_config(config)
        config['devices']['pad']['touchpad_mode']='directions';save_config(config)
        restored=load_config()['devices']['pad'];self.assertEqual(restored['touchpad_faders']['3']['topic'],'custom/fader/3')
        self.assertEqual(restored['touchpad_slide_values']['UP']['topic'],'custom/up')
        self.assertEqual(restored['touchpad_x_topic'],'T650-X')
        for changes in ({'touchpad_mode':'wrong'},{'touchpad_faders':[]},{'touchpad_faders':{'6':{}}},
                        {'touchpad_faders':{'1':{'enabled':'true'}}},{'touchpad_faders':{'1':{'topic':'x/#'}}},
                        {'touchpad_faders':{'1':{'topic':'same'},'2':{'topic':'same'}}},
                        {'touchpad_faders':{'1':{'topic':'T650-X'}}}):
            invalid=copy.deepcopy(config);invalid['devices']['pad'].update(touchpad_mode='faders',**changes) if 'touchpad_mode' not in changes else invalid['devices']['pad'].update(changes)
            with self.assertRaises(ValueError):validate(invalid)


class FaderMqttTests(TemporaryHome):
    def test_real_mqtt_core_learning_discovery_switch_and_restart(self):
        servers=[Broker() for _ in range(3)];pool=None;core=None
        try:
            config=load_config()
            for broker,server in zip(config['brokers'],servers):broker.update(enabled=True,host='127.0.0.1',port=server.port,discovery=broker['id']!='broker2')
            config['devices']['pad']={'name':'T650','enabled':True,'touchpad_gestures':True,'touchpad_xy':True,
                'targets':['broker1','broker2','broker3'],'touchpad_mode':'directions',
                'touchpad_slide_values':{'UP':{'enabled':True,'topic':'custom/up'}}}
            config['keys']=[{'id':'old','device':'pad','control':'TOUCHPAD_SLIDE_UP','name':'Old up','press':True,'release':True,'switch':True}]
            save_config(config);pool=Brokers(config,lambda *a:None)
            wait_for(lambda:pool.states.get('broker1')=='online')
            wait_for(lambda:any(t.startswith('homeassistant/device_automation/') for t,p,r in servers[0].messages))
            old_ids={t:json.loads(p)['unique_id'] for t,p,r in servers[0].messages if t.startswith('homeassistant/sensor/') and p}
            replacement=copy.deepcopy(config);replacement['devices']['pad']['touchpad_mode']='faders';save_config(replacement)
            pool.cleanup_removed(replacement);pool.close();pool=Brokers(load_config(),lambda *a:None)
            wait_for(lambda:all(pool.states.get(b['id'])=='online' for b in config['brokers']))
            def sensors(server):return {t:p for t,p,r in server.messages if t.startswith('homeassistant/sensor/')}
            wait_for(lambda:len([p for p in sensors(servers[0]).values() if p])==7)
            self.assertFalse(any(t.startswith('homeassistant/sensor/') for t,p,r in servers[1].messages))
            self.assertTrue(all(not p for t,p in {t:p for t,p,r in servers[0].messages if t.startswith('homeassistant/device_automation/') or t.startswith('homeassistant/binary_sensor/')}.items()))
            before=(home()/'config.json').read_bytes()
            with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
            core.learning={'device':'pad','expires':time.time()+30}
            core.event('pad','_touchpad_fader_value','value',[2,55])
            self.assertFalse(any(t.endswith('fader-2/value') for t,p,r in servers[0].messages))
            core.learning={}
            for lane in range(1,6):
                source=Input(replacement['devices']['pad'],lambda *e:core.event('pad',*e))
                source.frame([((lane-1)*200+100,900)],1);source.frame([((lane-1)*200+100,100)],1.2)
            wait_for(lambda:all(len([t for t,p,r in s.messages if '/fader-' in t])==5 for s in servers))
            for server in servers:
                rows=[(t,p,r) for t,p,r in server.messages if '/fader-' in t]
                self.assertTrue(all(p==b'90' and not r for t,p,r in rows))
            self.assertEqual(pool.send_slide_value('pad','UP',55)['delivered'],0)
            self.assertEqual(pool.send_report('pad','TOUCHPAD_SLIDE_UP','press')['reason'],'mode_inactive')
            core.config['devices']['pad']['targets']=['broker3'];pool.config=core.config
            self.assertEqual(pool.send_fader_value('pad',3,72)['delivered'],1)
            self.assertTrue(any(e['control']=='TOUCHPAD_FADER_3' and e['value']==90 for e in core.events))
            self.assertEqual((home()/'config.json').read_bytes(),before)
            back=copy.deepcopy(replacement);back['devices']['pad']['touchpad_mode']='directions';validate(back)
            pool.cleanup_removed(back);pool.close();pool=None
            save_config(back);pool=Brokers(load_config(),lambda *a:None)
            wait_for(lambda:pool.states.get('broker1')=='online')
            wait_for(lambda:all(not p for t,p in sensors(servers[0]).items() if '_fader_' in t))
            wait_for(lambda:any(t.startswith('homeassistant/device_automation/') and p for t,p,r in servers[0].messages[-20:]))
            latest={t:json.loads(p)['unique_id'] for t,p in sensors(servers[0]).items() if p}
            self.assertEqual(latest,old_ids)
            self.assertEqual(load_config()['devices']['pad']['touchpad_faders'],replacement['devices']['pad']['touchpad_faders'])
        finally:
            if pool:pool.close()
            if core:core.hardware.close();core.mobile.close()
            for server in servers:server.close()
