"""Bounded background MQTT system commands; input handling never waits for backups."""
from datetime import datetime, timezone
import json
import logging
import queue
import threading
import time
from urllib.request import build_opener, ProxyHandler
from .storage import home, atomic_json, read_json
from .web_control import request
from .backup import create_backup

LOG=logging.getLogger(__name__)

BASE='usb-extender/global'
COMMANDS={BASE+'/web/set':{'ON':'start','OFF':'stop'},
          BASE+'/web/autorun/set':{'ON':'enable','OFF':'disable'},
          BASE+'/backup/set':{'PRESS':'backup'},BASE+'/web/status/set':{'PRESS':'status'}}


def discovery(hub,availability):
    device={'identifiers':['ugso_'+hub+'_system'],'name':'USB Extender','manufacturer':'USB Extender','model':'Systemsteuerung'}
    result={}
    rows=[('switch','web','Webfrontend',BASE+'/web/set','webrun'),
          ('switch','autorun','Web-Autostart',BASE+'/web/autorun/set','autorun'),
          ('button','backup','Backup',BASE+'/backup/set',None),
          ('sensor','status','Systemstatus',None,'state'),
          ('sensor','backup','Backupstatus',None,'backup')]
    for kind,key,name,command,state in rows:
        unique='ugso_'+hub+'_management_'+kind+'_'+key
        value={'name':name,'unique_id':unique,'device':device,'availability_topic':availability}
        if command:value.update(command_topic=command,qos=0,retain=False)
        if state:value['state_topic']=BASE+'/state/'+state
        if kind=='switch':value.update(payload_on='ON',payload_off='OFF')
        if kind=='button':value['payload_press']='PRESS'
        if kind=='sensor' and key=='backup':value.update(value_template='{{ value_json.status }}',json_attributes_topic=BASE+'/state/backup')
        result['homeassistant/'+kind+'/'+unique+'/config']=json.dumps(value)
    return result


class Management:
    def __init__(self,publish):
        self.publish=publish;self.queue=queue.Queue(maxsize=4);self.stop=threading.Event();self.thread=None
        self.lock=threading.Lock();self.pending=set();self.web_config={};self.enabled=True
        saved=read_json(home()/'management-state.json',{})
        backup=saved.get('backup') if isinstance(saved,dict) else None
        if not isinstance(backup,str) or len(backup)>4096:backup=json.dumps({'status':'idle'})
        self.values={'webrun':'UNKNOWN','autorun':'UNKNOWN','state':'Status wird ermittelt',
                     'backup':backup}

    def snapshot(self):
        with self.lock:return dict(self.values)

    def update(self,**values):
        with self.lock:
            changed=any(self.values.get(k)!=v for k,v in values.items());self.values.update(values)
            snapshot=dict(self.values)
        if changed:
            try:self.publish(snapshot)
            except Exception:LOG.exception('MQTT-Systemstatus konnte nicht gesendet werden')

    def start(self):
        if self.thread and self.thread.is_alive():return
        self.thread=threading.Thread(target=self.run,name='mqtt-system-control',daemon=True);self.thread.start()

    def submit(self,topic,payload):
        action=COMMANDS.get(topic,{}).get(payload)
        if not action:return False
        with self.lock:
            if action=='backup' and action in self.pending:return False
            try:self.queue.put_nowait(action)
            except queue.Full:return False
            self.pending.add(action)
        return True

    def web_status(self,action='status'):
        status=request(action);ready=False
        if status['running']:
            host=self.web_config.get('host','0.0.0.0');host='127.0.0.1' if host=='0.0.0.0' else '::1' if host=='::' else host
            if ':' in host:host='['+host+']'
            try:
                with build_opener(ProxyHandler({})).open('http://'+host+':'+str(self.web_config.get('port',8098))+'/',timeout=1) as response:
                    ready=response.status==200
            except OSError:pass
        values={'webrun':'ON' if ready else 'OFF','autorun':'ON' if status['autorun'] else 'OFF'}
        old=self.snapshot()
        if action!='status' or any(old[k]!=v for k,v in values.items()):
            values['state']='Webfrontend erreichbar' if ready else 'Webfrontend startet' if status['running'] else 'Webfrontend gestoppt'
        self.update(**values)
        return ready,status['running']

    def execute(self,action):
        if action=='backup':
            stamp=lambda:datetime.now(timezone.utc).isoformat()
            self.update(backup=json.dumps({'status':'running','time':stamp()}),state='Sicherung wird erstellt')
            try:
                target=create_backup()
                value=json.dumps({'status':'ok','time':stamp(),'file':target.name},ensure_ascii=False)
                atomic_json(home()/'management-state.json',{'backup':value})
                self.update(backup=value,state='Sicherung abgeschlossen')
            except Exception:
                LOG.exception('MQTT-Sicherung fehlgeschlagen')
                value=json.dumps({'status':'error','time':stamp(),'error':'Sicherung fehlgeschlagen; Dienstprotokoll prüfen'})
                try:atomic_json(home()/'management-state.json',{'backup':value})
                except OSError:LOG.exception('Sicherungsstatus konnte nicht gespeichert werden')
                self.update(backup=value,state='Sicherung fehlgeschlagen')
        else:
            self.update(state='Webbefehl: '+action)
            ready,running=self.web_status(action)
            if action=='status':self.update(state=('Webfrontend erreichbar' if ready else 'Webfrontend startet' if running else 'Webfrontend gestoppt')+' · Autostart '+('ein' if self.snapshot()['autorun']=='ON' else 'aus'))
            deadline=time.monotonic()+10
            while running and not ready and action in ('start','enable') and time.monotonic()<deadline and not self.stop.wait(.25):
                ready,running=self.web_status()
            if action in ('start','enable') and not ready:self.update(state='Webfrontend nicht erreichbar; Dienstprotokoll prüfen')

    def run(self):
        due=0
        while not self.stop.is_set():
            action=None
            try:
                action=self.queue.get(timeout=.25);self.execute(action)
            except queue.Empty:pass
            except Exception:
                LOG.exception('MQTT-Websteuerung fehlgeschlagen')
                self.update(webrun='UNKNOWN',autorun='UNKNOWN',state='Websteuerung fehlgeschlagen; Dienstprotokoll prüfen')
            finally:
                if action:
                    with self.lock:self.pending.discard(action)
                    self.queue.task_done()
            if self.enabled and time.monotonic()>=due:
                due=time.monotonic()+5
                try:self.web_status()
                except Exception:self.update(webrun='UNKNOWN',autorun='UNKNOWN',state='Webstatus nicht verfügbar; Installation prüfen')

    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=2)
