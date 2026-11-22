"""Stable hardware associations and backed-up, explicit device administration."""
import copy
import hashlib
import tarfile
import time
import uuid
from .storage import home, load_config, read_json, atomic_json, save_config


def descriptor(device):
    result={name:device.get(name, '') for name in
            ('hardware_key','observed_id','vendor','product_id','serial','port','kind')}
    result['observed_id']=device.get('observed_id',device['id'])
    return result


def resolve_inventory(found, config):
    settings=config.get('devices', {})
    counts={};raw_counts={}
    for d in found:
        if d.get('hardware_key'):counts[d['hardware_key']]=counts.get(d['hardware_key'],0)+1
        raw=d.get('observed_id',d['id']);raw_counts[raw]=raw_counts.get(raw,0)+1
    result=[];used=set()
    for original in found:
        d=copy.deepcopy(original);raw=d.get('observed_id',d['id']);d['observed_id']=raw
        if raw_counts[raw]>1:
            # Broken/duplicated firmware serials must never choose a saved unit
            # merely because it was enumerated first. Bind explicitly by port.
            raw+='@'+d.get('port','')
            d['observed_id']=raw
        candidates=[]
        for ident,saved in settings.items():
            hw=saved.get('hardware',{})
            strong=d.get('hardware_key') and counts[d['hardware_key']]==1 and hw.get('hardware_key')==d['hardware_key']
            exact=hw.get('observed_id')==raw
            legacy=ident==raw and not hw and raw_counts.get(raw,0)==1
            if strong or exact or legacy:candidates.append(ident)
        if len(candidates)==1 and candidates[0] not in used:
            d['id']=candidates[0]
        elif raw in settings or raw in used or d['id']!=raw:
            d['id']='unassigned-'+hashlib.sha256(raw.encode()).hexdigest()[:24]
        used.add(d['id']);result.append(d)
    return result


def remember_hardware(config, found):
    for d in found:
        if d.get('connection')=='mobile':continue
        if d['id'] in config.get('devices',{}):
            config['devices'][d['id']]['hardware']=descriptor(d)


def administer(body, snapshot):
    from .learning import current
    if current():raise ValueError('Anlernen vor der Geräteverwaltung beenden')
    old=load_config();config=copy.deepcopy(old)
    action=body.get('action');ident=body.get('device')
    registry=read_json(home()/'mobile-devices.json',{})
    trust=read_json(home()/'mobile-trust.json',{})
    switches=read_json(home()/'switches.json',{})
    writes={}
    if action=='reassign':
        if ident not in config['devices']:raise ValueError('Gespeichertes Zielgerät fehlt')
        if ident.startswith('mobile-') or ident in registry:raise ValueError('Ein USB-Gerät kann keinem Mobile-Deck zugeordnet werden')
        if time.time()-snapshot.get('updated',0)>15 or snapshot.get('stopped'):raise ValueError('Aktuellen Gerätestatus abwarten')
        if any(d['id']==ident for d in snapshot.get('devices',[])):raise ValueError('Das Zielgerät ist noch verbunden')
        found=[d for d in snapshot.get('devices',[]) if d.get('observed_id',d['id'])==body.get('observed_id')]
        if len(found)!=1 or found[0].get('connection')=='mobile':raise ValueError('Eindeutiges verbundenes USB-Gerät auswählen')
        d=found[0];new=d['id']
        if any(r.get('device')==new for r in config.get('keys',[])+config.get('bindings',[])) or config['devices'].get(new,{}).get('deck_keys'):
            raise ValueError('Das neue Gerät hat eigene Belegungen; diese zuerst sichern und entfernen')
        previous=config['devices'][ident].get('hardware',{})
        if previous.get('vendor') and previous['vendor']!=d.get('vendor'):raise ValueError('Hersteller passt nicht zum gespeicherten Gerät')
        config['devices'][ident]['hardware']=descriptor(d)
        if new!=ident:config['devices'].pop(new,None)
    elif action=='remove':
        if ident not in config['devices'] and ident not in registry:raise ValueError('Gerät nicht gespeichert')
        removed={k['id'] for k in config.get('keys',[]) if k['device']==ident}
        config['devices'].pop(ident,None)
        config['keys']=[k for k in config.get('keys',[]) if k['device']!=ident]
        config['bindings']=[b for b in config.get('bindings',[]) if b['device']!=ident]
        writes['switches.json']={k:v for k,v in switches.items() if k not in removed}
        if ident in registry:
            registry.pop(ident);writes['mobile-devices.json']=registry
    elif action=='revoke':
        if ident not in trust:raise ValueError('Kopplung nicht gefunden')
        trust.pop(ident);writes['mobile-trust.json']=trust
    else:raise ValueError('Unbekannte Geräteaktion')
    # Save all affected metadata before changing anything. Icon files are untouched.
    names=['config.json','switches.json','mobile-devices.json','mobile-trust.json']
    before={name:read_json(home()/name,None) for name in names}
    folder=home()/'backups'/'device-actions';folder.mkdir(parents=True,exist_ok=True)
    backup=folder/(time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.tar.gz')
    with tarfile.open(backup,'w:gz') as archive:
        for name in names:
            if (home()/name).is_file():archive.add(home()/name,arcname=name)
    backup.chmod(0o600)
    applied=[]
    try:
        for name,value in writes.items():
            atomic_json(home()/name,value);applied.append(name)
        save_config(config)
    except Exception:
        if load_config()!=old:atomic_json(home()/'config.json',old)
        for name in reversed(applied):
            if before[name] is None:(home()/name).unlink(missing_ok=True)
            else:atomic_json(home()/name,before[name])
        raise
    return {'ok':True,'backup':str(backup)}
