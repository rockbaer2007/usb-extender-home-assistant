'use strict';
let config, status = {devices: [], events: [], brokers: {}, errors: {}}, iconList = [], page = 'overview', changed = false;
const $ = s => document.querySelector(s);
const el = (tag, text, cls) => { const e = document.createElement(tag); if(text !== undefined) e.textContent = text; if(cls) e.className = cls; return e; };
async function api(path, data) {
  const r = await fetch('/api/' + path, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-UGSo-Request':'1'},body:JSON.stringify(data)});
  const value = await r.json();
  if (!r.ok) { if(r.status === 401 && path !== 'login') showLogin(); throw new Error(value.error || 'Anfrage fehlgeschlagen'); }
  return value;
}
function error(e) { $('#error').textContent = e.message || String(e); $('#error').hidden = false; }
function notice(text) { $('#notice').textContent = text; $('#notice').hidden = false; }
function dirty() { changed = true; $('#save').disabled = false; $('#dirty').textContent = 'Ungespeicherte Änderungen'; }
function serviceAlive() { return typeof status.active === 'boolean' ? status.active : !!(status.updated && Math.abs(Date.now()/1000-status.updated)<15 && !status.stopped); }
function card(title, parent=$('#content')) { const c=el('article',undefined,'card'); if(title)c.append(el('h2',title)); parent.append(c); return c; }
function field(parent, label, value, change, type='text', choices=null) {
  const l=el('label', label), input=el(choices?'select':'input');
  if(choices) choices.forEach(([v,t])=>{const o=el('option',t);o.value=v;input.append(o);}); else input.type=type;
  if(type==='checkbox') { l.className='check';input.checked=!!value; l.prepend(input); } else {input.value=value??'';l.append(input);}
  input.addEventListener(type==='text'||type==='password'||type==='number'?'input':'change',()=>{change(type==='checkbox'?input.checked:type==='number'?Number(input.value):input.value);dirty();});
  parent.append(l);return input;
}
function routes(parent, selected, change) {
  const r=el('div',undefined,'route');
  config.brokers.forEach(b=>field(r,b.name,selected.includes(b.id),v=>{const next=v?[...selected,b.id]:selected.filter(x=>x!==b.id);selected=next;change(next);},'checkbox'));
  parent.append(r);
}
function button(parent, text, action, cls) { const b=el('button',text,cls); b.type='button';b.onclick=()=>Promise.resolve().then(action).catch(error);parent.append(b);return b; }
function empty(parent,title,text){const d=el('div',undefined,'empty');d.append(el('h2',title),el('p',text));parent.append(d);}
function render() {
  if(!config)return;
  $('#content').replaceChildren(); $('#notice').hidden=true;
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));
  $('#page-title').textContent={overview:'Dein Hub im Überblick',devices:'USB-Geräte',bindings:'Tasten & Anzeigen',brokers:'Bis zu drei MQTT-Broker',icons:'Deine Iconbibliothek',system:'System & Betrieb'}[page];
  ({overview,devices,bindings,brokers,icons,system})[page]();
}
function overview() {
  const grid=el('div',undefined,'grid');$('#content').append(grid);
  [['USB-Geräte',status.devices.length,'Vom Linux-System erkannt'],['Aktive Belegungen',config.bindings.length,'Tasten, Mediensteuerung und Anzeigen'],['MQTT-Verbindungen',Object.values(status.brokers).filter(x=>x==='online').length+' / 3','Jeder Broker arbeitet unabhängig']].forEach(([t,v,s])=>{const c=card(t,grid);c.append(el('div',String(v),'stat'),el('small',s));});
  const c=card('So richtest du deinen Hub ein');
  const list=el('ol');['Unter „MQTT-Broker“ mindestens eine Verbindung einrichten.','Unter „USB-Geräte“ das gewünschte Gerät ausdrücklich freigeben.','Taste drücken und das Ereignis unter „Tasten & Anzeigen“ übernehmen.','Zielbroker, Belegung und bei Stream Decks ein Icon auswählen.','Speichern. Danach kann die Weboberfläche per CLI abgeschaltet werden.'].forEach(t=>list.append(el('li',t)));c.append(list);
  if(!serviceAlive())c.append(el('p','USB-/MQTT-Dienst ist nicht aktiv oder liefert keinen aktuellen Status. Mit sudo systemctl status ugso-usbhub prüfen.','warning'));
  const note=card('Unterstützung');note.append(el('p','Alle USB-Geräte werden aufgelistet. Tastaturen und Medientasten werden über Linux evdev verarbeitet; unterstützte physische Stream Decks über den HID-Treiber. Andere Geräte sind zunächst nur in der Bestandsliste. Stream Deck Mobile ist kein direkt gekoppeltes USB-Gerät.'));
}
function devices() {
  if(!status.devices.length)empty($('#content'),'Noch kein USB-Gerät erkannt','USB-Geräte am Raspi einstecken. Die Bestandsliste wird alle fünf Sekunden aktualisiert.');
  const all=[...status.devices];Object.keys(config.devices).forEach(id=>{if(!all.some(d=>d.id===id))all.push({id,name:config.devices[id].name||id,kind:'offline',identity_hint:'Nicht verbunden; Einstellungen bleiben erhalten'});});
  all.forEach(d=>{
    const c=card(), row=el('div',undefined,'row spread');row.append(el('h2',d.name),el('span',d.kind,'badge'+(d.kind==='offline'?' offline':'')));c.append(row,el('div',d.id,'device-id'),el('small',d.identity_hint||''));
    const settings=config.devices[d.id] ||= {name:d.name,enabled:false,targets:[...config.default_targets],receive_broker:'',brightness:30};
    const fields=el('div',undefined,'fields');c.append(fields);
    field(fields,'Anzeigename',settings.name,v=>settings.name=v);
    field(fields,'Gerät für Eingaben freigeben',settings.enabled,v=>settings.enabled=v,'checkbox');
    field(fields,'Broker für Display-Rückmeldungen',settings.receive_broker,v=>settings.receive_broker=v,'select',[['','Keiner'],...config.brokers.map(b=>[b.id,b.name])]);
    const bright=field(fields,'Stream-Deck-Helligkeit (0–100)',settings.brightness,v=>settings.brightness=v,'number');bright.min=0;bright.max=100;
    c.append(el('div','Standardziele für dieses Gerät','route-title'));routes(c,settings.targets,v=>settings.targets=v);
    if(d.kind==='inventory')c.append(el('p','Für dieses Gerät gibt es noch keinen Eingabetreiber. Die Freigabe allein ergänzt kein herstellerspezifisches Protokoll.','warning'));
  });
}
function brokers() {
  const grid=el('div',undefined,'grid');$('#content').append(grid);
  config.brokers.forEach(b=>{
    const c=card(b.name,grid);c.append(el('span',status.brokers[b.id]||(b.enabled?'Warte auf Dienst':'Deaktiviert'),'badge'+(status.brokers[b.id]==='online'?'':' offline')));
    field(c,'Verbindung aktivieren',b.enabled,v=>b.enabled=v,'checkbox');
    const f=el('div',undefined,'fields');c.append(f);
    field(f,'Name',b.name,v=>b.name=v);field(f,'Host / IP',b.host,v=>b.host=v);
    field(f,'Port',b.port,v=>b.port=v,'number');field(f,'Benutzer',b.username,v=>b.username=v);
    const pw=field(f,b.password_set?'Passwort (leer = beibehalten)':'Passwort',b.password,v=>b.password=v,'password');pw.autocomplete='new-password';
    field(f,'Topic-Präfix',b.prefix,v=>b.prefix=v);
    field(c,'Gespeichertes Passwort löschen',false,v=>b.clear_password=v,'checkbox');
    field(c,'TLS mit Zertifikatsprüfung',b.tls,v=>b.tls=v,'checkbox');
    field(c,'Eigene CA-Datei auf dem Raspi (optional)',b.ca_file,v=>b.ca_file=v);
    field(c,'Discovery',b.discovery?'ha':'off',v=>b.discovery=v==='ha','select',[['off','Aus – nur MQTT-Daten senden'],['ha','Home Assistant – Geräteauslöser anmelden']]);
    c.append(el('p','Für ioBroker „Aus“ wählen. Die MQTT-Datenübertragung bleibt aktiv. Beim Abschalten werden bekannte eigene Discovery-Ankündigungen zurückgenommen.','muted'));
  });
  const c=card('Vorgabe für neue Geräte');routes(c,config.default_targets,v=>config.default_targets=v);c.append(el('p','Tastendrücke werden nicht gespeichert oder nach einer Verbindungsunterbrechung nachgesendet. MQTT-Rückmeldungen zur Anzeige kommen je Gerät von genau einem ausgewählten Broker.'));
}
function bindings() {
  const learn=card('Taste drücken und übernehmen');learn.append(el('p','Gerät zuerst freigeben und speichern. Mit „Übernehmen“ wird der tatsächliche Tastenname eingetragen. Danach die Belegung speichern. Erst passende Belegungen senden MQTT. „Gedrückt halten“ löst zusätzlich nach 0,7 Sekunden aus.'));
  const recent=el('div');learn.append(recent);renderEvents(recent,true);
  button(learn,'Leere Belegung hinzufügen',()=>addBinding());
  config.bindings.forEach((b,index)=>{
    const c=card();const row=el('div',undefined,'row spread');row.append(el('span','BELEGUNG '+(index+1),'binding-number'));button(row,'Entfernen',()=>{config.bindings.splice(index,1);dirty();render();},'danger');c.append(row);
    const f=el('div',undefined,'fields');c.append(f);
    field(f,'Gerät',b.device,v=>{b.device=v;refreshPreview();},'select',Object.keys(config.devices).map(id=>[id,config.devices[id].name||id]));
    const control=field(f,'Taste / Steuerelement',b.control,v=>b.control=v);
    control.placeholder='KEY_TAB (Tastatur) oder key:0 (Stream Deck)';
    field(f,'Ereignis',b.gesture,v=>b.gesture=v,'select',[['press','Drücken'],['release','Loslassen'],['hold','Gedrückt halten'],['repeat','Wiederholen'],['rotate_left','Links drehen'],['rotate_right','Rechts drehen'],['touch','Touch']]);
    field(f,'Text auf der Stream-Deck-Taste',b.text,v=>b.text=v);
    field(f,'Icon',b.icon,v=>b.icon=v,'select',[['','Kein Icon'],...iconList.map(i=>[i.id,i.collection+' · '+i.name])]);
    const inherit=field(f,'Geräteziele übernehmen',b.targets==null,v=>{b.targets=v?null:[];render();},'checkbox');
    if(b.targets!=null){c.append(el('div','An diese Broker senden','route-title'));routes(c,b.targets,v=>{b.targets=v;refreshPreview();});}
    const topicInput=field(c,'Sende-Topic (leer = automatisch)',b.topic,v=>{b.topic=v;refreshPreview();});
    topicInput.placeholder='z. B. haus/usb/tab';
    c.append(el('div','Tatsächliche MQTT-Ziele nach dem Speichern','route-title'));
    const preview=el('div');c.append(preview);
    function refreshPreview(){preview.replaceChildren();const targets=b.targets??config.devices[b.device]?.targets??config.default_targets;
      if(!targets.length){preview.append(el('p','Kein MQTT-Ziel ausgewählt.','warning'));return;}
      targets.forEach(id=>{const broker=config.brokers.find(x=>x.id===id);if(broker){const row=el('p');row.append(el('strong',broker.name+(broker.enabled?'':' (deaktiviert)')+' → '),el('code',b.topic||broker.prefix+'/event/'+b.device+'/'+b.id));preview.append(row);}});
    }refreshPreview();
    const more=el('details');more.append(el('summary','MQTT-Topic, Nutzdaten & Zustandsanzeige'));c.append(more);const advanced=el('div',undefined,'fields');more.append(advanced);
    [['Payload (leer = Ereignis als JSON)','payload'],['Zustands-Topic für Rückmeldung','state_topic'],['JSON-Feld, z. B. state (optional)','state_path'],['Wert für aktives Icon','on_value']].forEach(([name,key])=>field(advanced,name,b[key],v=>b[key]=v));
    field(advanced,'Aktives Icon',b.on_icon,v=>b.on_icon=v,'select',[['','Kein Icon'],...iconList.map(i=>[i.id,i.name])]);
    more.append(el('p','Rückmeldungen benötigen einen Empfangsbroker am Gerät. Home Assistant muss den Zustand auf das gewählte MQTT-Topic veröffentlichen.'));
  });
}
function addBinding(event) {
  const device=event?.device||Object.keys(config.devices)[0];
  if(!device)throw new Error('Zuerst unter USB-Geräte ein Gerät freigeben.');
  // getRandomValues also works on plain HTTP LAN addresses (randomUUID does not).
  const id=Array.from(crypto.getRandomValues(new Uint8Array(16)),n=>n.toString(16).padStart(2,'0')).join('');
  config.bindings.push({id,device,control:event?.control||'key:0',gesture:event?.gesture||'press',targets:null,text:'',icon:'',topic:'',payload:''});dirty();render();
}
function renderEvents(parent,learn=false) {
  parent.replaceChildren();const events=status.events.slice(0,learn?5:20);
  if(!events.length){parent.append(el('p','Noch keine Eingaben.'));return;}
  const wrap=el('div',undefined,'table-wrap'),t=el('table'),head=el('tr');['Zeit','Gerät','Taste','Ereignis','MQTT',...(learn?['']:[])].forEach(x=>head.append(el('th',x)));t.append(head);
  events.forEach(event=>{const row=el('tr');[new Date(event.time*1000).toLocaleTimeString(),config.devices[event.device]?.name||event.device,event.control,event.gesture].forEach(v=>row.append(el('td',v)));
    const delivery=el('td'),report=event.delivery;
    if(report){const labels={no_binding:'Keine passende gespeicherte Belegung',no_targets:'Kein MQTT-Ziel ausgewählt',not_connected:'Ziel deaktiviert oder nicht verbunden',sent:report.delivered+'× an MQTT übergeben'};delivery.append(el('div',labels[report.reason]||report.reason));
      (report.transmissions||[]).forEach(tx=>{const line=el('div');line.append(el('small',tx.name+' · '+({sent:'gesendet',offline:'offline',disabled:'deaktiviert',failed:'fehlgeschlagen'}[tx.state]||tx.state)+' · '+tx.topic));delivery.append(line);});
    }else delivery.textContent=event.delivered?event.delivered+'× an MQTT übergeben':'Nicht gesendet';
    row.append(delivery);if(learn){const action=el('td');button(action,'Übernehmen',()=>addBinding(event));row.append(action);}t.append(row);});wrap.append(t);parent.append(wrap);
}
function icons() {
  const c=card('Eigene Bilder und Elgato-Iconpacks');c.append(el('p','PNG, JPG, SVG, GIF und WebP; bei Animationen wird das erste Bild verwendet. ZIP und .streamDeckIconPack lokal hochladen. Es findet kein automatischer Marketplace-Download statt.'));
  const tools=el('div',undefined,'toolbar');c.append(tools);const label=el('label','Bild oder Iconpaket'),file=el('input');file.type='file';file.accept='.zip,.streamDeckIconPack,.png,.jpg,.jpeg,.svg,.gif,.webp';label.append(file);tools.append(label);
  button(tools,'Importieren',async()=>{if(!file.files[0])throw new Error('Bitte Datei auswählen.');const f=file.files[0];if(f.size>32*1024*1024)throw new Error('Datei ist größer als 32 MB.');const bytes=new Uint8Array(await f.arrayBuffer());let s='';for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode(...bytes.subarray(i,i+8192));const r=await api('icons/upload',{name:f.name,data:btoa(s)});iconList=await api('icons');render();notice(r.imported+' Icons importiert. '+(r.skipped?.length||0)+' übersprungen. '+JSON.stringify(r.skipped||[]));},'primary');
  const folder=el('div',undefined,'toolbar'),l=el('label','Ordner auf dem Raspi (wird in die Bibliothek kopiert)'),input=el('input');input.placeholder='/home/pi/meine-icons';l.append(input);folder.append(l);button(folder,'Ordner einlesen',async()=>{const r=await api('icons/folder',{path:input.value});iconList=await api('icons');render();notice(r.imported+' Icons importiert. '+JSON.stringify(r.skipped||[]));});c.append(folder);
  const search=el('input');search.placeholder='Icons nach Name, Sammlung oder Schlagwort suchen';c.append(search);const list=el('div',undefined,'icons');$('#content').append(list);
  function draw(){list.replaceChildren();iconList.filter(i=>(i.name+' '+i.collection+' '+i.tags.join(' ')).toLowerCase().includes(search.value.toLowerCase())).forEach(i=>{const tile=el('article',undefined,'icon-card'),img=el('img');img.src='/icons/'+i.id+'.png';img.alt=i.name;img.loading='lazy';tile.append(img,el('strong',i.name),el('small',i.collection),el('small',i.author));const detail=el('details');detail.append(el('summary','Lizenz & ID'),el('p',i.license||'Keine Lizenzangabe im Paket'),el('code',i.id));tile.append(detail);list.append(tile);});} search.oninput=draw;draw();
}
function system() {
  const c=card('Weboberfläche nur bei Bedarf');c.append(el('p','Das Schließen dieses Browserfensters beendet den Webdienst nicht. Mit „web stop“ wird der HTTP-Listener beendet. USB und MQTT laufen unabhängig weiter.'));
  c.append(el('pre','sudo ugso-usbhub web start    # jetzt starten\nsudo ugso-usbhub web stop     # jetzt abschalten\nsudo ugso-usbhub web status   # Status\nsudo ugso-usbhub web enable   # mit Autostart\nsudo ugso-usbhub web disable  # stoppen, ohne Autostart\nsudo ugso-usbhub backup       # Einstellungen und Icons sichern\nsudo journalctl -u ugso-usbhub -n 50'));
  c.append(el('p','Die Oberfläche verwendet HTTP im lokalen Netz. Nicht ins Internet freigeben. Für fremde Netze VPN oder einen HTTPS-Reverse-Proxy verwenden.','warning'));
  const d=card('Geräte- und Verbindungsdiagnose');Object.entries(status.errors||{}).forEach(([k,v])=>d.append(el('p',k+': '+v,'warning')));if(!Object.keys(status.errors||{}).length)d.append(el('p','Keine Gerätefehler gemeldet.'));
  const e=card('Letzte Eingaben (nur im Arbeitsspeicher)'),log=el('div');log.id='event-log';e.append(log);renderEvents(log);
  const f=card('Datenspeicherung');f.append(el('p','Einstellungen, Zugangsdaten und Icons liegen auf dem Raspi unter /var/lib/ugso-usbhub. Die letzten zehn Konfigurationsstände werden automatisch gesichert. Passwörter werden in der Oberfläche nicht zurückgeliefert. Geräte ohne Seriennummer werden über ihren USB-Port zugeordnet.'));
}
async function enter() { config=await api('config'); status=await api('status');iconList=await api('icons');$('#login').hidden=true;$('#workspace').hidden=false;$('#logout').hidden=false;$('#error').hidden=true;render(); }
function showLogin(){config=null;$('#login').hidden=false;$('#workspace').hidden=true;$('#logout').hidden=true;}
$('#login-form').onsubmit=async e=>{e.preventDefault();try{await api('login',{password:$('#password').value});$('#password').value='';await enter();}catch(e){error(e);}};
$('#logout').onclick=async()=>{if(changed&&!confirm('Ungespeicherte Änderungen verwerfen?'))return;await api('logout',{});changed=false;showLogin();};
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{page=b.dataset.page;render();});
$('#save').onclick=async()=>{try{await api('config',config);config=await api('config');changed=false;$('#save').disabled=true;$('#dirty').textContent='Gespeichert';$('#error').hidden=true;render();notice('Gespeichert. Der USB-/MQTT-Dienst übernimmt die Einstellungen innerhalb weniger Sekunden.');}catch(e){error(e);}};
setInterval(async()=>{if(!config)return;try{status=await api('status');$('#connection').textContent=serviceAlive()?'● USB-/MQTT-Dienst aktiv':'○ Dienst nicht aktiv';if(page==='bindings'){const target=$('#content article:first-child > div');if(target)renderEvents(target,true);}if(page==='system'&&$('#event-log'))renderEvents($('#event-log')); }catch(e){error(e);}},2500);
window.addEventListener('beforeunload',e=>{if(changed){e.preventDefault();e.returnValue='';}});
enter().catch(()=>{});
