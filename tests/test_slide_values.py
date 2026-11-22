"""Eight absolute directional values and retained HA sensor lifecycle, loopback only."""
import copy
import json
from unittest.mock import patch
from tests.test_hub import TemporaryHome
from tests.test_slide import Input
from tests.broker import Broker, wait_for
from ugso_usbhub.touchpad import SLIDE_DIRECTIONS, SYN_DROPPED, EV_SYN, EV_KEY, BTN_LEFT
from ugso_usbhub.storage import load_config, save_config, validate
from ugso_usbhub.mqtt import Brokers
from ugso_usbhub.core import Core


def options():
    return {'touchpad_slide_values':{d:{'enabled':True,'topic':'t650/'+d.lower()} for d in SLIDE_DIRECTIONS}}


class DirectionValueTests(TemporaryHome):
    def test_eight_directions_absolute_endpoints_and_no_tap(self):
        paths={'UP':((500,1000),(500,0),100),'DOWN':((500,0),(500,1000),0),
               'RIGHT':((0,500),(1000,500),100),'LEFT':((1000,500),(0,500),0),
               'UP_RIGHT':((0,1000),(1000,0),100),'DOWN_LEFT':((1000,0),(0,1000),0),
               'DOWN_RIGHT':((0,0),(1000,1000),100),'UP_LEFT':((1000,1000),(0,0),0)}
        for direction,(start,end,expected) in paths.items():
            source=Input(options());source.frame([start],1)
            midpoint=tuple(round((a+b)/2) for a,b in zip(start,end))
            source.frame([midpoint],1.2);source.frame([end],1.4);source.frame([],1.5)
            values=[e for e in source.events if e[1]=='_touchpad_slide_value']
            self.assertEqual([(e[2],e[3]) for e in values],[(direction,50),(direction,expected)])
            self.assertFalse(any('TAP' in name for name in source.actions()))
            self.assertFalse(source.positions())

    def test_opt_in_short_slide_and_rate_coalescing(self):
        source=Input();source.frame([(500,500)],1);source.frame([(600,500)],1.1)
        self.assertFalse(any(e[1]=='_touchpad_slide_value' for e in source.events))
        config=options();config['touchpad_rate']=1
        source=Input(config);source.frame([(500,500)],1);source.frame([(600,500)],1.1)
        source.frame([(700,500)],1.2);source.frame([],1.3);source.tick(2.11)
        values=[e for e in source.events if e[1]=='_touchpad_slide_value']
        self.assertEqual([e[3] for e in values],[60,70])
        self.assertGreaterEqual(values[1][0]-values[0][0],1)
        source.tick(4);self.assertEqual(len([e for e in source.events if e[1]=='_touchpad_slide_value']),2)

    def test_pending_cancel_on_multitouch_drop_and_settings_change(self):
        for reason in ('multi','drop','configure','click'):
            config={**options(),'touchpad_rate':1};source=Input(config)
            source.frame([(500,500)],1);source.frame([(600,500)],1.1);source.frame([(700,500)],1.2)
            if reason=='multi':source.frame([(700,500),(800,500)],1.3)
            elif reason=='drop':source.pad.feed(EV_SYN,SYN_DROPPED,0,1.3)
            elif reason=='click':source.pad.feed(EV_KEY,BTN_LEFT,1,1.3)
            else:
                config['touchpad_slide_values']['RIGHT']['enabled']=False
                source.pad.configure(config)
            source.tick(3)
            self.assertEqual(len([e for e in source.events if e[1]=='_touchpad_slide_value']),1)

    def test_all_rate_limits_and_disabled_directions(self):
        for rate in (1,5,30):
            config={**options(),'touchpad_rate':rate,'touchpad_sensitivity':10}
            config['touchpad_slide_values']['LEFT']['enabled']=False
            source=Input(config);source.frame([(0,500)],1)
            for n in range(1,101):source.frame([(n*10,500)],1+n/100)
            values=[e for e in source.events if e[1]=='_touchpad_slide_value']
            self.assertTrue(values)
            self.assertTrue(all(b[0]-a[0]>=1/rate-1e-8 for a,b in zip(values,values[1:])))
            before=len(values)
            for n in range(1,101):source.frame([(1000-n*10,500)],3+n/100)
            self.assertEqual(len([e for e in source.events if e[1]=='_touchpad_slide_value']),before)

    def test_config_roundtrip_migration_and_validation(self):
        config=load_config();config['devices']['pad']={'name':'T650',**options(),'touchpad_xy':True}
        config['devices']['pad']['touchpad_slide_values']['UP']['topic']=''
        save_config(config);saved=load_config()
        self.assertEqual(saved['devices'],config['devices'])
        self.assertEqual(saved['devices']['pad']['touchpad_slide_values']['UP']['topic'],'t650-touchpad/slide-up/value')
        for changes in ({'UP':{'enabled':'yes'}},{'OTHER':{}},{'UP':{'topic':'x/#'}},[],{'UP':{'enabled':True,'topic':'same'},'DOWN':{'enabled':True,'topic':'same'}}):
            invalid=copy.deepcopy(config);invalid['devices']['pad']['touchpad_slide_values']=changes
            with self.assertRaises(ValueError):validate(invalid)


