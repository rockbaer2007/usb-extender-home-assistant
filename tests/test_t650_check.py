import sys
import types
from unittest.mock import Mock,patch
from tests.test_hub import TemporaryHome
from tools.t650_check import main,replay,summarize,drain_pending,value_options
from ugso_usbhub.storage import home


class ProbeTests(TemporaryHome):
    def test_pending_evdev_generator_is_consumed_and_becomes_empty(self):
        pending=[1,2,3]
        device=Mock();device.fd=13
        def read():
            while pending:yield pending.pop(0)
        device.read.side_effect=read
        with patch('tools.t650_check.select.select',side_effect=lambda *_:([13] if pending else [],[],[])):
            self.assertEqual(drain_pending(device),3)
        self.assertEqual(pending,[])

    def test_continuous_input_and_read_race_do_not_hang_drain(self):
        device=Mock();device.fd=13
        device.read.side_effect=lambda:iter(range(100))
        with patch('tools.t650_check.select.select',return_value=([13],[],[])):
            self.assertEqual(drain_pending(device,maximum=12),12)
        device.read.side_effect=BlockingIOError
        with patch('tools.t650_check.select.select',return_value=([13],[],[])):
            self.assertEqual(drain_pending(device),0)
        device.read.side_effect=lambda:iter(range(100))
        with patch('tools.t650_check.select.select',return_value=([13],[],[])),patch('tools.t650_check.time.monotonic',side_effect=[0,.01,.21]):
            self.assertEqual(drain_pending(device,seconds=.2),1)

    def test_replay_reports_diagonal_position_and_no_tap(self):
        raw=[(0,3,57,1),(0,3,53,100),(0,3,54,100),(0,0,0,0),
             (.1,3,53,800),(.1,3,54,800),(.1,0,0,0),(.2,3,57,-1),(.2,0,0,0)]
        result=summarize(replay(raw,[(0,1000),(0,1000)]))
        self.assertEqual(result['actions'],{'TOUCHPAD_SLIDE_DOWN_RIGHT':1})
        self.assertEqual(result['tap_actions'],0);self.assertEqual(result['xy_max'],[80,80])
        self.assertEqual(result['direction_values']['DOWN_RIGHT']['last'],80)
        self.assertEqual(len(value_options()['touchpad_slide_values']),8)

    def test_k400_is_rejected_before_any_service_action(self):
        backup=home()/'backup.tar.gz';backup.write_bytes(b'placeholder')
        device=Mock(name='device');device.name='Logitech K400';device.uniq='k400'
        args=['t650_check','--device','/dev/input/event14','--uniq','k400','--backup',str(backup)]
        with patch.object(sys,'argv',args),patch.dict('sys.modules',{'evdev':types.SimpleNamespace(InputDevice=Mock(return_value=device))}),patch('tools.t650_check.subprocess.run') as run:
            with self.assertRaises(SystemExit):main()
            run.assert_not_called();device.close.assert_called_once()

    def test_service_restored_even_if_test_and_report_write_fail(self):
        backup=home()/'backup.tar.gz';backup.write_bytes(b'placeholder')
        device=Mock();device.name='Logitech T650';device.uniq='t650'
        device.capabilities.return_value={3:[47,53,54,57]}
        device.absinfo.return_value=types.SimpleNamespace(min=0,max=1000)
        args=['t650_check','--device','/dev/input/event13','--uniq','t650','--backup',str(backup),
              '--pause-service','--output',str(home()/'report')]
        with patch.object(sys,'argv',args),patch.dict('sys.modules',{'evdev':types.SimpleNamespace(InputDevice=Mock(return_value=device))}),patch('tools.t650_check.subprocess.run',return_value=types.SimpleNamespace(returncode=0)) as run,patch('tools.t650_check.live_hashes',return_value={}),patch('ugso_usbhub.storage.defaults',side_effect=RuntimeError('test failed')),patch('tools.t650_check.Path.write_text',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):main()
            self.assertEqual(run.call_args_list[-1].args[0],['systemctl','start','ugso-usbhub'])
            self.assertIn(['systemctl','stop','ugso-usbhub'],[c.args[0] for c in run.call_args_list])
