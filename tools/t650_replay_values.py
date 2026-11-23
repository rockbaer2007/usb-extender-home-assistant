"""Replay an existing physical T650 recording through 0.1.32 and local MQTT only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ugso_usbhub import __version__
from ugso_usbhub.touchpad import Touchpad,SLIDE_DIRECTIONS
from tests.broker import Broker,wait_for
from ugso_usbhub.storage import defaults,save_config
from ugso_usbhub.core import Core


def metadata():
    folder=Path('/var/lib/ugso-usbhub')
    return {name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in
        ('config.json','switches.json','mobile-identity.json','mobile-trust.json','mobile-devices.json') if (folder/name).is_file()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    args=parser.parse_args()
    if __version__ not in ('0.1.32','0.1.33','0.1.34','0.1.35','0.1.36'):parser.error('Quellpaket 0.1.32–0.1.36 erforderlich')
    source=json.loads(args.report.read_text(encoding='utf-8'))
    if 't650' not in source.get('device','').lower():parser.error('Kein T650-Bericht')
    output=args.report.with_name('values-replay-'+time.strftime('%Y%m%d-%H%M%S')+'.json')
    before=metadata();servers=[];core=None
    result={'version':__version__,'source':str(args.report),'scope':'replay of physical evdev recordings; loopback MQTT; no real HA check','phases':[]}
    try:
        with tempfile.TemporaryDirectory(prefix='t650-values-replay-') as folder:
            os.environ['UGSO_USB_HOME']=folder
            config=defaults()
            values={d:{'enabled':True,'topic':'t650-replay/'+d.lower()+'/value'} for d in SLIDE_DIRECTIONS}
            config['devices']['t650']={'name':'T650 Replay','enabled':True,'touchpad_gestures':True,
                'touchpad_xy':True,'touchpad_x_topic':'t650-replay/x','touchpad_y_topic':'t650-replay/y',
                'touchpad_slide_values':values,'targets':['broker1','broker2','broker3']}
            for broker in config['brokers']:
                server=Broker();servers.append(server)
                broker.update(enabled=True,host='127.0.0.1',port=server.port,discovery=broker['id']!='broker2')
            save_config(config);core=Core()
            wait_for(lambda:all(core.brokers.states.get(b['id'])=='online' for b in config['brokers']))
            wait_for(lambda:all(len([m for m in servers[i].messages if m[0].startswith('homeassistant/sensor/')])==10 for i in (0,2)))
            expected=[]
            for direction in SLIDE_DIRECTIONS:
                raw_path=args.report.parent/(direction+'-raw.json')
                raw=json.loads(raw_path.read_text(encoding='utf-8'))
                events=[];stamp=0.
                def emit(*event):
                    events.append((stamp,*event));core.event('t650',*event)
                    if event[0]=='_touchpad_position':
                        expected.extend([('t650-replay/x',str(event[2][0])),('t650-replay/y',str(event[2][1]))])
                    if event[0]=='_touchpad_slide_value':expected.append((values[event[1]]['topic'],str(event[2])))
                pad=Touchpad(emit,*source['ranges'],config['devices']['t650'])
                for stamp,kind,code,value in raw:pad.feed(kind,code,value,stamp);pad.tick(stamp)
                if raw:stamp=raw[-1][0]+1.1;pad.tick(stamp)
                rows=[e for e in events if e[1]=='_touchpad_slide_value' and e[2]==direction]
                tips=[e for e in events if e[1].startswith('TOUCHPAD_TAP_') and e[2]=='press']
                xy=[e for e in events if e[1]=='_touchpad_position']
                phase={'direction':direction,'raw_events':len(raw),'values':len(rows),'first':rows[0][3] if rows else None,
                    'last':rows[-1][3] if rows else None,'min':min(e[3] for e in rows) if rows else None,
                    'max':max(e[3] for e in rows) if rows else None,'xy_pairs':len(xy),'tips':len(tips)}
                result['phases'].append(phase);print(json.dumps(phase),flush=True)
            wait_for(lambda:all(len([m for m in s.messages if m[0].startswith('t650-replay/')])==len(expected) for s in servers))
            messages=[[(t,p.decode(),r) for t,p,r in s.messages if t.startswith('t650-replay/')] for s in servers]
            result['mqtt_counts']=[len(m) for m in messages]
            result['mqtt_identical']=messages[0]==messages[1]==messages[2]
            result['mqtt_matches_events']=all([(t,p) for t,p,r in rows]==expected for rows in messages)
            result['mqtt_plain_numbers']=bool(expected) and all(p.isdigit() and 0<=int(p)<=100 and not r for rows in messages for t,p,r in rows)
            discoveries=[{t:json.loads(p) for t,p,r in s.messages if t.startswith('homeassistant/sensor/') and p} for s in servers]
            expected_topics={'t650-replay/x','t650-replay/y',*[v['topic'] for v in values.values()]}
            result['discovery_counts']=[len(d) for d in discoveries]
            result['discovery_valid']=not discoveries[1] and all(len(discoveries[i])==10 and
                {v['state_topic'] for v in discoveries[i].values()}==expected_topics and
                len({v['unique_id'] for v in discoveries[i].values()})==10 and
                all(v['device']['identifiers']==[f"ugso_{config['hub_id']}_t650"] for v in discoveries[i].values()) for i in (0,2))
    finally:
        if core:core.brokers.close();core.hardware.close();core.mobile.close()
        for server in servers:server.close()
        result['metadata_unchanged']=before==metadata()
        output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
        os.chmod(output,0o600)
    result['passed']=all(result.get(k) for k in ('mqtt_identical','mqtt_matches_events','mqtt_plain_numbers','discovery_valid','metadata_unchanged')) and len(result['phases'])==8 and all(p['values'] and p['xy_pairs'] and not p['tips'] for p in result['phases'])
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print('ERGEBNIS:',json.dumps({k:v for k,v in result.items() if k not in ('phases','source','scope')},ensure_ascii=False))
    print('Bericht:',output)
    if not result['passed']:raise SystemExit('Prüfung nicht bestanden; Bericht auswerten.')


if __name__=='__main__':main()
