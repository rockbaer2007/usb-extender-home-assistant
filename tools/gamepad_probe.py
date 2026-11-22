"""Read-only evdev gamepad probe. No USB Extender, MQTT or network imports."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import time

GUIDED_STEPS=(
    ('NEUTRAL','ANALOG-Modus einstellen. Alle Tasten und Sticks loslassen und während der Messung NICHTS berühren'),
    ('LINKER_STICK_HORIZONTAL','Nur linken Stick mehrfach ganz LINKS → Mitte → RECHTS → Mitte bewegen'),
    ('LINKER_STICK_VERTIKAL','Nur linken Stick mehrfach ganz OBEN → Mitte → UNTEN → Mitte bewegen'),
    ('RECHTER_STICK_HORIZONTAL','Nur rechten Stick mehrfach ganz LINKS → Mitte → RECHTS → Mitte bewegen'),
    ('RECHTER_STICK_VERTIKAL','Nur rechten Stick mehrfach ganz OBEN → Mitte → UNTEN → Mitte bewegen'),
    ('L1','Nur linke OBERE Schultertaste mehrfach drücken und loslassen'),
    ('R1','Nur rechte OBERE Schultertaste mehrfach drücken und loslassen'),
    ('L2','Nur linken UNTEREN Schultertrigger langsam ganz drücken und wieder vollständig loslassen'),
    ('R2','Nur rechten UNTEREN Schultertrigger langsam ganz drücken und wieder vollständig loslassen'),
    ('LINKER_STICK_KLICK','Nur linken Stick senkrecht HINEINDRÜCKEN und loslassen, möglichst nicht auslenken'),
    ('RECHTER_STICK_KLICK','Nur rechten Stick senkrecht HINEINDRÜCKEN und loslassen, möglichst nicht auslenken'))


def guided_assessment(phase,baseline):
    signals=[];ignored=[]
    for key,control in phase.get('controls',{}).items():
        if control['type']==1 and control.get('pressed',0):
            signals.append({'name':control['name'],'kind':'Taste','pressed':control['pressed'],'released':control.get('released',0)})
        elif control['type']==3:
            reference=baseline.get('controls',{}).get(key,{})
            noise=reference.get('max',0)-reference.get('min',0)
            axis=next((a for interface in phase.get('interfaces',[]) for code,a in interface['axes'].items()
                       if key==f"{interface['path']}:3:{code}"),{})
            span=control['max']-control['min']
            threshold=max(3,(axis.get('max',255)-axis.get('min',0))*.04,noise*3)
            result={'name':control['name'],'kind':'Achse','min':control['min'],'max':control['max'],
                'distinct':len(control.get('distinct_values',[])),'neutral_span':noise}
            if span>=threshold:signals.append(result)
            else:ignored.append(result)
    return {'signals':signals,'below_noise_threshold':ignored,'multiple_signals':len(signals)>1}


def is_gamepad(capabilities):
    keys=capabilities.get(1,[])
    keys=[k[0] if isinstance(k,tuple) else k for k in keys]
    axes=capabilities.get(3,[])
    axes=[a[0] if isinstance(a,tuple) else a for a in axes]
    return any(0x120<=k<=0x13f for k in keys) or (any(0x100<=k<=0x10f for k in keys) and any(a in (0,1,16,17) for a in axes))


def normalize(value,low,high):
    if high<=low:return None
    return round(max(0,min(100,100*(value-low)/(high-low))),2)


def code_name(ecodes,kind,code):
    name=ecodes.bytype.get(kind,{}).get(code,str(code))
    if isinstance(name,(tuple,list)):
        preferred=next((n for n in name if n in ('BTN_SOUTH','BTN_EAST','BTN_NORTH','BTN_WEST')),None)
        return preferred or '/'.join(name)
    return name


def transport(path):
    node=(Path('/sys/class/input')/Path(path).name/'device').resolve()
    for parent in (node,*node.parents):
        if (parent/'idVendor').is_file() and (parent/'idProduct').is_file():return parent.name
    return str(node)


def scan(evdev):
    groups={}
    for path in sorted(evdev.list_devices()):
        device=None
        try:
            device=evdev.InputDevice(path)
            if not is_gamepad(device.capabilities()):continue
            port=transport(path)
            group=groups.setdefault(port,{'port':port,'name':device.name,'paths':[],
                'vendor':f'{device.info.vendor:04x}','product':f'{device.info.product:04x}'})
            group['paths'].append(path)
        except (OSError,PermissionError):continue
        finally:
            if device:device.close()
    return list(groups.values())


def hashes():
    folder=Path('/var/lib/ugso-usbhub')
    return {name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in
        ('config.json','switches.json','mobile-identity.json','mobile-trust.json','mobile-devices.json') if (folder/name).is_file()}


def axis_info(device,code):
    info=device.absinfo(code)
    return {name:getattr(info,name) for name in ('value','min','max','fuzz','flat','resolution')}


def describe(device,ecodes):
    caps=device.capabilities();axes={}
    for code in caps.get(3,[]):
        code=code[0] if isinstance(code,tuple) else code
        axes[str(code)]={'name':code_name(ecodes,3,code),**axis_info(device,code)}
    keys=[code_name(ecodes,1,k[0] if isinstance(k,tuple) else k) for k in caps.get(1,[])]
    return {'path':device.path,'name':device.name,'uniq':device.uniq,'phys':device.phys,
        'vendor':f'{device.info.vendor:04x}','product':f'{device.info.product:04x}',
        'version':device.info.version,'keys':keys,'axes':axes}


def format_event(device,event,ecodes,start,mode):
    row={'mode':mode,'seconds':round(time.monotonic()-start,4),'path':device.path,
        'type':event.type,'code':event.code,'name':code_name(ecodes,event.type,event.code),'raw':event.value}
    if event.type==1:row['meaning']={0:'losgelassen',1:'gedrückt',2:'Wiederholung'}.get(event.value,'unbekannt')
    if event.type==3:
        axis=axis_info(device,event.code)
        row.update(min=axis['min'],max=axis['max'],percent=normalize(event.value,axis['min'],axis['max']))
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--guided',action='store_true',help='Einzelzuordnung im Analogmodus, inklusive Ruhemessung')
    parser.add_argument('--output',type=Path,default=Path('gamepad-test-'+time.strftime('%Y%m%d-%H%M%S')))
    args=parser.parse_args()
    if not 10<=args.seconds<=300:parser.error('--seconds: 10–300')
    if os.geteuid()!=0:parser.error('Mit sudo ausführen (nur Gamepad lesen, keine Einstellungen ändern).')
    import evdev
    args.output.mkdir(mode=0o700,parents=True,exist_ok=False)
    transcript=args.output/'ausgabe.txt';raw_path=args.output/'ereignisse.jsonl'
    report={'scope':'physical gamepad, read-only evdev, no MQTT/network, two user-selected modes',
        'phases':[],'original_service_active':False,'completed':False}
    report['guided']=args.guided
    if args.guided:report['scope']='physical gamepad, guided isolated controls in user-selected analog mode; no MQTT/network'
    old_home=os.environ.get('UGSO_USB_HOME')
    before=None;devices=[];running=False
    def log(message):
        print(message,flush=True)
        with transcript.open('a',encoding='utf-8') as f:f.write(message+'\n')
    def ask(message):log(message);return input('> ').strip()
    try:
        running=subprocess.run(['systemctl','is-active','--quiet','ugso-usbhub'],check=False).returncode==0
        report['original_service_active']=running
        if running:subprocess.run(['systemctl','stop','ugso-usbhub'],check=True)
        # Continue only after the input/MQTT daemon is really stopped.
        if subprocess.run(['systemctl','is-active','--quiet','ugso-usbhub'],check=False).returncode==0:
            raise RuntimeError('USB-/MQTT-Dienst ist noch aktiv; keine Messung gestartet.')
        before=hashes()
        log('GAMEPAD-PRÜFUNG · USB-/MQTT-Dienst pausiert. Keine Gamepad-MQTT-Nachrichten.')
        log('Andere USB-/Mobile-Belegungen pausieren ebenfalls bis zum Testende. Webdienst bleibt erhalten.')
        candidates=scan(evdev)
        if not candidates:
            log('Kein Gamepad mit Linux-Eingabetreiber gefunden. Erkannte Eingabegeräte:')
            for path in sorted(evdev.list_devices()):
                device=evdev.InputDevice(path)
                try:log(f'  {path}: {device.name} ({device.info.vendor:04x}:{device.info.product:04x})')
                finally:device.close()
            raise RuntimeError('Keine passende Gamepad-Schnittstelle; nichts mitgeschnitten.')
        for index,item in enumerate(candidates,1):log(f"  {index}: {item['name']} · {item['vendor']}:{item['product']} · Port {item['port']} · {', '.join(item['paths'])}")
        choice=ask('Nummer des Gamepads wählen (Enter = 1). Nur dieses Gerät wird gelesen.') or '1'
        if not choice.isdecimal() or not 1<=int(choice)<=len(candidates):raise RuntimeError('Ungültige Geräteauswahl.')
        chosen=candidates[int(choice)-1];report['selected']=chosen
        if args.guided:log('GEFÜHRTER EINZELTEST: Analogmodus beibehalten. Pro Schritt nur das genannte Element bewegen. s = nicht vorhanden/überspringen.')
        specs=[('analog',name,prompt) for name,prompt in GUIDED_STEPS] if args.guided else [('digital',None,None),('analog',None,None)]
        with raw_path.open('x',encoding='utf-8') as raw:
            for mode,step,prompt in specs:
                label=step or mode.upper()
                answer=ask(f'{step}: {prompt}. Erst nach Enter und MESSUNG STARTET ausführen; zuvor alles loslassen (s = überspringen).') if args.guided else ask(f'Jetzt {mode.upper()}-Modus am Gamepad einstellen, Sticks loslassen, dann Enter. Noch keine Testbewegung.')
                if args.guided and answer.lower()=='s':
                    report['phases'].append({'mode':mode,'step':step,'skipped':True,'controls':{}});log(label+' übersprungen.');continue
                current=next((item for item in scan(evdev) if item['port']==chosen['port']),None)
                if current is None:raise RuntimeError('Gamepad am gewählten USB-Port nicht wiedergefunden. Nach erneutem Verbinden Test neu starten.')
                devices=[evdev.InputDevice(path) for path in current['paths']]
                if any(not is_gamepad(d.capabilities()) for d in devices):raise RuntimeError('Gerätezuordnung änderte sich; Messung abgebrochen.')
                phase={'mode':mode,'device':current,'interfaces':[describe(d,evdev.ecodes) for d in devices],'controls':{}}
                if step:phase['step']=step
                report['phases'].append(phase)
                (args.output/(label.lower()+'-faehigkeiten.json')).write_text(json.dumps(phase['interfaces'],ensure_ascii=False,indent=2),encoding='utf-8')
                for interface in (phase['interfaces'] if not args.guided or step=='NEUTRAL' else []):
                    log(f"{mode.upper()} · {interface['path']} · {interface['name']} · {interface['vendor']}:{interface['product']}")
                    log('Tasten: '+', '.join(interface['keys']))
                    for axis in interface['axes'].values():log(f"  {axis['name']}: Bereich {axis['min']} … {axis['max']}, Ruhewert {axis['value']}, Totzone {axis['flat']}")
                # Discard bounded queued mode-switch events; count real test input only.
                for device in devices:
                    deadline=time.monotonic()+.2;count=0
                    while time.monotonic()<deadline and count<4096 and select.select([device.fd],[],[],0)[0]:
                        try:
                            for event in device.read():
                                count+=1
                                if count>=4096 or time.monotonic()>=deadline:break
                        except BlockingIOError:break
                log(f'MESSUNG {label} STARTET · {args.seconds} Sekunden: '+(prompt if args.guided else 'alle Tasten, Steuerkreuz, beide Sticks, Trigger einzeln bewegen.'))
                start=time.monotonic();progress=0;event_count=0
                while time.monotonic()-start<args.seconds:
                    ready=select.select(devices,[],[],.05)[0]
                    for device in ready:
                        try:
                            for event in device.read():
                                if time.monotonic()-start>=args.seconds:break
                                row=format_event(device,event,evdev.ecodes,start,mode)
                                if step:row['step']=step
                                raw.write(json.dumps(row,ensure_ascii=False)+'\n')
                                if event.type==0:
                                    if event.code==3:
                                        phase['dropped']=phase.get('dropped',0)+1;log('WARNUNG: SYN_DROPPED – Ereignisse verloren, Phase wiederholen.')
                                    continue
                                event_count+=1
                                entry=phase['controls'].setdefault(f'{device.path}:{event.type}:{event.code}',{'name':row['name'],'type':event.type,'code':event.code,'count':0,'min':event.value,'max':event.value})
                                entry.update(count=entry['count']+1,min=min(entry['min'],event.value),max=max(entry['max'],event.value))
                                if event.type==1:
                                    edge='pressed' if event.value==1 else 'released' if event.value==0 else 'repeated'
                                    entry[edge]=entry.get(edge,0)+1
                                if event.type==3:
                                    values=entry.setdefault('distinct_values',[])
                                    if event.value not in values and len(values)<512:values.append(event.value)
                                detail=row.get('meaning','')
                                if event.type==3:detail=f"{row['percent']} % (Bereich {row['min']} … {row['max']})"
                                if not args.guided:log(f"{row['seconds']:7.2f}s · {Path(device.path).name:8} · {row['name']:28} · Rohwert {event.value:7} · {detail}")
                        except BlockingIOError:pass
                    elapsed=int(time.monotonic()-start)
                    if elapsed>=progress+10:
                        progress=elapsed;log(f'Noch {max(0,args.seconds-elapsed)} Sekunden …')
                raw.flush();phase['events']=event_count
                log(f"{label} fertig: {event_count} Ereignisse, {len(phase['controls'])} Eingabecodes.")
                if args.guided and step!='NEUTRAL':
                    baseline=next((p for p in report['phases'] if p.get('step')=='NEUTRAL'),{})
                    phase['assessment']=guided_assessment(phase,baseline)
                    log('Reagiert: '+json.dumps(phase['assessment']['signals'],ensure_ascii=False))
                for device in devices:device.close()
                devices=[]
        report['completed']=True
    except (Exception,KeyboardInterrupt) as exc:
        report['error']=str(exc) or type(exc).__name__;log('Abbruch/Fehler: '+report['error'])
    finally:
        for device in devices:
            try:device.close()
            except OSError:pass
        try:report['settings_unchanged']=before==hashes() if before is not None else None
        except OSError as exc:report['settings_unchanged']=False;report['metadata_error']=str(exc)
        try:
            if running:subprocess.run(['systemctl','start','ugso-usbhub'],check=True)
            report['service_restored']=(subprocess.run(['systemctl','is-active','--quiet','ugso-usbhub'],check=False).returncode==0)==running
        except Exception as exc:report['restore_error']=str(exc);report['service_restored']=False
        report['mqtt_in_probe']=False
        report['meaningful_phases']=len(report['phases'])==(len(GUIDED_STEPS) if args.guided else 2) and all(not p.get('dropped') for p in report['phases']) and (any(p.get('assessment',{}).get('signals') for p in report['phases']) if args.guided else all(p.get('events',0)>0 for p in report['phases']))
        if args.guided and not any(p.get('step')=='NEUTRAL' and not p.get('skipped') for p in report['phases']):report['meaningful_phases']=False
        if old_home!=os.environ.get('UGSO_USB_HOME'):report['unexpected_environment_change']=True
        result_path=args.output/'bericht.json'
        result_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        if args.guided:
            log('\nEINZELZUORDNUNG (Ruherauschen wird gesondert berücksichtigt):')
            for phase in report['phases']:
                if phase.get('step')=='NEUTRAL':continue
                signals=phase.get('assessment',{}).get('signals',[])
                log(phase['step']+': '+('ÜBERSPRUNGEN' if phase.get('skipped') else json.dumps(signals,ensure_ascii=False) if signals else 'KEIN KLARES SIGNAL'))
            log('Mehrere reagierende Codes sind Kandidaten, keine automatisch eindeutige Zuordnung. Gleichzeitige Nebenachsen und ruhende Tasten separat beurteilen.')
        log('ERGEBNIS: '+json.dumps({k:report.get(k) for k in ('completed','meaningful_phases','settings_unchanged','service_restored','mqtt_in_probe','error')},ensure_ascii=False))
        log('Protokoll: '+str(transcript.resolve()));log('Rohdaten: '+str(raw_path.resolve()));log('Bericht: '+str(result_path.resolve()))
        for file in args.output.iterdir():os.chmod(file,0o600)
        uid=os.environ.get('SUDO_UID','');gid=os.environ.get('SUDO_GID','')
        if uid.isdecimal() and gid.isdecimal() and int(uid)>0:
            for file in [args.output,*args.output.iterdir()]:os.chown(file,int(uid),int(gid))
    if not all(report.get(k) for k in ('completed','meaningful_phases','settings_unchanged','service_restored')):raise SystemExit(1)


if __name__=='__main__':main()
