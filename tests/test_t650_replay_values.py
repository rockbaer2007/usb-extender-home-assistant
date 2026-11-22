import json
from unittest.mock import patch
from tests.test_hub import TemporaryHome
from ugso_usbhub.storage import home
from tools.t650_replay_values import main


class ReplayValueTests(TemporaryHome):
    def test_complete_recording_to_three_local_brokers_and_ten_sensors(self):
        folder=home();report=folder/'report.json'
        report.write_text(json.dumps({'device':'Logitech T650','ranges':[[0,1000],[0,1000]]}),encoding='utf-8')
        paths={'UP':((500,1000),(500,0)),'DOWN':((500,0),(500,1000)),
            'RIGHT':((0,500),(1000,500)),'LEFT':((1000,500),(0,500)),
            'UP_RIGHT':((0,1000),(1000,0)),'DOWN_LEFT':((1000,0),(0,1000)),
            'DOWN_RIGHT':((0,0),(1000,1000)),'UP_LEFT':((1000,1000),(0,0))}
        for direction,(start,end) in paths.items():
            raw=[(0,3,57,1),(0,3,53,start[0]),(0,3,54,start[1]),(0,0,0,0),
                (.2,3,53,end[0]),(.2,3,54,end[1]),(.2,0,0,0),(.3,3,57,-1),(.3,0,0,0)]
            (folder/(direction+'-raw.json')).write_text(json.dumps(raw),encoding='utf-8')
        with patch('sys.argv',['t650_replay_values',str(report)]):main()
        result=json.loads(next(folder.glob('values-replay-*.json')).read_text(encoding='utf-8'))
        self.assertTrue(result['passed']);self.assertEqual(result['discovery_counts'],[10,0,10])
        self.assertEqual(result['mqtt_counts'],[24,24,24]);self.assertEqual(len(result['phases']),8)
