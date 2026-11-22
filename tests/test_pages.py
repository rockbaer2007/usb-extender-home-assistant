"""Device-isolated deck pages, stable mappings, navigation edges and rendering."""
import copy
import io
from unittest.mock import patch
from PIL import Image
from tests.test_hub import TemporaryHome
from ugso_usbhub.storage import load_config,save_config,validate,home
from ugso_usbhub.keymap import ensure_deck_keys,all_bindings
from ugso_usbhub.core import Core
from ugso_usbhub.deck import key_image


class Deck:
    def __init__(self):self.images={};self.writes=0
    def key_count(self):return 6
    def connected(self):return True
    def is_visual(self):return True
    def set_brightness(self,value):pass
    def key_image_format(self):return {'size':(72,72),'format':'PNG','rotation':0,'flip':(False,False)}
    def set_key_image(self,key,image):self.images[key]=image;self.writes+=1
    def close(self):pass


class Recorder:
    def __init__(self):self.calls=[];self.states={};self.discovery_errors={}
    def send_report(self,*args,**kwargs):
        self.calls.append((args,kwargs));return {'delivered':0,'matched':0,'reason':'no_targets','transmissions':[]}
    def close(self):pass
    def flush_resets(self,now):pass


class PageTests(TemporaryHome):
    def setUp(self):
        super().setUp();config=load_config()
        for ident in ['tablet','phone']:
            config['devices'][ident]={'name':ident,'enabled':True,'targets':['broker1'],'deck_page_count':3,'deck_keys':{}}
            for page in range(3):
                config['devices'][ident]['deck_keys'][str(page*128)]={'background':['#ff0000','#0000ff','#00ff00'][page]}
                for slot,action in [(3,'previous'),(4,'next'),(5,'home')]:
                    config['devices'][ident]['deck_keys'][str(page*128+slot)]={'action':action,'show_page':True}
        config['bindings']=[{'id':'old','device':'tablet','control':'key:0','gesture':'press','topic':'keep/topic','payload':'ON'}]
        ensure_deck_keys(config,[{'id':ident,'kind':'streamdeck','deck':{'keys':6}} for ident in ['tablet','phone']])
        save_config(config);self.before=(home()/'config.json').read_bytes()
        self.pool=Recorder()
        with patch('ugso_usbhub.core.Brokers',return_value=self.pool):self.core=Core()
        self.core.hardware.decks={ident:Deck() for ident in ['tablet','phone']}
        self.core.hardware.refresh_decks()

    def tearDown(self):
        self.core.hardware.close();self.pool.close();super().tearDown()

    def tap(self,key,device='tablet'):
        self.core.event(device,'key:'+str(key),'press',1)
        self.core.event(device,'key:'+str(key),'release',0)

    def test_navigation_bounds_repeat_guard_home_and_device_isolation(self):
        other=self.core.hardware.decks['phone'].writes
        self.core.event('tablet','key:4','press',1)
        self.assertEqual(self.core.hardware.active_page('tablet'),1)
        self.core.event('tablet','key:4','press',1)
        self.assertEqual(self.core.hardware.active_page('tablet'),1)
        self.core.event('tablet','key:4','release',0)
        self.tap(4);self.tap(4)
        self.assertEqual(self.core.hardware.active_page('tablet'),2)
        self.tap(3);self.assertEqual(self.core.hardware.active_page('tablet'),1)
        self.tap(5);self.tap(3)
        self.assertEqual(self.core.hardware.active_page('tablet'),0)
        self.assertEqual(self.core.hardware.active_page('phone'),0)
        self.assertEqual(self.core.hardware.decks['phone'].writes,other)
        self.assertEqual(self.pool.calls,[],'Navigation emits no MQTT actions')
        self.assertEqual((home()/'config.json').read_bytes(),self.before)

    def test_held_key_release_does_not_fire_on_new_page_and_topics_are_stable(self):
        original=copy.deepcopy(self.core.config['bindings'])
        self.core.event('tablet','key:0','press',1)
        self.tap(4)
        self.pool.calls.clear()
        self.core.event('tablet','key:0','release',0)
        self.assertEqual(self.pool.calls,[])
        self.tap(0)
        self.assertTrue(self.pool.calls)
        self.assertTrue(all(args[1]=='key:128' for args,kwargs in self.pool.calls))
        row=next(k for k in self.core.config['keys'] if k['device']=='tablet' and k['control']=='key:128')
        self.assertEqual(row['press_topic'],'tablet-page-2-key-0/press')
        first=next(k for k in self.core.config['keys'] if k['device']=='tablet' and k['control']=='key:0')
        self.assertEqual(first['press_topic'],'tablet-key-0/press')
        self.assertEqual(self.core.config['bindings'],original)

    def test_inactive_page_feedback_and_restart_keep_designs_and_settings(self):
        deck=self.core.hardware.decks['tablet'];initial=deck.images[0];writes=deck.writes
        self.core.hardware.display_logical('tablet',128,'','Feedback')
        self.assertEqual(deck.writes,writes);self.assertEqual(deck.images[0],initial)
        self.tap(4)
        with Image.open(io.BytesIO(deck.images[0])) as image:self.assertEqual(image.convert('RGB').getpixel((0,0)),(0,0,255))
        expected=key_image((72,72),{'background':'#0000ff'},label='Feedback',page=1,pages=3)
        with Image.open(io.BytesIO(deck.images[0])) as image:self.assertEqual(image.convert('RGB').tobytes(),expected.tobytes())
        with patch('ugso_usbhub.core.Brokers',return_value=Recorder()):restarted=Core()
        self.assertEqual(restarted.hardware.active_page('tablet'),0)
        self.assertEqual(restarted.config,self.core.config)
        restarted.brokers.close();restarted.hardware.close()

    def test_learning_does_not_navigate_and_nav_actions_preserve_mqtt_rows(self):
        import time
        self.core.learning={'device':'tablet','expires':time.time()+30,'id':'test'}
        self.tap(4)
        self.assertEqual(self.core.hardware.active_page('tablet'),0)
        bindings=all_bindings(self.core.config)
        self.assertFalse(any(b['device']=='tablet' and b['control']=='key:4' for b in bindings))
        saved=copy.deepcopy(self.core.config['keys'])
        self.core.config['devices']['tablet']['deck_keys']['4']['action']='mqtt'
        self.assertTrue(any(b['device']=='tablet' and b['control']=='key:4' for b in all_bindings(self.core.config)))
        self.assertEqual(self.core.config['keys'],saved)

    def test_learning_transition_does_not_leave_deck_release_suppressed(self):
        import time
        self.core.learning={'device':'tablet','expires':time.time()+30,'id':'test'}
        self.core.event('tablet','key:0','press',1)
        self.core.release_all('tablet');self.core.learning={}
        self.core.event('tablet','key:0','release',0)
        self.pool.calls.clear();self.tap(0)
        self.assertTrue(self.pool.calls)
        self.assertFalse(self.core.learning_releases)

    def test_disconnect_clears_held_navigation_for_reconnection(self):
        self.core.event('tablet','key:4','press',1)
        self.assertTrue(self.core.navigation_down)
        self.core.release_all('tablet',disconnected=True)
        self.assertFalse(self.core.navigation_down)
        self.assertFalse(self.core.deck_ignored_releases)
        self.tap(4)
        self.assertEqual(self.core.hardware.active_page('tablet'),2)

    def test_resize_preserves_page_key_ids_hidden_pages_and_validation(self):
        config=copy.deepcopy(self.core.config)
        known={k['control']:k['id'] for k in config['keys'] if k['device']=='tablet'}
        ensure_deck_keys(config,[{'id':'tablet','kind':'streamdeck','deck':{'keys':15}}])
        self.assertTrue(all(next(k for k in config['keys'] if k['device']=='tablet' and k['control']==control)['id']==ident for control,ident in known.items()))
        config['devices']['tablet']['deck_page_count']=1
        validate(config)
        self.assertIn('128',config['devices']['tablet']['deck_keys'])
        self.assertFalse(any(b['device']=='tablet' and int(b['control'].split(':')[1])>=128 for b in all_bindings(config)))
        for invalid in [0,9,True,'2']:
            config['devices']['tablet']['deck_page_count']=invalid
            with self.assertRaises(ValueError):validate(config)

    def test_navigation_labels_and_page_badges_render(self):
        style={'action':'home','show_page':True}
        first=key_image((72,72),style,page=0,pages=3)
        second=key_image((72,72),style,page=1,pages=3)
        self.assertNotEqual(first.tobytes(),second.tobytes())
        self.assertNotEqual(first.tobytes(),key_image((72,72),{}).tobytes())

    def test_goto_target_save_reload_device_isolation_and_no_mqtt(self):
        from ugso_usbhub.deck import validate_artwork
        style={'action':'goto','target_page':3,'show_page':True}
        self.core.config['devices']['tablet']['deck_keys']['1']=style
        save_config(self.core.config)
        self.assertEqual(load_config()['devices']['tablet']['deck_keys']['1'],style)
        self.tap(1)
        self.assertEqual(self.core.hardware.active_page('tablet'),2)
        self.assertEqual(self.core.hardware.active_page('phone'),0)
        self.assertEqual(self.pool.calls,[])
        self.tap(5)
        self.assertEqual(self.core.hardware.active_page('tablet'),0)
        for target in [0,9,True,'2',None]:
            with self.assertRaises(ValueError):validate_artwork({'action':'goto','target_page':target})
        self.assertNotEqual(key_image((72,72),style).tobytes(),key_image((72,72),{}).tobytes())

    def test_deleted_middle_page_keeps_remaining_controls_and_ids(self):
        config=self.core.config
        preserved=copy.deepcopy([k for k in config['keys'] if k['device']=='tablet' and k['control']=='key:256'])
        config['devices']['tablet']['deck_page_count']=2
        config['devices']['tablet']['deck_page_order']=[0,2]
        for key in list(config['devices']['tablet']['deck_keys']):
            if int(key)//128==1:del config['devices']['tablet']['deck_keys'][key]
        config['keys']=[k for k in config['keys'] if not (k['device']=='tablet' and int(k['control'].split(':')[1])//128==1)]
        validate(config);self.core.hardware.config=config
        self.tap(4)
        self.assertEqual(self.core.hardware.active_page('tablet'),1)
        self.pool.calls.clear();self.tap(0)
        self.assertTrue(all(args[1]=='key:256' for args,kwargs in self.pool.calls))
        self.assertEqual([k for k in config['keys'] if k['device']=='tablet' and k['control']=='key:256'],preserved)
        self.assertEqual(preserved[0]['press_topic'],'tablet-page-3-key-0/press')
        for order in [[2,0],[0,0],[0,8]]:
            config['devices']['tablet']['deck_page_order']=order
            with self.assertRaises(ValueError):validate(config)
