"""Local synthetic MT input and real loopback MQTT for one-finger slide."""
import copy
import time
from unittest.mock import Mock, patch
from tests.test_hub import TemporaryHome
from tests.broker import Broker, wait_for
from ugso_usbhub.touchpad import Touchpad, EV_ABS, EV_SYN, EV_KEY, MT_SLOT, MT_ID, MT_X, MT_Y, SYN_REPORT, SYN_DROPPED, BTN_LEFT
from ugso_usbhub.storage import load_config, save_config, validate, home, merge_public, public_config
from ugso_usbhub.mqtt import Brokers
from ugso_usbhub.core import Core


class Input:
    def __init__(self, options=None, emit=None):
        self.now=0.;self.events=[]
        def record(*event):
            self.events.append((self.now,*event))
            if emit:emit(*event)
        self.pad=Touchpad(record,(0,1000),(0,1000),options)

    def frame(self, points, now):
        self.now=now
        for slot in range(4):
            self.pad.feed(EV_ABS,MT_SLOT,slot,now)
            self.pad.feed(EV_ABS,MT_ID,slot if slot<len(points) else -1,now)
            if slot<len(points):
                self.pad.feed(EV_ABS,MT_X,points[slot][0],now)
                self.pad.feed(EV_ABS,MT_Y,points[slot][1],now)
        self.pad.feed(EV_SYN,SYN_REPORT,0,now)

    def tick(self, now):self.now=now;self.pad.tick(now)
    def actions(self):return [e[1] for e in self.events if e[2]=='press']
    def positions(self):return [e for e in self.events if e[1]=='_touchpad_position']


