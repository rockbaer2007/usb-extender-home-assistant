import copy
import json
import subprocess
import tarfile
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch
from tests.test_hub import TemporaryHome
from tests.broker import Broker, wait_for
from ugso_usbhub.storage import home, load_config, save_config, validate
from ugso_usbhub.management import Management, BASE, COMMANDS, discovery
from ugso_usbhub.backup import create_backup
from ugso_usbhub.web_control import perform, UNIT, main as helper_main, request as helper_request
from ugso_usbhub.mqtt import Brokers


class ManagementTests(TemporaryHome):
    def test_socket_helper_protocol_and_client_error_handling(self):
        from unittest.mock import MagicMock
        connection=MagicMock();connection.recv.return_value=b'start\n'
        context=MagicMock();context.__enter__.return_value=connection
        with patch('ugso_usbhub.web_control.socket.socket',return_value=context),patch('ugso_usbhub.web_control.perform',return_value={'running':True,'autorun':False}) as call:
            helper_main();call.assert_called_once_with('start')
            self.assertEqual(json.loads(connection.sendall.call_args.args[0]),{'running':True,'autorun':False})
        connection.recv.return_value=b'x'*33
        with patch('ugso_usbhub.web_control.socket.socket',return_value=context),patch('ugso_usbhub.web_control.perform') as call,self.assertLogs(level='ERROR'):
            helper_main();call.assert_not_called();self.assertIn('error',json.loads(connection.sendall.call_args.args[0]))
        connection.recv.side_effect=[b'{"running":true,"autorun":false}',b'']
        with patch('ugso_usbhub.web_control.socket.socket',return_value=context),patch('ugso_usbhub.web_control.socket.AF_UNIX',1,create=True):
            self.assertEqual(helper_request('status'),{'running':True,'autorun':False})
        connection.recv.side_effect=[b'{"error":"unavailable"}',b'']
        with patch('ugso_usbhub.web_control.socket.socket',return_value=context),patch('ugso_usbhub.web_control.socket.AF_UNIX',1,create=True):
            with self.assertRaises(OSError):helper_request('status')

    def test_explicit_opt_in_and_exact_command_validation(self):
        config=load_config();self.assertTrue(all(not b.get('control_enabled') for b in config['brokers']))
        config['brokers'][0]['control_enabled']='yes'
        with self.assertRaises(ValueError):validate(config)
        manager=Management(Mock())
        self.assertFalse(manager.submit(BASE+'/web/set','start; reboot'))
        self.assertFalse(manager.submit(BASE+'/backup/set','ON'))
        self.assertFalse(manager.submit('other','ON'))
        self.assertTrue(manager.submit(BASE+'/backup/set','PRESS'))
        self.assertFalse(manager.submit(BASE+'/backup/set','PRESS'),'pending backup deduplicated')
        for topic,payload in [(BASE+'/web/set','ON'),(BASE+'/web/set','OFF'),(BASE+'/web/autorun/set','ON')]:
            self.assertTrue(manager.submit(topic,payload))
        self.assertFalse(manager.submit(BASE+'/web/autorun/set','OFF'),'bounded queue')
        ordered=Management(Mock())
        for payload in ('ON','OFF','ON'):self.assertTrue(ordered.submit(BASE+'/web/set',payload))
        self.assertEqual([ordered.queue.get_nowait() for _ in range(3)],['start','stop','start'])

    def test_privileged_helper_allows_only_fixed_unit_commands(self):
        with patch('ugso_usbhub.web_control.subprocess.run',return_value=types.SimpleNamespace(returncode=0)) as run:
            for action,verbs in [('start',['start']),('stop',['stop']),('enable',['enable','--now']),('disable',['disable','--now'])]:
                self.assertEqual(perform(action),{'running':True,'autorun':True})
                self.assertIn(['systemctl',*verbs,UNIT],[call.args[0] for call in run.call_args_list])
            before=run.call_count
            for action in ['restart ssh','enable /tmp/unit','backup','start\nstop','']:
                with self.assertRaises(ValueError):perform(action)
            self.assertEqual(run.call_count,before)
        with patch('ugso_usbhub.web_control.subprocess.run',return_value=types.SimpleNamespace(returncode=4)):
            with self.assertRaises(OSError):perform('status')

    def test_running_is_not_reported_on_until_http_is_ready(self):
        manager=Management(Mock())
        response=Mock();response.__enter__=Mock(return_value=types.SimpleNamespace(status=200));response.__exit__=Mock(return_value=False)
        with patch('ugso_usbhub.management.request',return_value={'running':True,'autorun':True}),patch('ugso_usbhub.management.build_opener') as opener:
            opener.return_value.open.side_effect=OSError('not listening')
            self.assertEqual(manager.web_status(),(False,True));self.assertEqual(manager.snapshot()['webrun'],'OFF')
            opener.return_value.open.side_effect=None;opener.return_value.open.return_value=response
            self.assertEqual(manager.web_status(),(True,True));self.assertEqual(manager.snapshot()['webrun'],'ON')
            self.assertEqual(manager.snapshot()['autorun'],'ON')
        with patch('ugso_usbhub.management.request',return_value={'running':False,'autorun':False}):
            manager.web_status('disable');self.assertEqual(manager.snapshot()['autorun'],'OFF')
            manager.execute('status');self.assertIn('Webfrontend gestoppt',manager.snapshot()['state']);self.assertIn('Autostart aus',manager.snapshot()['state'])

    def test_backup_contains_settings_icons_pairings_without_export_recursion(self):
        config=load_config();save_config(config)
        (home()/'mobile-trust.json').write_text('{"tablet":"keep"}')
        (home()/'icons').mkdir();(home()/'icons/icon.svg').write_text('<svg/>')
        (home()/'exports').mkdir();(home()/'exports/old-secret.tar.gz').write_bytes(b'old')
        first=create_backup();second=create_backup();self.assertNotEqual(first,second)
        with tarfile.open(first) as archive:
            self.assertEqual(json.load(archive.extractfile('ugso-usbhub/config.json')),config)
            self.assertEqual(archive.extractfile('ugso-usbhub/mobile-trust.json').read(),b'{"tablet":"keep"}')
            self.assertEqual(archive.extractfile('ugso-usbhub/icons/icon.svg').read(),b'<svg/>')
            self.assertFalse(any('/exports/' in name for name in archive.getnames()))
        self.assertEqual(load_config(),config)
        manager=Management(Mock());manager.execute('backup');result=json.loads(manager.snapshot()['backup'])
        self.assertEqual(result['status'],'ok');self.assertNotIn('/',result['file'])
        self.assertNotIn('keep',json.dumps(manager.snapshot()))
        self.assertEqual(Management(Mock()).snapshot()['backup'],manager.snapshot()['backup'])

    def test_backup_failure_and_worker_do_not_block_submit(self):
        manager=Management(Mock())
        with patch('ugso_usbhub.management.create_backup',side_effect=OSError('private details')),self.assertLogs('ugso_usbhub.management',level='ERROR'):
            manager.execute('backup')
        self.assertEqual(json.loads(manager.snapshot()['backup'])['status'],'error')
        self.assertNotIn('private details',str(manager.snapshot()))
        started=threading.Event();finish=threading.Event()
        with patch.object(manager,'execute',side_effect=lambda action:(started.set(),finish.wait(2))),patch.object(manager,'web_status'):
            manager.start();self.assertTrue(manager.submit(BASE+'/backup/set','PRESS'));self.assertTrue(started.wait(1))
            self.assertTrue(manager.submit(BASE+'/web/set','ON'));finish.set();manager.close()

    def test_mqtt_rejects_retained_duplicate_and_untrusted_control(self):
        config=load_config();manager=Mock();pool=Brokers(config,Mock(),start=False,management=manager)
        broker=config['brokers'][0]
        message=types.SimpleNamespace(topic=BASE+'/web/set',payload=b'ON',retain=False,dup=False)
        pool._message(broker)(None,None,message);manager.submit.assert_not_called()
        broker['control_enabled']=True
        for flag in ['retain','dup']:
            setattr(message,flag,True);pool._message(broker)(None,None,message);setattr(message,flag,False)
        manager.submit.assert_not_called()
        pool._message(broker)(None,None,message);manager.submit.assert_called_once_with(message.topic,'ON')

    def test_discovery_and_real_loopback_commands_states_cleanup(self):
        server=Broker();config=load_config();config['brokers'][0].update(enabled=True,host='127.0.0.1',port=server.port,discovery=True,control_enabled=True)
        manager=Mock();manager.snapshot.return_value={'webrun':'OFF','autorun':'OFF','state':'Bereit','backup':'{"status":"idle"}'}
        received=[];pool=Brokers(config,lambda *args:received.append(args),management=manager)
        try:
            wait_for(lambda:pool.states.get('broker1')=='online')
            wait_for(lambda:all(topic in server.subscriptions for topic in COMMANDS))
            server.publish(BASE+'/web/set','ON');wait_for(lambda:manager.submit.called)
            manager.submit.assert_called_with(BASE+'/web/set','ON');self.assertEqual(received,[])
            wait_for(lambda:len([x for x in server.messages if x[0].startswith('homeassistant/') and x[1]])==5)
            for topic,payload,retain in server.messages:
                if topic.startswith(BASE+'/state/'):self.assertTrue(retain)
                if topic.startswith('homeassistant/') and payload:
                    data=json.loads(payload)
                    if 'command_topic' in data:self.assertFalse(data['retain'])
            updated=copy.deepcopy(config);updated['brokers'][0]['control_enabled']=False
            pool.cleanup_removed(updated)
            wait_for(lambda:len([x for x in server.messages if x[0].startswith('homeassistant/') and x[1]==b''])==5)
            self.assertIn((BASE+'/state/webrun',b'UNKNOWN',True),server.messages)
        finally:pool.close();server.close()

    def test_live_mqtt_worker_http_readiness_backup_and_two_broker_feedback(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):self.send_response(200);self.end_headers()
            def log_message(self,*args):pass
        http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        servers=[Broker(),Broker()];config=load_config();config['web']={'host':'127.0.0.1','port':http.server_port}
        for broker,server in zip(config['brokers'],servers):broker.update(enabled=True,host='127.0.0.1',port=server.port,control_enabled=True)
        save_config(config);before=copy.deepcopy(load_config());state={'running':False,'autorun':False};holder={}
        def backend(action):
            if action in ('start','enable'):state['running']=True
            if action in ('stop','disable'):state['running']=False
            if action in ('enable','disable'):state['autorun']=action=='enable'
            return dict(state)
        manager=Management(lambda values:holder.get('pool') and holder['pool'].publish_management(values))
        pool=None
        try:
            with patch('ugso_usbhub.management.request',side_effect=backend):
                pool=Brokers(config,Mock(),management=manager);holder['pool']=pool
                wait_for(lambda:all(pool.states.get(b['id'])=='online' for b in config['brokers'][:2]))
                servers[0].publish(BASE+'/web/set','ON');wait_for(lambda:manager.snapshot()['webrun']=='ON')
                for server in servers:wait_for(lambda:any(t==BASE+'/state/webrun' and p==b'ON' and retain for t,p,retain in server.messages))
                servers[1].publish(BASE+'/web/autorun/set','ON');wait_for(lambda:manager.snapshot()['autorun']=='ON')
                servers[0].publish(BASE+'/backup/set','PRESS');wait_for(lambda:json.loads(manager.snapshot()['backup'])['status']=='ok')
                servers[1].publish(BASE+'/web/autorun/set','OFF');wait_for(lambda:manager.snapshot()['autorun']=='OFF' and manager.snapshot()['webrun']=='OFF')
                self.assertEqual(load_config(),before)
                manager.close()
        finally:
            manager.close()
            if pool:pool.close()
            for server in servers:server.close()
            http.shutdown();http.server_close();thread.join(timeout=1)
