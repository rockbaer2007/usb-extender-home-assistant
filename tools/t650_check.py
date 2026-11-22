"""Interactive real-T650 check; isolated MQTT, no live configuration writes."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ugso_usbhub.touchpad import Touchpad

DIRECTIONS=('RIGHT','LEFT','UP','DOWN','DOWN_RIGHT','UP_LEFT','DOWN_LEFT','UP_RIGHT')
PROMPTS=('nach rechts','nach links','nach oben','nach unten','links oben → rechts unten',
         'rechts unten → links oben','rechts oben → links unten','links unten → rechts oben')


def value_options():
    return {'touchpad_xy':True,'touchpad_slide_values':{
        name:{'enabled':True,'topic':'t650-test/slide-'+name.lower()+'/value'} for name in DIRECTIONS}}


def drain_pending(device, seconds=.2, maximum=4096):
    """Consume evdev's generator; never wait for a continuously active pad."""
    deadline=time.monotonic()+seconds
    count=0
    while count<maximum and time.monotonic()<deadline and select.select([device.fd],[],[],0)[0]:
        try:
            for _ in device.read():
                count+=1
                if count>=maximum or time.monotonic()>=deadline:return count
        except BlockingIOError:
            break
    return count


def replay(raw, ranges, sensitivity=5, rate=10):
    events=[];stamp=0.
    pad=Touchpad(lambda *e:events.append((stamp,*e)),*ranges,
                 {**value_options(),'touchpad_sensitivity':sensitivity,'touchpad_rate':rate})
    for stamp,kind,code,value in raw:
        pad.feed(kind,code,value,stamp);pad.tick(stamp)
    if raw:stamp=raw[-1][0]+1.1;pad.tick(stamp)
    return events


def summarize(events):
    actions=Counter(e[1] for e in events if e[2]=='press')
    xy=[e for e in events if e[1]=='_touchpad_position']
    slides=[e for e in events if e[2]=='press' and e[1].startswith('TOUCHPAD_SLIDE_')]
    result={'actions':dict(actions),'xy_pairs':len(xy),'slide_actions':len(slides),
            'tap_actions':sum(v for k,v in actions.items() if k.startswith('TOUCHPAD_TAP_'))}
    values=[e for e in events if e[1]=='_touchpad_slide_value']
    result['direction_values']={}
    for direction in DIRECTIONS:
        rows=[e[3] for e in values if e[2]==direction]
        if rows:result['direction_values'][direction]={'count':len(rows),'first':rows[0],'last':rows[-1],'min':min(rows),'max':max(rows)}
    result['values_min_interval']=round(min(b[0]-a[0] for a,b in zip(values,values[1:])),6) if len(values)>1 else None
    for label,rows in [('xy',xy),('slide',slides)]:
        gaps=[b[0]-a[0] for a,b in zip(rows,rows[1:])]
        result[label+'_min_interval']=round(min(gaps),6) if gaps else None
    if xy:
        result['xy_min']=[min(e[3][axis] for e in xy) for axis in (0,1)]
        result['xy_max']=[max(e[3][axis] for e in xy) for axis in (0,1)]
    return result