class SlideTests(TemporaryHome):
    def test_diagonals_and_reverse_do_not_emit_cardinal_actions_or_taps(self):
        for dx,dy,name in [(150,150,'DOWN_RIGHT'),(-150,-150,'UP_LEFT'),(-150,150,'DOWN_LEFT'),(150,-150,'UP_RIGHT')]:
            source=Input({'touchpad_xy':True})
            source.frame([(500,500)],1);source.frame([(500+dx,500+dy)],1.05);source.frame([],1.1)
            self.assertEqual(source.actions(),['TOUCHPAD_SLIDE_'+name])
            self.assertEqual(source.positions()[-1][3],[round((500+dx)/10),round((500+dy)/10)])

    def test_eight_sector_classification_tolerates_small_axis_deviation(self):
        from ugso_usbhub.touchpad import slide_direction
        for vector,name in [((100,30),'RIGHT'),((30,100),'DOWN'),((-100,30),'LEFT'),((30,-100),'UP'),
                            ((100,50),'DOWN_RIGHT'),((-100,50),'DOWN_LEFT'),((100,-50),'UP_RIGHT'),((-100,-50),'UP_LEFT')]:
            self.assertEqual(slide_direction(*vector),name)

    def test_four_directions_are_learnable_press_release_pairs_without_tap(self):
        for dx,dy,name in [(100,0,'RIGHT'),(-100,0,'LEFT'),(0,100,'DOWN'),(0,-100,'UP')]:
            source=Input();source.frame([(500,500)],1);source.frame([(500+dx,500+dy)],1.05)
            source.frame([],1.1)
            self.assertEqual(source.actions(),['TOUCHPAD_SLIDE_'+name])
            self.assertEqual([e[2:] for e in source.events],[('press',1),('release',0)])
            self.assertEqual(source.positions(),[])

    def test_sensitivity_and_return_to_origin_do_not_generate_tap(self):
        slow=Input({'touchpad_sensitivity':1});fast=Input({'touchpad_sensitivity':10})
        for source in (slow,fast):
            source.frame([(500,500)],1);source.frame([(530,500)],1.05);source.frame([(500,500)],1.16);source.frame([],1.2)
        self.assertEqual(slow.actions(),[])
        self.assertEqual(fast.actions(),['TOUCHPAD_SLIDE_RIGHT','TOUCHPAD_SLIDE_LEFT'])
        tap=Input();tap.frame([(500,500)],2);tap.frame([],2.1)
        self.assertEqual(tap.actions(),['TOUCHPAD_TAP_1'])

    def test_rates_one_five_and_thirty_limit_directions_and_coordinates(self):
        for rate in (1,5,30):
            source=Input({'touchpad_sensitivity':10,'touchpad_rate':rate,'touchpad_xy':True})
            source.frame([(0,500)],1)
            for i in range(1,101):source.frame([(i*10,500)],1+i*.01)
            for events in ([e for e in source.events if e[2]=='press'],source.positions()):
                self.assertTrue(events)
                self.assertLessEqual(len(events),rate+1)
                self.assertTrue(all(b[0]-a[0]>=1/rate-1e-9 for a,b in zip(events,events[1:])))
            source.tick(3);before=len(source.events);source.tick(4);source.tick(5)
            self.assertEqual(len(source.events),before,'no unchanged retransmission')

    def test_position_clamping_final_value_and_drop_cancel(self):
        source=Input({'touchpad_xy':True,'touchpad_rate':1})
        source.frame([(500,500)],1);source.frame([(800,500)],1.1)
        self.assertEqual(source.positions()[-1][3],[80,50])
        source.frame([(1200,-100)],1.15);source.frame([],1.2)
        source.tick(2.11)
        self.assertEqual(source.positions()[-1][3],[100,0])
        self.assertEqual(len(source.positions()),2)
        self.assertFalse(any('TAP' in a for a in source.actions()))
        source.frame([(500,500)],3);source.frame([(900,900)],3.1)
        source.frame([(1000,1000)],3.2)
        source.pad.feed(EV_SYN,SYN_DROPPED,0,3.3)
        before=len(source.events);source.tick(5);self.assertEqual(len(source.events),before)

    def test_second_finger_and_mechanical_click_cancel_pending_xy(self):
        for mechanical in (False,True):
            source=Input({'touchpad_xy':True,'touchpad_rate':1})
            source.frame([(300,300)],1);source.frame([(400,300)],1.1)
            source.frame([(500,300)],1.2)
            if mechanical:source.pad.feed(EV_KEY,BTN_LEFT,1,1.21)
            else:source.frame([(500,300),(700,300)],1.21)
            before=len(source.positions());source.tick(3)
            self.assertEqual(len(source.positions()),before)
        two=Input({'touchpad_xy':True});two.frame([(200,200),(400,200)],4)
        two.frame([(200,400),(400,400)],4.1);two.frame([],4.2)
        self.assertEqual(two.positions(),[])
        self.assertEqual(two.actions(),['TOUCHPAD_SCROLL_DOWN'])

    def test_configuration_change_discards_pending_state(self):
        source=Input({'touchpad_xy':True,'touchpad_rate':1})
        source.frame([(300,300)],1);source.frame([(400,300)],1.1);source.frame([(500,300)],1.2)
        before=len(source.events);source.pad.configure({'touchpad_xy':False,'touchpad_rate':1})
        source.tick(3);self.assertEqual(len(source.events),before)


class SlideConfigTests(TemporaryHome):
    def test_settings_and_topics_survive_save_and_secret_merge(self):
        config=load_config();config['brokers'][0]['password']='keep-existing'
        config['devices']['pad']={'name':'Büro T650','enabled':True,'targets':['broker2'],
            'touchpad_gestures':True,'touchpad_xy':True,'touchpad_sensitivity':7,'touchpad_rate':12}
        save_config(config);saved=load_config()
        self.assertEqual(saved['devices']['pad']['touchpad_x_topic'],'buero-t650-touchpad/x')
        self.assertEqual(saved['devices']['pad']['touchpad_y_topic'],'buero-t650-touchpad/y')
        self.assertEqual(merge_public(public_config(saved),saved),saved)
        saved['devices']['pad']['name']='Renamed';save_config(saved)
        self.assertEqual(load_config()['devices']['pad']['touchpad_x_topic'],'buero-t650-touchpad/x')
        self.assertEqual(load_config()['brokers'][0]['password'],'keep-existing')

    def test_invalid_settings_and_topic_collisions_rejected(self):
        for changes in [{'touchpad_sensitivity':0},{'touchpad_sensitivity':11},{'touchpad_rate':0},
                        {'touchpad_rate':31},{'touchpad_rate':True},{'touchpad_rate':2.5},
                        {'touchpad_xy':'yes'},{'touchpad_x_topic':'bad/#'},
                        {'touchpad_x_topic':'same','touchpad_y_topic':'same'}]:
            config=load_config();config['devices']['pad']={'touchpad_xy':True,**changes}
            with self.assertRaises(ValueError):validate(config)

    def test_core_suppresses_xy_during_learning_and_learns_direction_only(self):
        config=load_config();config['devices']['pad']={'enabled':True,'touchpad_gestures':True,'touchpad_xy':True}
        save_config(config);pool=Mock()
        pool.send_position.return_value={'delivered':2,'matched':2,'reason':'sent','transmissions':[]}
        pool.send_report.return_value={'delivered':0,'matched':0,'reason':'no_binding','transmissions':[]}
        with patch('ugso_usbhub.core.Brokers',return_value=pool):core=Core()
        try:
            core.learning={'device':'pad','id':'learn','expires':time.time()+30}
            source=Input({'touchpad_xy':True},lambda *e:core.event('pad',*e))
            source.frame([(300,300)],1);source.frame([(500,300)],1.1);source.frame([],1.2)
            pool.send_position.assert_not_called();pool.send_report.assert_not_called()
            self.assertTrue(any(e['control']=='TOUCHPAD_SLIDE_RIGHT' and e['learning_id']=='learn' for e in core.events))
            core.learning={};source.frame([(300,300)],2);source.frame([(600,400)],2.1)
            pool.send_position.assert_called_once_with('pad',60,40)
            self.assertFalse(core.pressed.get(('pad','_touchpad_position')))
        finally:core.hardware.close();core.mobile.close()


