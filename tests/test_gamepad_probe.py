import contextlib
import io
import itertools
import json
import types
from unittest.mock import Mock,patch
from tests.test_hub import TemporaryHome
from ugso_usbhub.storage import home
from tools.gamepad_probe import is_gamepad,normalize,code_name,scan,main,guided_assessment,GUIDED_STEPS


class GamepadProbeTests(TemporaryHome):
    def test_detection_excludes_keyboards_mice_and_touchpads(self):
        self.assertTrue(is_gamepad({1:[288],3:[0,1]}))
        self.assertTrue(is_gamepad({1:[(304,1)],3:[0,1]}))
        self.assertTrue(is_gamepad({1:[256,257],3:[0,1]}))
        self.assertFalse(is_gamepad({1:[30,48],3:[]}))
        self.assertFalse(is_gamepad({1:[272,273],3:[0,1,53,54]}))
        self.assertFalse(is_gamepad({1:[330,272],3:[53,54,57]}))

    def test_normalization_signed_unsigned_hat_and_alias(self):
        self.assertEqual(normalize(-32768,-32768,32767),0)
        self.assertEqual(normalize(0,-32768,32767),50)
        self.assertEqual(normalize(32767,-32768,32767),100)
        self.assertEqual(normalize(255,0,255),100)
        self.assertEqual([normalize(v,-1,1) for v in (-1,0,1)],[0,50,100])
        self.assertIsNone(normalize(2,0,0))
        self.assertEqual(normalize(400,0,255),100)
        self.assertEqual(code_name(types.SimpleNamespace(bytype={1:{304:['BTN_A','BTN_SOUTH']}}),1,304),'BTN_SOUTH')

    def test_scanning_closes_devices_and_groups_only_pad_interfaces(self):
        pad=Mock();pad.name='Generic USB Joystick';pad.info.vendor=0x79;pad.info.product=6;pad.capabilities.return_value={1:[288],3:[0,1]}
        keyboard=Mock();keyboard.capabilities.return_value={1:[30,48]}
        evdev=types.SimpleNamespace(list_devices=lambda:['/dev/input/event1','/dev/input/event2'],InputDevice=Mock(side_effect=[pad,keyboard]))
        with patch('tools.gamepad_probe.transport',return_value='1-1.4'):result=scan(evdev)
        self.assertEqual(len(result),1);self.assertEqual(result[0]['vendor'],'0079');self.assertEqual(result[0]['product'],'0006')
        self.assertEqual(result[0]['paths'],['/dev/input/event1']);pad.close.assert_called_once();keyboard.close.assert_called_once()

    def test_guided_assessment_separates_real_axis_button_and_noise(self):
        phase={'interfaces':[{'path':'event1','axes':{'0':{'min':0,'max':255},'2':{'min':0,'max':255}}}],
            'controls':{'event1:3:0':{'name':'ABS_X','type':3,'min':0,'max':255,'distinct_values':[0,50,128,255]},
                'event1:3:2':{'name':'ABS_Z','type':3,'min':125,'max':135,'distinct_values':[125,128,135]},
                'event1:1:288':{'name':'BTN_TRIGGER','type':1,'pressed':3,'released':3},
                'event1:4:4':{'name':'MSC_SCAN','type':4,'min':1,'max':9}}}
        baseline={'controls':{'event1:3:2':{'min':125,'max':135}}}
        result=guided_assessment(phase,baseline)
        self.assertEqual([s['name'] for s in result['signals']],['ABS_X','BTN_TRIGGER'])
        self.assertEqual(result['below_noise_threshold'][0]['name'],'ABS_Z');self.assertTrue(result['multiple_signals'])
        self.assertEqual(len(GUIDED_STEPS),11)

    def run_probe(self,failed=False,guided=False):
        folder=home()/'capture';args=['gamepad_probe','--seconds','10','--output',str(folder)]
        if guided:args.append('--guided')
        selected={'port':'1-1.4','name':'Generic USB Joystick','paths':['/dev/input/event1'],'vendor':'0079','product':'0006'}
        device=Mock();device.path='/dev/input/event1';device.fd=13;device.name='Generic USB Joystick';device.uniq='';device.phys='usb/test'
        device.info.vendor=0x79;device.info.product=6;device.info.version=1
        device.capabilities.return_value={1:[288],3:[0]}
        device.absinfo.return_value=types.SimpleNamespace(value=127,min=0,max=255,fuzz=0,flat=15,resolution=0)
        answer_count=[0];values=itertools.cycle([0,255])
        def answer(_):answer_count[0]+=1;return ''
        device.read.side_effect=lambda:iter([types.SimpleNamespace(type=3,code=0,value=255 if not guided or answer_count[0]<=2 else next(values))])
        evdev=types.SimpleNamespace(InputDevice=Mock(return_value=device),ecodes=types.SimpleNamespace(bytype={1:{288:'BTN_TRIGGER'},3:{0:'ABS_X'}}))
        calls=[]
        def run(args,**kwargs):
            calls.append(args)
            if args[1]=='is-active':return types.SimpleNamespace(returncode=0 if len([a for a in calls if a[1]=='is-active']) in (1,3) else 3)
            return types.SimpleNamespace(returncode=0)
        fake_scan=Mock(side_effect=RuntimeError('scan failed')) if failed else Mock(return_value=[selected])
        with patch.object(__import__('sys'),'argv',args),patch.dict('sys.modules',{'evdev':evdev}),patch('tools.gamepad_probe.os.geteuid',return_value=0,create=True),patch('tools.gamepad_probe.hashes',return_value={'config.json':'same','mobile-trust.json':'same'}),patch('tools.gamepad_probe.subprocess.run',side_effect=run),patch('tools.gamepad_probe.scan',fake_scan),patch('tools.gamepad_probe.time.monotonic',side_effect=itertools.count()),patch('tools.gamepad_probe.select.select',return_value=([device],[],[])),patch('builtins.input',side_effect=answer),patch.dict('os.environ',{'SUDO_UID':'','SUDO_GID':''}),contextlib.redirect_stdout(io.StringIO()):
            if failed:
                with self.assertRaises(SystemExit):main()
            else:main()
        result=json.loads((folder/'bericht.json').read_text(encoding='utf-8'))
        self.assertIn(['systemctl','stop','ugso-usbhub'],calls);self.assertIn(['systemctl','start','ugso-usbhub'],calls)
        self.assertTrue(result['service_restored']);self.assertTrue(result['settings_unchanged']);self.assertFalse(result['mqtt_in_probe'])
        return folder,result

    def test_two_modes_create_readable_raw_capability_and_summary_logs(self):
        folder,result=self.run_probe()
        self.assertTrue(result['completed']);self.assertTrue(result['meaningful_phases'])
        self.assertEqual([p['mode'] for p in result['phases']],['digital','analog'])
        self.assertIn('ABS_X',(folder/'ausgabe.txt').read_text(encoding='utf-8'))
        rows=[json.loads(line) for line in (folder/'ereignisse.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertTrue(rows);self.assertEqual(rows[0]['percent'],100)
        self.assertTrue((folder/'digital-faehigkeiten.json').is_file());self.assertTrue((folder/'analog-faehigkeiten.json').is_file())

    def test_error_restores_service_and_records_failure(self):
        folder,result=self.run_probe(failed=True)
        self.assertFalse(result['completed']);self.assertEqual(result['error'],'scan failed')

    def test_guided_capture_labels_all_eleven_phases_and_prints_final_summary(self):
        folder,result=self.run_probe(guided=True)
        self.assertTrue(result['guided']);self.assertTrue(result['completed']);self.assertTrue(result['meaningful_phases'])
        self.assertEqual([p['step'] for p in result['phases']],[name for name,prompt in GUIDED_STEPS])
        self.assertEqual(result['phases'][1]['assessment']['signals'][0]['name'],'ABS_X')
        self.assertIn('EINZELZUORDNUNG',(folder/'ausgabe.txt').read_text(encoding='utf-8'))
        rows=[json.loads(line) for line in (folder/'ereignisse.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertTrue(all('step' in row for row in rows))