def live_hashes():
    folder=Path('/var/lib/ugso-usbhub')
    return {name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
            for name in ('config.json','switches.json','mobile-identity.json','mobile-trust.json','mobile-devices.json') if (folder/name).is_file()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device',required=True)
    parser.add_argument('--uniq',required=True)
    parser.add_argument('--backup',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path('t650-results-'+time.strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('--pause-service',action='store_true')
    args=parser.parse_args()
    if not args.backup.is_file() or args.backup.stat().st_size==0:parser.error('Geprüfte Sicherung angeben')
    from evdev import InputDevice
    device=InputDevice(args.device)
    if 't650' not in device.name.lower() or device.uniq!=args.uniq:
        device.close();parser.error('Name/Kennung passen nicht zum T650; keine anderen Geräte auswerten')
    codes=[c[0] if isinstance(c,tuple) else c for c in device.capabilities().get(3,[])]
    if not all(code in codes for code in (47,53,54,57)):
        device.close();parser.error('Type-B-Multitouch fehlt')
    ranges=[(device.absinfo(code).min,device.absinfo(code).max) for code in (53,54)]
    args.output.mkdir(parents=True,exist_ok=False)
    os.chmod(args.output,0o700)
    running=subprocess.run(['systemctl','is-active','--quiet','ugso-usbhub']).returncode==0
    if running and not args.pause_service:
        device.close();parser.error('Dienst läuft; --pause-service für isolierte Prüfung verwenden')
    report={'device':device.name,'uniq':device.uniq,'ranges':ranges,'backup':str(args.backup),
            'phases':[],'scope':'real evdev input, temporary config, three loopback MQTT brokers'}
    pool=None;core=None;servers=[];before=None
    try:
        if running:subprocess.run(['systemctl','stop','ugso-usbhub'],check=True)
        before=live_hashes()
        with tempfile.TemporaryDirectory(prefix='t650-check-') as temporary:
            os.environ['UGSO_USB_HOME']=temporary
            from tests.broker import Broker,wait_for
            from ugso_usbhub.storage import defaults,save_config
            from ugso_usbhub.core import Core
            config=defaults();config['devices']['t650']={'name':'T650 Test','enabled':True,
                'touchpad_gestures':True,**value_options(),'targets':['broker1','broker2','broker3']}
            for direction in (*DIRECTIONS,'TAP_1'):
                control='TOUCHPAD_'+('SLIDE_'+direction if direction in DIRECTIONS else direction)
                config.setdefault('keys',[]).append({'id':direction,'device':'t650','control':control,'name':direction,
                    'press':True,'release':True,'switch':False,'press_topic':'t650-test/'+direction+'/press',
                    'release_topic':'t650-test/'+direction+'/release'})
            config['devices']['t650'].update(touchpad_x_topic='t650-test/x',touchpad_y_topic='t650-test/y')
            for broker in config['brokers']:
                server=Broker();servers.append(server)
                broker.update(enabled=True,host='127.0.0.1',port=server.port,discovery=broker['id']!='broker2')
            save_config(config);core=Core();pool=core.brokers
            wait_for(lambda:len(pool.states)==3 and all(s=='online' for s in pool.states.values()))
            wait_for(lambda:all(len([m for m in servers[i].messages if m[0].startswith('homeassistant/sensor/')])==10 for i in (0,2)))
            phases=list(zip(DIRECTIONS,PROMPTS))+[('TAP_1','nur kurz tippen, ohne Schieben'),
                ('RATE','zügig mit EINEM Finger über die GANZE Fläche hin und her schieben, jeweils abheben')]
            for name,prompt in phases:
                input('\n'+name+': '+prompt+'. Finger abheben, Enter drücken, dann 6 Sekunden mehrfach ausführen. ')
                drained=drain_pending(device)
                print(name+': MESSUNG STARTET JETZT · 6 Sekunden · alte Ereignisse: '+str(drained),flush=True)
                events=[];raw=[];stamp=0.;start=time.monotonic()
                progress=0
                def emit(*event):
                    events.append((stamp,*event));core.event('t650',*event)
                pad=Touchpad(emit,*ranges,value_options())
                while time.monotonic()-start<6:
                    if select.select([device.fd],[],[],.01)[0]:
                        for event in device.read():
                            stamp=time.monotonic()-start
                            if event.type in (0,1,3):
                                raw.append((stamp,event.type,event.code,event.value))
                                pad.feed(event.type,event.code,event.value,stamp)
                    stamp=time.monotonic()-start;pad.tick(stamp)
                    elapsed=int(stamp)
                    if elapsed>progress and elapsed<6:
                        progress=elapsed;print(name+': noch '+str(6-elapsed)+' Sekunden',flush=True)
                # Allow one final rate window to publish the last position.
                time.sleep(.11);stamp=time.monotonic()-start;pad.tick(stamp)
                result={'name':name,'raw_events':len(raw),'live':summarize(events),
                    'sensitivity':{str(n):summarize(replay(raw,ranges,n,10)) for n in (1,5,10)},
                    'rates':{str(n):summarize(replay(raw,ranges,5,n)) for n in (1,5,30)}}
                result['expected_seen']=('TOUCHPAD_'+('TAP_1' if name=='TAP_1' else 'SLIDE_'+name)) in result['live']['actions'] if name!='RATE' else None
                result['expected_value_seen']=name in result['live']['direction_values'] if name in DIRECTIONS else None
                report['phases'].append(result)
                (args.output/(name+'-raw.json')).write_text(json.dumps(raw),encoding='utf-8')
                print(name,'live:',json.dumps(result['live'],ensure_ascii=False),'erwartete Richtung:',result['expected_seen'],flush=True)
                print('Empfindlichkeit 1/5/10:',[result['sensitivity'][str(n)]['slide_actions'] for n in (1,5,10)],
                      'Rate 1/5/30:',[result['rates'][str(n)]['xy_min_interval'] for n in (1,5,30)],flush=True)
            time.sleep(.2)
            messages=[[{'topic':t,'payload':p.decode(),'retain':r} for t,p,r in s.messages if t.startswith('t650-test/')] for s in servers]
            report['mqtt_counts']=[len(m) for m in messages]
            report['mqtt_identical']=messages[0]==messages[1]==messages[2]
            report['mqtt_plain_xy']=all(m['payload'].isdigit() and 0<=int(m['payload'])<=100 and not m['retain'] for rows in messages for m in rows if m['topic'] in ('t650-test/x','t650-test/y'))
            report['mqtt_messages']=messages
            numeric_topics={'t650-test/x','t650-test/y',*[v['topic'] for v in value_options()['touchpad_slide_values'].values()]}
            report['mqtt_plain_values']=all(m['payload'].isdigit() and 0<=int(m['payload'])<=100 and not m['retain'] for rows in messages for m in rows if m['topic'] in numeric_topics)
            report['mqtt_value_topics']=sorted({m['topic'] for m in messages[0] if m['topic'] in numeric_topics})
            discoveries=[]
            for server in servers:
                discoveries.append({t:json.loads(p) for t,p,r in server.messages if t.startswith('homeassistant/sensor/') and p})
            report['discovery_counts']=[len(d) for d in discoveries]
            report['discovery_valid']=all(len(discoveries[i])==10 and len({v['unique_id'] for v in discoveries[i].values()})==10 and
                all(v['device']['identifiers']==[f"ugso_{config['hub_id']}_t650"] and v['state_topic'] in numeric_topics for v in discoveries[i].values()) for i in (0,2)) and not discoveries[1]
            report['discovery_scope']='Loopback MQTT payload check; real Home Assistant entity display not checked'
            directions=[p for p in report['phases'] if p['name'] in DIRECTIONS]
            report['hardware_values_pass']=len(directions)==8 and all(p['expected_seen'] and p['expected_value_seen'] and not p['live']['tap_actions'] for p in directions) and len(report['mqtt_value_topics'])==10
    finally:
        try:
            if pool:pool.close()
            if core:core.hardware.close();core.mobile.close()
            for server in servers:server.close()
            device.close()
            report['settings_unchanged']=before==live_hashes() if before is not None else None
            (args.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        finally:
            if running:subprocess.run(['systemctl','start','ugso-usbhub'],check=True)
    print('\nBericht:',args.output/'report.json',flush=True)
    print('Einstellungen unverändert:',report['settings_unchanged'],flush=True)
    print('MQTT:',report.get('mqtt_counts'),'identisch:',report.get('mqtt_identical'),'X/Y Zahlen:',report.get('mqtt_plain_xy'),flush=True)
    print('Acht Richtungswerte:',report.get('hardware_values_pass'),'alle Zahlen:',report.get('mqtt_plain_values'),'Discovery:',report.get('discovery_counts'),report.get('discovery_valid'),flush=True)
    if not all(report.get(k) for k in ('hardware_values_pass','mqtt_plain_values','mqtt_identical','discovery_valid','settings_unchanged')):
        raise SystemExit('Prüfung unvollständig/fehlgeschlagen; Bericht auswerten, kein Erfolg bestätigt.')


if __name__=='__main__':main()