class SlideMqttTests(TemporaryHome):
    def setUp(self):
        super().setUp();self.servers=[Broker() for _ in range(3)];self.config=load_config()
        for broker,server in zip(self.config['brokers'],self.servers):
            broker.update(enabled=True,host='127.0.0.1',port=server.port,discovery=False)
        self.config['devices']['pad']={'name':'T650','enabled':True,'touchpad_gestures':True,'touchpad_xy':True,
            'targets':['broker1','broker2','broker3']}
        self.config['keys']=[{'id':'slide','device':'pad','control':'TOUCHPAD_SLIDE_RIGHT','name':'Right',
            'press':True,'release':True,'switch':False,'press_topic':'t650-slide/right','release_topic':'t650-slide/right-release'}]
        save_config(self.config);self.before=(home()/'config.json').read_bytes()
        self.pool=Brokers(self.config,lambda *args:None)
        wait_for(lambda:len(self.pool.states)==3 and all(s=='online' for s in self.pool.states.values()))

    def tearDown(self):
        self.pool.close()
        for server in self.servers:server.close()
        super().tearDown()

    def test_real_mqtt_plain_values_all_three_brokers_and_slide_action(self):
        with patch('ugso_usbhub.core.Brokers',return_value=self.pool):core=Core()
        try:
            source=Input({'touchpad_xy':True},lambda *e:core.event('pad',*e))
            source.frame([(300,300)],1);source.frame([(800,500)],1.1);source.frame([],1.2)
            wait_for(lambda:all(any(m[0]=='t650-touchpad/y' for m in s.messages) for s in self.servers))
            for server in self.servers:
                values={topic:payload.decode() for topic,payload,retain in server.messages}
                self.assertEqual(values['t650-touchpad/x'],'80');self.assertEqual(values['t650-touchpad/y'],'50')
                self.assertEqual(values['t650-slide/right'],'press')
                self.assertEqual(values['t650-slide/right-release'],'release')
                self.assertTrue(all(not m[2] for m in server.messages if 't650-' in m[0]))
            self.assertEqual((home()/'config.json').read_bytes(),self.before)
        finally:core.hardware.close();core.mobile.close()

    def test_routing_opt_out_and_offline_broker(self):
        self.config['devices']['pad']['targets']=['broker2','broker3']
        report=self.pool.send_position('pad',0,100)
        self.assertEqual(report['delivered'],4)
        wait_for(lambda:any(m[0]=='t650-touchpad/y' for m in self.servers[1].messages))
        self.assertFalse(any(m[0]=='t650-touchpad/x' for m in self.servers[0].messages))
        self.servers[1].close();wait_for(lambda:self.pool.states['broker2']=='offline')
        self.assertEqual(self.pool.send_position('pad',22,33)['delivered'],2)
        self.config['devices']['pad']['touchpad_xy']=False
        self.assertEqual(self.pool.send_position('pad',99,99)['delivered'],0)