class ValueDiscoveryTests(TemporaryHome):
    def test_real_three_brokers_discovery_routing_cleanup_and_restart(self):
        servers=[Broker() for _ in range(3)];pool=None
        try:
            config=load_config()
            for broker,server in zip(config['brokers'],servers):broker.update(enabled=True,host='127.0.0.1',port=server.port,discovery=broker['id']!='broker2')
            config['devices']['pad']={'name':'T650','enabled':True,'touchpad_gestures':True,'touchpad_xy':True,
                'targets':['broker1','broker2','broker3'],**options()}
            save_config(config);pool=Brokers(config,lambda *a:None)
            prefix='homeassistant/sensor/'
            wait_for(lambda:all(pool.states.get(b['id'])=='online' for b in config['brokers']))
            wait_for(lambda:all(len([m for m in servers[i].messages if m[0].startswith(prefix)])>=10 for i in (0,2)))
            self.assertFalse(any(m[0].startswith(prefix) for m in servers[1].messages))
            sensors={t:json.loads(p) for t,p,r in servers[0].messages if t.startswith(prefix)}
            self.assertEqual(len(sensors),10)
            self.assertEqual(len({v['unique_id'] for v in sensors.values()}),10)
            self.assertTrue(all(v['device']['identifiers']==[f"ugso_{config['hub_id']}_pad"] for v in sensors.values()))
            self.assertTrue(all(r for t,p,r in servers[0].messages if t.startswith(prefix)))
            count=len([m for m in servers[0].messages if m[0].startswith(prefix)])
            servers[0].publish('homeassistant/status','online')
            wait_for(lambda:len([m for m in servers[0].messages if m[0].startswith(prefix)])>=count+10)
            with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
            try:
                source=Input(options(),lambda *e:core.event('pad',*e))
                source.frame([(500,1000)],1);source.frame([(500,0)],1.2);source.frame([],1.3)
                wait_for(lambda:all(any(t=='t650/up' and p==b'100' and not r for t,p,r in s.messages) for s in servers))
                core.learning={'device':'pad','expires':__import__('time').time()+60}
                before=sum(len(s.messages) for s in servers)
                core.event('pad','_touchpad_slide_value','UP',42)
                self.assertEqual(sum(len(s.messages) for s in servers),before)
            finally:core.hardware.close();core.mobile.close()
            pool.send_position('pad',58,37)
            wait_for(lambda:all(any(t=='t650-touchpad/x' and p==b'58' for t,p,r in s.messages) for s in servers))
            changed=copy.deepcopy(config);changed['devices']['pad']['touchpad_xy']=False
            changed['devices']['pad']['touchpad_slide_values']['UP']['enabled']=False
            pool.cleanup_removed(changed)
            wait_for(lambda:len([m for m in servers[0].messages if m[0].startswith(prefix) and m[1]==b''])==3)
            pool.close();pool=None
            save_config(changed);pool=Brokers(load_config(),lambda *a:None)
            wait_for(lambda:all(pool.states.get(b['id'])=='online' for b in config['brokers']))
            pool.sync_discovery(changed['brokers'][0])
            last={t:p for t,p,r in servers[0].messages if t.startswith(prefix)}
            self.assertEqual(len([p for p in last.values() if p]),7)
            changed['devices']['pad']['targets']=['broker1'];pool.config=changed
            self.assertEqual(pool.send_slide_value('pad','RIGHT',75)['delivered'],1)
            self.assertEqual(pool.send_slide_value('pad','UP',75)['delivered'],0)
            disabled=copy.deepcopy(changed);disabled['brokers'][0]['discovery']=False
            pool.cleanup_removed(disabled)
            wait_for(lambda:all(p==b'' for t,p in {t:p for t,p,r in servers[0].messages if t.startswith(prefix)}.items()))
            servers[0].close();wait_for(lambda:pool.states['broker1']=='offline')
            self.assertEqual(pool.send_slide_value('pad','RIGHT',75)['delivered'],0)
        finally:
            if pool:pool.close()
            for server in servers:server.close()
