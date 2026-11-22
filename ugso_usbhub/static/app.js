'use strict';
let config, savedConfig, status = {devices: [], events: [], brokers: {}, errors: {}}, iconList = [], page = 'overview', changed = false;
const $ = s => document.querySelector(s);
const cloneConfig = value => JSON.parse(JSON.stringify(value));
const el = (tag, text, cls) => { const e = document.createElement(tag); if(text !== undefined) e.textContent = text; if(cls) e.className = cls; return e; };
async function api(path, data) {
  const target=path==='icons'&&data===undefined?'icons/catalog':path;
  const r = await fetch('/api/' + target, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-UGSo-Request':'1'},body:JSON.stringify(data)});
  let value = await r.json();
  if (!r.ok) { if(r.status === 401 && path !== 'login') showLogin(); throw new Error(value.error || 'Anfrage fehlgeschlagen'); }
  if(path==='icons'&&Array.isArray(value.items))value=value.items.map(item=>({...item,license:item.license??(item.license_refs||[item.license_ref]).map(ref=>value.licenses?.[item.package_folder||item.collection||'Eigene Icons']?.[ref]||'').filter(Boolean).join('\n\n---\n\n')}));
  return value;
}
function error(e) { $('#error').textContent = e.message || String(e); $('#error').hidden = false; }
function notice(text) { $('#notice').textContent = text; $('#notice').hidden = false; }
function dirty() { changed = true; $('#save').disabled = !!learning; $('#dirty').textContent = 'Ungespeicherte Änderungen'; refreshKeyEditIndicators(); }
function serviceAlive() { return typeof status.active === 'boolean' ? status.active : !!(status.updated && Math.abs(Date.now()/1000-status.updated)<15 && !status.stopped); }
function renderStorage(){
  refreshTouchpadVisuals();
  refreshGamepadVisuals();
  refreshScannerVisuals();
  const node=$('#storage-space');if(!node)return;
  const disk=status.storage;
  if(!disk||!Number.isFinite(disk.free)||!Number.isFinite(disk.total)||disk.total<=0){node.textContent='Speicherplatz derzeit nicht verfügbar';return;}
  const size=bytes=>bytes>=1024**3?(bytes/1024**3).toLocaleString('de-DE',{maximumFractionDigits:2})+' GiB':(bytes/1024**2).toLocaleString('de-DE',{maximumFractionDigits:0})+' MiB';
  node.textContent='Speicher frei: '+size(disk.free)+' von '+size(disk.total);
  node.classList.toggle('storage-low',disk.free<Math.min(256*1024**2,disk.total*.05));
}
function card(title, parent=$('#content')) { const c=el('article',undefined,'card'); if(title)c.append(el('h2',title)); parent.append(c); return c; }
function field(parent, label, value, change, type='text', choices=null) {
  const l=el('label', label), input=el(choices?'select':'input');
  input.setAttribute('aria-label',label);
  if(choices) choices.forEach(([v,t])=>{const o=el('option',t);o.value=v;input.append(o);}); else input.type=type;
  if(type==='checkbox') { l.className='check';input.checked=!!value; l.prepend(input); } else {input.value=value??'';l.append(input);}
  input.addEventListener(type==='text'||type==='password'||type==='number'?'input':'change',()=>{change(type==='checkbox'?input.checked:type==='number'?Number(input.value):input.value);dirty();});
  parent.append(l);return input;
}
let pickerSource, pickerIndex, activeIconPicker, pickerLastPackage='', pickerFieldNumber=0;
function uniqueIconEntries(items){
  const result=[],seen=new Map();
  for(const item of items){
    const key=JSON.stringify([item.package_folder||item.collection||'Eigene Icons',item.id]);
    if(!seen.has(key)){const copy={...item,tags:[...(item.tags||[])],aliases:[...(item.aliases||[])]};seen.set(key,copy);result.push(copy);continue;}
    const primary=seen.get(key),alias={name:item.name,filename:item.filename,subfolder:item.subfolder,tags:item.tags||[],original_path:item.original_path};
    if(!primary.aliases.some(a=>a.filename===alias.filename&&a.original_path===alias.original_path))primary.aliases.push(alias);
    primary.aliases.push(...(item.aliases||[]));primary.tags=[...new Set([...primary.tags,...(item.tags||[])])];
  }
  return result;
}
function iconSearchText(item){return [item.name,item.filename,item.collection,item.package_folder,item.subfolder,...(item.tags||[]),...(item.aliases||[]).flatMap(a=>[a.name,a.filename,a.subfolder,...(a.tags||[])])].filter(Boolean).join(' ').toLocaleLowerCase();}
function iconAliasText(item){return (item.aliases||[]).map(a=>a.filename||a.name).filter(Boolean).join(', ');}
function iconPickerIndex(){
  if(pickerSource===iconList)return pickerIndex;
  pickerSource=iconList;const byId=new Map(),packs=new Map();
  for(const item of uniqueIconEntries(iconList)){
    const key=item.package_folder||item.collection||'Eigene Icons';
    if(!packs.has(key))packs.set(key,{key,name:item.collection||key,items:[]});
    const entry={item,search:iconSearchText(item)};
    packs.get(key).items.push(entry);byId.set(item.id,item);
  }
  return pickerIndex={byId,packs:[...packs.values()],items:[...packs.values()].flatMap(p=>p.items.map(e=>e.item))};
}
function iconField(parent,label,value,change,emptyLabel='Kein Icon'){
  const wrap=el('div',undefined,'icon-picker-field'),caption=el('span',label),id='icon-field-'+(++pickerFieldNumber);
  caption.id=id;wrap.append(caption);parent.append(wrap);
  let current=value||'';
  const choose=button(wrap,'',()=>openIconPicker({label,value:current,emptyLabel,onChoose(next){if(next===current)return;current=next;change(next);update();dirty();}}),'icon-picker-trigger');
  choose.setAttribute('aria-label',label);choose.setAttribute('aria-haspopup','dialog');
  function update(){
    const item=iconPickerIndex().byId.get(current);choose.replaceChildren();
    if(current){const img=el('img');img.alt='';img.width=24;img.height=24;img.loading='lazy';img.src='/thumbnails/'+current+'.png';choose.append(img);}
    const text=el('span',item?.name||(current?'Gespeichertes Icon nicht in der Bibliothek':emptyLabel));choose.append(text,el('span','▦','icon-picker-symbol'));
    choose.title=item?[item.name,item.collection,item.filename].filter(Boolean).join(' · '):emptyLabel;choose.dataset.icon=current;
  }
  update();return choose;
}
function closeIconPicker(){if(activeIconPicker)activeIconPicker();}
function openIconPicker({label,value='',emptyLabel='Kein Icon',onChoose}){
  closeIconPicker();const index=iconPickerIndex(),priorFocus=document.activeElement;
  const dialog=el('dialog',undefined,'icon-picker-dialog');dialog.setAttribute('aria-label','Icon auswählen · '+label);
  const heading=el('div',undefined,'icon-picker-heading');heading.append(el('h2','Icon auswählen'),el('small',label));dialog.append(heading);
  const search=el('input');search.type='search';search.placeholder='In Icons suchen …';search.setAttribute('aria-label','In Icons suchen');dialog.append(search);
  const body=el('div',undefined,'icon-picker-body'),count=el('small'),list=el('div');count.setAttribute('role','status');body.append(count,list);dialog.append(body);
  const footer=el('div',undefined,'icon-picker-footer'),preview=el('div',undefined,'icon-picker-selection'),actions=el('div',undefined,'row');footer.append(preview,actions);dialog.append(footer);
  let chosen=value,filterTimer,closed=false,opened='',observer;
  const selected=index.byId.get(value);
  opened=selected?(selected.package_folder||selected.collection||'Eigene Icons'):pickerLastPackage;
  if(typeof IntersectionObserver!=='undefined')observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){const img=entry.target;img.src=img.dataset.src;observer.unobserve(img);}},{root:body,rootMargin:'120px'});
  function cleanupImages(node){node.querySelectorAll('img[data-src]').forEach(img=>observer?.unobserve(img));}
  function image(item){const img=el('img');img.alt='';img.width=48;img.height=48;img.decoding='async';img.dataset.src='/thumbnails/'+item.id+'.png';if(observer)observer.observe(img);else{img.loading='lazy';img.src=img.dataset.src;}return img;}
  function close(){if(closed)return;closed=true;clearTimeout(filterTimer);observer?.disconnect();activeIconPicker=null;dialog.remove();if(priorFocus?.isConnected)priorFocus.focus();}
  activeIconPicker=close;
  function apply(){const next=chosen;close();onChoose(next);}
  button(actions,emptyLabel,()=>{chosen='';showSelection();});
  const accept=button(actions,'Übernehmen',apply,'primary');button(actions,'Abbrechen',close);
  function showSelection(){
    preview.replaceChildren();const item=index.byId.get(chosen);
    if(item){const img=image(item);observer?.unobserve(img);img.src=img.dataset.src;preview.append(img);const text=el('span');text.append(el('strong',item.name),el('small',[item.collection,item.filename,item.aliases?.length?'Weitere Namen: '+iconAliasText(item):'',item.animated?'Animation · Miniatur zeigt erstes Bild':''].filter(Boolean).join(' · ')));text.title=text.textContent;preview.append(text);}
    else preview.append(el('span',chosen?'Gespeichertes Icon bleibt erhalten':emptyLabel));
    accept.disabled=false;
    dialog.querySelectorAll('.icon-picker-tile').forEach(tile=>{tile.setAttribute('aria-pressed',String(tile.dataset.icon===chosen));});
  }
  function renderPacks(){
    cleanupImages(list);list.replaceChildren();const query=search.value.toLocaleLowerCase().trim(),matches=[];
    for(const pack of index.packs){const items=query?pack.items.filter(entry=>entry.search.includes(query)):pack.items;if(items.length)matches.push({...pack,items});}
    count.textContent=matches.reduce((total,pack)=>total+pack.items.length,0)+' Icons · '+matches.length+' Pakete · 48×48-Miniaturen';
    if(query&&!matches.some(p=>p.key===opened))opened=matches[0]?.key||'';
    if(!matches.length){list.append(el('p',query?'Keine passenden Icons.':'Noch keine Icons importiert.'));return;}
    for(const pack of matches){
      const details=el('details',undefined,'icon-picker-package'),summary=el('summary',pack.name+' ('+pack.items.length+')');details.append(summary);list.append(details);
      let pageNumber=0,content;
      const selectedAt=pack.items.findIndex(e=>e.item.id===chosen);if(selectedAt>=0)pageNumber=Math.floor(selectedAt/96);
      function populate(){
        if(content){cleanupImages(content);content.remove();}content=el('div');details.append(content);
        const grid=el('div',undefined,'icon-picker-grid');content.append(grid);
        const start=pageNumber*96;
        for(const {item} of pack.items.slice(start,start+96)){
          const tile=button(grid,'',()=>{chosen=item.id;showSelection();},'icon-picker-tile');tile.dataset.icon=item.id;
          tile.setAttribute('aria-label',item.name+' · '+(item.filename||item.name));tile.setAttribute('aria-pressed',String(item.id===chosen));
          tile.title=[item.name,item.filename,item.subfolder,item.aliases?.length?'Weitere Namen: '+iconAliasText(item):'',item.animated?'Animiert · Auswahl zeigt erstes Bild':''].filter(Boolean).join('\n');tile.append(image(item));tile.ondblclick=()=>{chosen=item.id;apply();};
          const failed=tile.querySelector('img');failed.onerror=()=>{tile.classList.add('icon-picker-failed');tile.title+='\nMiniatur konnte nicht geladen werden';};
        }
        if(pack.items.length>96){const pager=el('div',undefined,'icon-picker-pager');content.append(pager);
          const previous=button(pager,'‹ Zurück',()=>{pageNumber--;populate();summary.scrollIntoView?.({block:'nearest'});});previous.disabled=pageNumber===0;
          pager.append(el('span',(start+1)+'–'+Math.min(start+96,pack.items.length)+' von '+pack.items.length));
          const next=button(pager,'Weiter ›',()=>{pageNumber++;populate();summary.scrollIntoView?.({block:'nearest'});});next.disabled=start+96>=pack.items.length;
        }
      }
      details.addEventListener('toggle',()=>{
        if(!details.isConnected)return;
        if(details.open){opened=pack.key;pickerLastPackage=pack.key;for(const other of list.querySelectorAll('details'))if(other!==details)other.open=false;if(!content)populate();}
        else if(content){cleanupImages(content);content.remove();content=null;}
      });
      if(opened===pack.key){details.open=true;populate();}
    }
  }
  search.oninput=()=>{clearTimeout(filterTimer);filterTimer=setTimeout(renderPacks,120);};
  dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
  dialog.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();close();return;}if(event.key==='Tab'){const nodes=[...dialog.querySelectorAll('input,button,summary')].filter(n=>!n.disabled&&(!n.closest('details')||n.tagName==='SUMMARY'||n.closest('details').open));const first=nodes[0],last=nodes.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}});
  footer.append(el('small','Icon markieren und übernehmen (oder doppelklicken). Danach oben speichern.'));
  document.body.append(dialog);if(typeof dialog.showModal==='function')dialog.showModal();else dialog.setAttribute('open','');
  showSelection();renderPacks();search.focus();
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
  closeIconPicker();
  renderStorage();
  updateDeckTab();
  $('#content').replaceChildren(); $('#notice').hidden=true;
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.page===page));
  $('#page-title').textContent={overview:'Dein Hub im Überblick',devices:'USB / Virtuelle Geräte',bindings:'Tasten & Anzeigen',streamdeck:'Stream Deck',mobile:'Stream Deck Mobile',brokers:'Bis zu drei MQTT-Broker',icons:'Deine Iconbibliothek',system:'System & Betrieb'}[page];
  ({overview,devices,bindings,streamdeck,mobile,brokers,icons,system})[page]();
}
function overview() {
  const grid=el('div',undefined,'grid');$('#content').append(grid);
  [['USB / Virtuelle Geräte',status.devices.length,'Vom Linux-System erkannt'],['Aktive Belegungen',config.bindings.length+(config.keys||[]).filter(k=>k.enabled!==false).length,'Tasten, Mediensteuerung und Anzeigen'],['MQTT-Verbindungen',Object.values(status.brokers).filter(x=>x==='online').length+' / 3','Jeder Broker arbeitet unabhängig']].forEach(([t,v,s])=>{const c=card(t,grid);c.append(el('div',String(v),'stat'),el('small',s));});
  const c=card('So richtest du deinen Hub ein');
  const list=el('ol');['Unter „MQTT-Broker“ mindestens eine Verbindung einrichten.','Unter „USB / Virtuelle Geräte“ das gewünschte Gerät ausdrücklich freigeben.','Taste drücken und das Ereignis unter „Tasten & Anzeigen“ übernehmen.','Zielbroker, Belegung und bei Stream Decks ein Icon auswählen.','Speichern. Danach kann die Weboberfläche per CLI abgeschaltet werden.'].forEach(t=>list.append(el('li',t)));c.append(list);
  if(!serviceAlive())c.append(el('p','USB-/MQTT-Dienst ist nicht aktiv oder liefert keinen aktuellen Status. Mit sudo systemctl status ugso-usbhub prüfen.','warning'));
  const note=card('Unterstützung');note.append(el('p','Alle USB-Geräte werden aufgelistet. Tastaturen und Medientasten werden über Linux evdev verarbeitet; unterstützte physische Stream Decks über den HID-Treiber. Andere Geräte sind zunächst nur in der Bestandsliste. Stream Deck Mobile ist kein direkt gekoppeltes USB-Gerät.'));
}
async function deviceAction(action,device,observed_id){
  if(changed||learning||learnedDraft.length)throw new Error('Änderungen zuerst speichern und Anlernen beenden.');
  const result=await api('devices',{action,device,observed_id});
  if(action==='remove'){
    knownDecks.delete(device);editorPages.delete(device);
    if(device.startsWith('mobile-'))forgottenDecks.add(device);
    if(deckDevice===device){deckDevice='';deckKey=0;}
    if(openKeyDevice===device){openKeyDevice=null;openKeyEntry=null;}
  }
  config=await api('config');savedConfig=cloneConfig(config);status=await api('status');keyEditBaseline.clear();render();
  notice('Gespeichert. Sicherung der betroffenen Einstellungen: '+result.backup);
}
const touchpadDirections=[['UP','Unten → oben'],['DOWN','Oben → unten'],['RIGHT','Links → rechts'],['LEFT','Rechts → links'],['UP_RIGHT','Links unten → rechts oben'],['DOWN_LEFT','Rechts oben → links unten'],['DOWN_RIGHT','Links oben → rechts unten'],['UP_LEFT','Rechts unten → links oben']];
const touchpadPreviewValues=new Map(),touchpadLastTriggers=new Map();
function markTouchpadBinding(entry,device,control){
  if(control.startsWith('TOUCHPAD_SLIDE_')&&config.devices[device]?.touchpad_mode==='faders'){
    entry.classList.add('touchpad-binding-paused');entry.querySelector('summary')?.append(el('small',' · Flächenmodus: pausiert','touchpad-paused-label'));
  }
}
function refreshTouchpadVisuals(){
  if(!config)return;
  for(const event of status.events||[]){
    if(!/^TOUCHPAD_(SLIDE_|FADER_)/.test(event.control))continue;
    const id=event.device+'|'+event.control;
    if(event.gesture==='value'&&(!touchpadPreviewValues.has(id)||event.time>touchpadPreviewValues.get(id).time))touchpadPreviewValues.set(id,event);
    if(['value','press'].includes(event.gesture)&&(!touchpadLastTriggers.has(event.device)||event.time>touchpadLastTriggers.get(event.device).time))touchpadLastTriggers.set(event.device,event);
  }
  for(const view of document.querySelectorAll('.touchpad-mode-view')){
    const device=view.dataset.device,settings=config.devices[device]||{},mode=settings.touchpad_mode||'directions';
    const ready=!!settings.enabled&&!!settings.touchpad_gestures,saved=(savedConfig.devices[device]?.touchpad_mode||'directions')===mode;
    view.dataset.mode=mode;view.querySelector('.touchpad-mode-status').textContent=(mode==='faders'?'Fünf Regler aktiv · Richtungsaktionen pausiert':'Acht Richtungen aktiv · Regler pausiert')+(!ready?' · Gerät/Gesten ausgeschaltet':'')+(!saved?' · Vorschau, noch nicht gespeichert':'');
    for(const tile of view.querySelectorAll('[data-control]')){
      const active=ready&&tile.dataset.mode===mode&&(mode!=='faders'||settings.touchpad_faders?.[tile.dataset.lane]?.enabled!==false);
      const event=touchpadPreviewValues.get(device+'|'+tile.dataset.control),last=touchpadLastTriggers.get(device);
      tile.classList.toggle('touchpad-tile-disabled',!active);
      const recent=active&&saved&&last?.control===tile.dataset.control&&Date.now()/1000-last.time<6;
      tile.classList.toggle('touchpad-tile-triggered',recent);
      tile.querySelector('.touchpad-tile-value').textContent=!active?'Pausiert':!saved?'Vorschau':event?String(event.value):'Bereit';
      tile.setAttribute('aria-label',tile.dataset.name+' · '+(active?'aktiv':'pausiert')+(recent?' · letzter Trigger':''));
      const bar=tile.querySelector('.touchpad-fader-fill');if(bar)bar.style.height=active&&saved&&event?Math.max(0,Math.min(100,event.value))+'%':'0%';
    }
  }
}
const gamepadAxes=[['left_x','Linker Stick X','ABS_X'],['left_y','Linker Stick Y','ABS_Y'],['right_x','Rechter Stick X','ABS_RX'],['right_y','Rechter Stick Y','ABS_RZ']];
function refreshScannerVisuals(){
  if(!config)return;
  for(const node of document.querySelectorAll('.scanner-last')){
    const settings=config.devices[node.dataset.device]||{},saved=savedConfig.devices[node.dataset.device]||{};
    const event=(status.events||[]).find(e=>e.device===node.dataset.device&&e.control==='BARCODE_SCAN'&&e.gesture==='scan');
    node.textContent=!settings.enabled||!settings.scanner_enabled?'Scanner pausiert':!saved.scanner_enabled?'Vorschau · erst speichern':event?'Letzter Scan: '+event.value:'Bereit · noch kein Scan empfangen';
  }
}
const gamepadPreviewValues=new Map();
function refreshGamepadVisuals(){
  if(!config)return;
  for(const event of status.events||[]){
    if(event.gesture!=='value'||!/^GAMEPAD_(LEFT|RIGHT)_[XY]$/.test(event.control))continue;
    const key=event.device+'|'+event.control;if(!gamepadPreviewValues.has(key)||event.time>gamepadPreviewValues.get(key).time)gamepadPreviewValues.set(key,event);
  }
  for(const tile of document.querySelectorAll('.gamepad-axis-tile')){
    const settings=config.devices[tile.dataset.device]||{},active=settings.enabled&&settings.gamepad_axes_enabled&&settings.gamepad_axes?.[tile.dataset.axis]?.enabled!==false;
    const value=gamepadPreviewValues.get(tile.dataset.device+'|GAMEPAD_'+tile.dataset.axis.toUpperCase());
    const saved=!!savedConfig.devices[tile.dataset.device]?.gamepad_axes_enabled===!!settings.gamepad_axes_enabled;
    tile.classList.toggle('touchpad-tile-disabled',!active);
    tile.querySelector('output').textContent=!active?'Pausiert':!saved?'Vorschau':value?String(value.value):'Bereit';
    tile.querySelector('meter').value=active&&saved&&value?value.value:50;
  }
}
function devices() {
  if(!status.devices.length)empty($('#content'),'Noch kein USB-Gerät erkannt','USB-Geräte am Raspi einstecken. Die Bestandsliste wird alle fünf Sekunden aktualisiert.');
  const all=status.devices.filter(d=>!(d.connection==='mobile'&&forgottenDecks.has(d.id)));Object.keys(config.devices).forEach(id=>{if(!all.some(d=>d.id===id))all.push({id,name:config.devices[id].name||id,kind:'offline',identity_hint:'Nicht verbunden; Einstellungen bleiben erhalten'});});
  for(const d of status.mobile?.known_decks||[])if(!all.some(x=>x.id===d.id)&&!forgottenDecks.has(d.id))all.push({...d,kind:'offline',connection:'mobile'});
  all.forEach(d=>{
    const c=card(), row=el('div',undefined,'row spread');row.append(el('h2',d.name),el('span',d.kind,'badge'+(d.kind==='offline'?' offline':'')));c.append(row,el('div',d.id,'device-id'),el('small',d.identity_hint||''));
    const settings=config.devices[d.id] ||= {name:d.name,enabled:false,targets:[...config.default_targets],receive_broker:'',brightness:30};
    const fields=el('div',undefined,'fields');c.append(fields);
    field(fields,'Anzeigename',settings.name,v=>settings.name=v);
    field(fields,'Gerät für Eingaben freigeben',settings.enabled,v=>settings.enabled=v,'checkbox');
    field(fields,'Broker für Display-Rückmeldungen',settings.receive_broker,v=>settings.receive_broker=v,'select',[['','Keiner'],...config.brokers.map(b=>[b.id,b.name])]);
    const bright=field(fields,'Stream-Deck-Helligkeit (0–100)',settings.brightness,v=>settings.brightness=v,'number');bright.min=0;bright.max=100;
    if(d.kind==='input'||(d.kind==='offline'&&d.connection!=='mobile'&&!d.id.startsWith('mobile-'))){
      const scanner=el('details',undefined,'scanner-options');c.append(scanner);scanner.append(el('summary','Barcode-/QR-Scanner · USB-Tastatur'));
      const controls=el('fieldset',undefined,'fields');
      field(scanner,'Als Barcode-/QR-Scanner verwenden',!!settings.scanner_enabled,v=>{settings.scanner_enabled=v;controls.disabled=!v;refreshScannerVisuals();},'checkbox');
      scanner.append(controls);controls.disabled=!settings.scanner_enabled;
      field(controls,'Scanner-Tastaturlayout',settings.scanner_layout||'de',v=>settings.scanner_layout=v,'select',[['de','Deutsch (DE)'],['us','Englisch (US)']]);
      field(controls,'Scanner-Abschluss',settings.scanner_terminator||'enter',v=>settings.scanner_terminator=v,'select',[['enter','Enter (empfohlen)'],['tab','Tab'],['timeout','Scanpause']]);
      const timeout=field(controls,'Scanner-Pause (100–3000 ms)',settings.scanner_timeout_ms??500,v=>settings.scanner_timeout_ms=v,'number');timeout.min=100;timeout.max=3000;timeout.step=50;
      const topic=field(controls,'Scanner-Topic',settings.scanner_topic||'',v=>settings.scanner_topic=v);topic.placeholder='Leer = beim Speichern automatisch anlegen';
      field(scanner,'HA-Tag-URLs als Tag-ID senden',settings.scanner_ha_urls!==false,v=>settings.scanner_ha_urls=v,'checkbox');
      const output=el('output',undefined,'scanner-last');output.dataset.device=d.id;output.setAttribute('aria-live','polite');scanner.append(output);
      scanner.append(el('p','Scanner auf USB-Tastaturmodus und dasselbe DE-/US-Layout einstellen. Enter als Abschluss empfohlen. Scanpause beendet im Pausenmodus einen Scan; bei Enter/Tab verwirft sie unvollständige Eingaben. Maximal 4096 UTF-8-Bytes, druckbare Zeichen.'));
      scanner.append(el('small','Kein Anlernen erforderlich. Im Scanner-Modus pausieren vorhandene Tasten-, Touchpad- und Gamepad-Aktionen; die Einstellungen bleiben gespeichert. Geräte-Zielbroker gelten. HA-Discovery am HA-Broker einschalten: MQTT-Tag-Scanner erzeugt tag_scanned. Gleiche Codes lösen bei jedem Scan erneut aus. Inhalte werden nicht ausgeführt.'));
    }
    if(isDragonrise(d.id)&&!settings.scanner_enabled){
      const gamepad=el('details',undefined,'gamepad-options');c.append(gamepad);gamepad.append(el('summary','Gamepad · DragonRise 0079:0006'));
      field(gamepad,'Stickwerte per MQTT senden (0–100)',!!settings.gamepad_axes_enabled,v=>{settings.gamepad_axes_enabled=v;if(v)settings.gamepad_profile='dragonrise-0079-0006';refreshGamepadVisuals();},'checkbox');
      const rate=field(gamepad,'Gamepad-Senderate je Achse (1–30/s)',settings.gamepad_rate??10,v=>settings.gamepad_rate=v,'number');rate.min=1;rate.max=30;rate.step=1;
      const axes=el('div',undefined,'fields');gamepad.append(axes);
      for(const [name,label,raw] of gamepadAxes){
        const value=(settings.gamepad_axes ||= {})[name] ||= {enabled:true,topic:''},row=el('div');axes.append(row);
        field(row,label+' · Wert senden',value.enabled!==false,v=>{value.enabled=v;refreshGamepadVisuals();},'checkbox');
        const topic=field(row,label+' · Topic',value.topic,v=>value.topic=v);topic.placeholder='Leer = beim Speichern automatisch anlegen';
        const tile=el('div',undefined,'gamepad-axis-tile');Object.assign(tile.dataset,{device:d.id,axis:name});row.append(tile);
        tile.append(el('small',raw),el('output','Bereit'));const meter=el('meter');meter.min=0;meter.max=100;meter.value=50;meter.setAttribute('aria-label',label+' · letzter Wert');tile.append(meter);
      }
      gamepad.append(el('p','Analogmodus am Gamepad verwenden. Vier Stickachsen: 0–100, Mitte 50; die vom Gerät gemeldete Totzone beruhigt die Mitte. ABS_Z wird ignoriert. Eigene Topics und HA-Sensoren am selben Gerät; Geräte-Zielbroker gelten. Änderungen erst speichern.'));
      gamepad.append(el('small','Schultertasten und Stick-Klicks unter „Tasten & Anzeigen“ anlernen: L1 = BTN_BASE, R1 = BTN_BASE2, L2 = BTN_TOP2, R2 = BTN_PINKIE, linker Klick = BTN_BASE5, rechter Klick = BTN_BASE6. L2/R2 sind digitale Tasten. Vorhandene Belegungen und Linux-IDs bleiben erhalten.'));
    }
    if(!settings.scanner_enabled&&!isDragonrise(d.id)&&(d.kind==='input'||(d.kind==='offline'&&!d.id.startsWith('mobile-')))){
      field(fields,'Touchpad-Gesten auswerten',!!settings.touchpad_gestures,v=>settings.touchpad_gestures=v,'checkbox');
      c.append(el('small','Für T650 und andere Multitouch-Touchpads: Tippen, Ein-Finger-Slide, Scrollen, Wischen und Pinch anlernen. Zuerst freigeben, Gesten aktivieren und speichern.'));
      const options=el('details',undefined,'touchpad-options');options.append(el('summary','Ein-Finger-Slide und optionale X/Y-Werte'));c.append(options);
      const controls=el('div',undefined,'fields');options.append(controls);
      const modeInput=field(controls,'Touchpad-Modus',settings.touchpad_mode||'directions',v=>{settings.touchpad_mode=v;updateMode();},'select',[['directions','Acht Slide-Richtungen'],['faders','Flächenmodus · fünf senkrechte Regler']]);
      const sensitivity=field(controls,'Slide-Empfindlichkeit (1–10)',settings.touchpad_sensitivity??5,v=>settings.touchpad_sensitivity=v,'number');sensitivity.min=1;sensitivity.max=10;sensitivity.step=1;
      const rate=field(controls,'Slide-/X/Y-Senderate (1–30/s)',settings.touchpad_rate??10,v=>settings.touchpad_rate=v,'number');rate.min=1;rate.max=30;rate.step=1;
      field(options,'X/Y-Werte zusätzlich per MQTT senden (0–100)',!!settings.touchpad_xy,v=>settings.touchpad_xy=v,'checkbox');
      const topics=el('div',undefined,'fields');options.append(topics);
      for(const axis of ['x','y']){const input=field(topics,axis.toUpperCase()+'-Topic',settings['touchpad_'+axis+'_topic']||'',v=>settings['touchpad_'+axis+'_topic']=v);input.placeholder='Leer = beim Speichern automatisch anlegen';}
      const slideValues=el('details');options.append(slideValues);slideValues.append(el('summary','Richtungswerte einzeln aktivieren (0–100)'));
      const valueFields=el('fieldset',undefined,'fields');slideValues.append(valueFields);
      for(const [direction,label] of touchpadDirections){
        const values=settings.touchpad_slide_values ||= {};const value=values[direction] ||= {enabled:false,topic:''};
        const row=el('div');valueFields.append(row);
        field(row,label+' · Wert senden',!!value.enabled,v=>value.enabled=v,'checkbox');
        const input=field(row,label+' · Topic',value.topic,v=>value.topic=v);input.placeholder='Leer = beim Speichern automatisch anlegen';
      }
      slideValues.append(el('small','Absolute Position auf der gesamten Fläche: oben und rechts 100, unten und links 0. Diagonal: Mittelwert der beiden Achsen entlang der Diagonale; Gegenrichtung zählt zurück. Nur die erkannte Richtung sendet. Kurze Wege nutzen einen Teilbereich. Senderate und Empfindlichkeit gelten auch hier. HA-Discovery meldet aktivierte Werte und X/Y als Sensoren am selben Gerät an, wenn Discovery beim Zielbroker eingeschaltet ist.'));
      const faders=el('details',undefined,'touchpad-fader-settings');options.append(faders);faders.append(el('summary','Fünf senkrechte Regler · Topics'));
      const faderFields=el('fieldset',undefined,'fields');faders.append(faderFields);
      for(let lane=1;lane<=5;lane++){
        const values=settings.touchpad_faders ||= {},value=values[lane] ||= {enabled:true,topic:''},row=el('div');faderFields.append(row);
        field(row,'Regler '+lane+' · Wert senden',value.enabled!==false,v=>{value.enabled=v;refreshTouchpadVisuals();},'checkbox');
        const input=field(row,'Regler '+lane+' · Topic',value.topic,v=>value.topic=v);input.placeholder='Leer = beim Speichern automatisch anlegen';
      }
      faders.append(el('small','Fünf gleich breite Streifen von links nach rechts. Aufsetzen wählt den Regler bis zum Abheben, auch bei seitlichem Verrutschen. Nur vertikales Schieben aktiviert: unten 0, oben 100. Neue Regler sind im Flächenmodus standardmäßig aktiv. X/Y bleibt unabhängig.'));
      const view=el('div',undefined,'touchpad-mode-view');view.dataset.device=d.id;view.append(el('p',undefined,'touchpad-mode-status'));options.insertBefore(view,slideValues);
      view.append(el('small','Türkis: Regler aktiv · Gold: Richtungsaktionen aktiv · Grau: pausiert · Leuchtender Rand: letzter Trigger (bis zu 6 s). Aktualisierung bei geöffneter Oberfläche, kein Tastenbild-/Geräte-Upload.'));
      const compass=el('div',undefined,'touchpad-compass'),strips=el('div',undefined,'touchpad-strips');view.append(compass,strips);
      for(const direction of ['UP_LEFT','UP','UP_RIGHT','LEFT','','RIGHT','DOWN_LEFT','DOWN','DOWN_RIGHT']){
        if(!direction){compass.append(el('span','8 Richtungen','touchpad-compass-center'));continue;}
        const tile=el('div',undefined,'touchpad-direction-tile');tile.dataset.control='TOUCHPAD_SLIDE_'+direction;tile.dataset.mode='directions';tile.dataset.name=touchpadDirections.find(x=>x[0]===direction)[1];tile.append(el('strong',direction.replaceAll('_',' ')),el('span','Bereit','touchpad-tile-value'));compass.append(tile);
      }
      for(let lane=1;lane<=5;lane++){
        const tile=el('div',undefined,'touchpad-fader-tile');Object.assign(tile.dataset,{control:'TOUCHPAD_FADER_'+lane,mode:'faders',name:'Regler '+lane,lane:String(lane)});
        tile.append(el('div',undefined,'touchpad-fader-fill'),el('strong','Regler '+lane),el('span','Bereit','touchpad-tile-value'));strips.append(tile);
      }
      function updateMode(){const faderMode=modeInput.value==='faders';valueFields.disabled=faderMode;faderFields.disabled=!faderMode;slideValues.classList.toggle('touchpad-settings-paused',faderMode);faders.classList.toggle('touchpad-settings-paused',!faderMode);if(faderMode)faders.open=true;refreshTouchpadVisuals();}
      updateMode();
      options.append(el('small','10 = empfindlich, 1 = größere Bewegung nötig. Acht Richtungen im Anlernmodus: TOUCHPAD_SLIDE_LEFT/RIGHT/UP/DOWN sowie UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT. X/Y ist standardmäßig aus, nutzt die Geräte-Zielbroker und sendet reine Zahlen, kein JSON. X: links 0 → rechts 100; Y: oben 0 → unten 100. Kein zusätzlicher Tipp nach Schieben.'));
    }
    c.append(el('div','Standardziele für dieses Gerät','route-title'));routes(c,settings.targets,v=>settings.targets=v);
    if(d.kind==='inventory')c.append(el('p','Für dieses Gerät gibt es noch keinen Eingabetreiber. Die Freigabe allein ergänzt kein herstellerspezifisches Protokoll.','warning'));
    const actions=el('div',undefined,'row');c.append(actions);
    if(savedConfig.devices[d.id]||(status.mobile?.known_decks||[]).some(x=>x.id===d.id)){
      const remove=button(actions,'🗑 Gerät entfernen',async()=>{
        if(confirm('„'+settings.name+'“ mit Tasten, Seiten und MQTT-Zuordnungen entfernen? Iconpakete und die Mobile-Kopplung bleiben erhalten. Ein angeschlossenes USB-Gerät erscheint danach nicht freigegeben.'))await deviceAction('remove',d.id);
      },'danger');remove.setAttribute('aria-label','Gerät entfernen: '+settings.name);
    }
    if(d.kind!=='offline'&&d.connection!=='mobile'){
      const choices=Object.entries(savedConfig.devices).filter(([id,s])=>id!==d.id&&!id.startsWith('mobile-')&&!status.devices.some(x=>x.id===id)&&(!s.hardware?.vendor||s.hardware.vendor===d.vendor));
      if(choices.length){
        let target=choices[0][0];field(actions,'Vorhandenem Gerät zuordnen',target,v=>target=v,'select',choices.map(([id,s])=>[id,s.name||id]));
        button(actions,'Zuordnung übernehmen',async()=>{if(confirm('Dieses USB-Gerät dem gespeicherten Eintrag „'+savedConfig.devices[target].name+'“ zuordnen? Dessen Tasten, Seiten, IDs und Topics bleiben erhalten.'))await deviceAction('reassign',target,d.observed_id||d.id);});
      }
    }
  });
  refreshTouchpadVisuals();
  refreshGamepadVisuals();
  refreshScannerVisuals();
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
  learningPanel();
  const learn=card('Taste drücken und übernehmen');learn.append(el('p','Gerät zuerst freigeben und speichern. Mit „Übernehmen“ wird der tatsächliche Tastenname eingetragen. Danach die Belegung speichern. Erst passende Belegungen senden MQTT. „Gedrückt halten“ löst zusätzlich nach 0,7 Sekunden aus.'));
  const recent=el('div');recent.id='learn-events';learn.append(recent);renderEvents(recent,true);
  button(learn,'Leere Belegung hinzufügen',()=>addBinding());
  config.bindings.forEach((b,index)=>{
    const group=deviceKeyGroup($('#saved-keys'),b.device),entry=el('details',undefined,'key-entry');entry.name='usb-key-entries';entry.open=openKeyEntry===b.id;
    entry.append(el('summary',(config.devices[b.device]?.name||b.device)+' – '+b.control+' – '+(b.text||'Einzelbelegung')));group.append(entry);
    markTouchpadBinding(entry,b.device,b.control);
    entry.addEventListener('toggle',()=>{if(entry.isConnected&&entry.open){openKeyEntry=b.id;document.querySelectorAll('.key-entry').forEach(other=>{if(other!==entry)other.open=false;});}});
    const c=card(undefined,entry);const row=el('div',undefined,'row spread');row.append(el('span','BELEGUNG '+(index+1),'binding-number'));button(row,'Entfernen',()=>{config.bindings.splice(index,1);dirty();render();},'danger');c.append(row);
    const f=el('div',undefined,'fields');c.append(f);
    field(f,'Gerät',b.device,v=>{b.device=v;refreshPreview();},'select',Object.keys(config.devices).map(id=>[id,config.devices[id].name||id]));
    const control=field(f,'Taste / Steuerelement',b.control,v=>b.control=v);
    control.placeholder='KEY_TAB (Tastatur) oder key:0 (Stream Deck)';
    field(f,'Ereignis',b.gesture,v=>b.gesture=v,'select',[['press','Drücken'],['release','Loslassen'],['hold','Gedrückt halten'],['repeat','Wiederholen'],['rotate_left','Links drehen'],['rotate_right','Rechts drehen'],['touch','Touch']]);
    field(f,'Text auf der Stream-Deck-Taste',b.text,v=>b.text=v);
    iconField(f,'Icon',b.icon,v=>b.icon=v);
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
    iconField(advanced,'Aktives Icon',b.on_icon,v=>b.on_icon=v);
    more.append(el('p','Rückmeldungen benötigen einen Empfangsbroker am Gerät. Home Assistant muss den Zustand auf das gewählte MQTT-Topic veröffentlichen.'));
  });
}
function addBinding(event) {
  const deck=event&&status.devices.find(d=>d.id===event.device&&d.kind==='streamdeck'&&d.deck);
  if(deck){ensureDeckKeys(deck);dirty();render();return;}
  const device=event?.device||Object.keys(config.devices)[0];
  if(!device)throw new Error('Zuerst unter USB / Virtuelle Geräte ein Gerät freigeben.');
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
    if(report){const labels={learning:'Anlernmodus · nicht gesendet',no_binding:'Keine passende gespeicherte Belegung',no_targets:'Kein MQTT-Ziel ausgewählt',not_connected:'Ziel deaktiviert oder nicht verbunden',sent:report.delivered+'× an MQTT übergeben'};delivery.append(el('div',labels[report.reason]||report.reason));
      (report.transmissions||[]).forEach(tx=>{const line=el('div');line.append(el('small',tx.name+' · '+({sent:'gesendet',offline:'offline',disabled:'deaktiviert',failed:'fehlgeschlagen'}[tx.state]||tx.state)+' · '+tx.topic));delivery.append(line);});
    }else delivery.textContent=event.delivered?event.delivered+'× an MQTT übergeben':'Nicht gesendet';
    row.append(delivery);if(learn){const action=el('td');button(action,'Übernehmen',()=>addBinding(event));row.append(action);}t.append(row);});wrap.append(t);parent.append(wrap);
}
function icons() {
  const c=card('Eigene Bilder und Elgato-Iconpacks');c.append(el('p','Pakete aufklappen oder durchsuchen. GIF und animiertes WebP werden mit Bildzeiten übernommen (maximal 10 Bilder/s). Originaldateien behalten ihre Namen und Unterordner. Plugincode wird nicht ausgeführt.'));
  const favorites=el('div',undefined,'toolbar');c.append(favorites);
  button(favorites,'MDI-Favoriten hinzufügen · 40 Icons',async()=>{const result=await api('icons/favorites',{});iconList=await api('icons');render();notice(result.imported+' MDI-Favoriten übernommen · SteelBlue · 20 Ein-/Aus-Paare. Vorhandene Zuordnungen bleiben erhalten.');});
  c.append(el('small','Optionales Offline-Paket für übliche HA-Entitäten. Weitere CSS-Farbsets als einzelne ZIPs importieren; normal/gedrückt oder MQTT-Zustand selbst zuordnen.'));
  const tools=el('div',undefined,'toolbar');c.append(tools);const label=el('label','Einzelne Icons oder Iconpakete'),file=el('input');file.type='file';file.multiple=true;file.accept='.zip,.streamDeckIconPack,.streamDeckPlugin,.png,.jpg,.jpeg,.svg,.gif,.webp';label.append(file);tools.append(label);
  const upload=button(tools,'Dateien importieren',()=>importFiles(file.files,false),'primary');
  const local=el('div',undefined,'toolbar'),localLabel=el('label','Ganzer Ordner auf diesem Computer (mit Unterordnern)'),directory=el('input');directory.type='file';directory.multiple=true;directory.setAttribute('webkitdirectory','');localLabel.append(directory);local.append(localLabel);c.append(local);
  const uploadFolder=button(local,'Ordner importieren',()=>importFiles(directory.files,true),'primary');
  const progress=el('p');progress.setAttribute('role','status');
  const bar=el('progress',undefined,'icon-import-progress');bar.hidden=true;bar.setAttribute('aria-label','Paketimport-Fortschritt');c.append(bar,progress);
  async function importFiles(selection,isFolder){
    const files=Array.from(selection||[]);
    if(!files.length)throw new Error(isFolder?'Bitte Ordner auswählen.':'Bitte Datei auswählen.');
    const supported=files.filter(f=>/\.(png|jpe?g|svg|gif|webp)$/i.test(f.name)||(!isFolder&&/\.(zip|streamdeckiconpack|streamdeckplugin)$/i.test(f.name)));
    if(files.length>10000||supported.reduce((n,f)=>n+f.size,0)>96*1024*1024)throw new Error('Importlimit: maximal 10.000 Dateien / 96 MB.');
    const isMetadata=f=>/^(manifest\.json|icons\.json|licen[cs]e(?:\.txt|\.md)?)$/i.test(f.name);
    [file,directory,upload,uploadFolder].forEach(e=>e.disabled=true);
    $('#error').hidden=true;$('#notice').hidden=true;
    let imported=0;const skipped=files.filter(f=>!supported.includes(f)&&!(isFolder&&isMetadata(f))).map(f=>({file:f.webkitRelativePath||f.name,reason:'Nicht unterstütztes Format'}));
    [file,directory,upload,uploadFolder].forEach(e=>e.disabled=true);
    try{
      let requests=supported;
      if(isFolder){
        const metadata=files.filter(f=>isMetadata(f)&&f.size<=(f.name.toLowerCase()==='icons.json'?8*1024*1024:256*1024));
        const bytes=await iconFolderArchive([...supported,...metadata],(current,total)=>{bar.hidden=false;bar.max=total;bar.value=current;progress.textContent='Ordner vorbereiten: '+current+' von '+total+' Dateien';});
        const root=(files[0]?.webkitRelativePath||'Eigene Icons').split('/')[0];
        requests=[{name:root+'.zip',size:bytes.length,arrayBuffer:async()=>bytes.buffer}];
      }
      for(let index=0;index<requests.length;index++){
        const f=requests[index];progress.textContent=(index+1)+' / '+requests.length+' · '+(f.webkitRelativePath||f.name);
        bar.hidden=false;bar.max=requests.length;bar.value=index;
        try{
          const archive=/\.(zip|streamdeckiconpack|streamdeckplugin)$/i.test(f.name),limit=(archive?32:8)*1024*1024;
          if(f.size>limit)throw new Error('Datei ist größer als '+(archive?32:8)+' MB.');
          const bytes=new Uint8Array(await f.arrayBuffer());let s='';for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode(...bytes.subarray(i,i+8192));
          const payload={name:f.name,data:btoa(s)};
          payload.import_id=keyId();let polling=false;
          if(archive){bar.removeAttribute('value');progress.textContent=f.name+' · Übertragen und Paket prüfen …';}
          const timer=archive?setInterval(async()=>{
            if(polling)return;polling=true;
            try{const p=await api('icons/progress');if(p.id===payload.import_id&&p.total>0){bar.max=p.total;bar.value=p.current;progress.textContent=f.name+' · '+p.current+' von '+p.total+' Icons · '+p.file;}}catch{}finally{polling=false;}
          },350):null;
          try{const result=await api('icons/upload',payload);imported+=result.imported;skipped.push(...(result.skipped||[]));}
          finally{if(timer!=null)clearInterval(timer);}
          if(!archive){bar.max=requests.length;bar.value=index+1;}
        }catch(e){skipped.push({file:f.webkitRelativePath||f.name,reason:e.message||String(e)});}
      }
      iconList=await api('icons');render();
      notice(imported+' Icons importiert. '+skipped.length+' übersprungen.'+(skipped.length?' '+JSON.stringify(skipped.slice(0,10)):''));
    }finally{[file,directory,upload,uploadFolder].forEach(e=>e.disabled=false);progress.textContent='';bar.hidden=true;}
  }
  const folder=el('div',undefined,'toolbar'),l=el('label','Ordner auf dem Raspi (wird in die Bibliothek kopiert)'),input=el('input');input.placeholder='/home/pi/meine-icons';l.append(input);folder.append(l);button(folder,'Ordner einlesen',async()=>{const r=await api('icons/folder',{path:input.value});iconList=await api('icons');render();notice(r.imported+' Icons importiert. '+JSON.stringify(r.skipped||[]));});c.append(folder);
  const search=el('input');search.placeholder='Icons nach Name, Sammlung oder Schlagwort suchen';search.setAttribute('aria-label','Iconsuche');c.append(search);
  const list=el('div',undefined,'icon-packages');$('#content').append(list);
  const popup=el('div',undefined,'icon-hover');popup.hidden=true;popup.setAttribute('role','tooltip');$('#content').append(popup);
  const opened=new Set();
  function draw(){
    popup.hidden=true;list.replaceChildren();const query=search.value.toLowerCase().trim(),packs=new Map();
    iconPickerIndex().items.filter(i=>iconSearchText(i).includes(query)).forEach(i=>{const name=i.package_folder||i.collection||'Eigene Icons';if(!packs.has(name))packs.set(name,[]);packs.get(name).push(i);});
    for(const [name,items] of packs){
      const pack=el('details',undefined,'icon-package'),summary=el('summary'),heading=el('span',undefined,'icon-package-heading');
      const allItems=iconList.filter(i=>(i.package_folder||i.collection||'Eigene Icons')===name);
      const licenses=[...new Set(allItems.map(i=>String(i.license||'').trim()).filter(Boolean))];
      const authors=[...new Set(allItems.map(i=>i.author).filter(Boolean))];
      const license=el('span',licenses.length>1?'Lizenzhinweise ('+licenses.length+')':licenses.length?'Lizenz: '+licenses[0].replace(/\s+/g,' '):'Keine Lizenzangabe','icon-package-license-label');
      license.title=licenses.join('\n\n')||'Keine Lizenzangabe im Paket';
      heading.append(el('span',(items[0].collection||name)+' ('+items.length+')','icon-package-name'),license);summary.append(heading);pack.append(summary);list.append(pack);
      let drawn=false;
      function populate(){if(drawn)return;drawn=true;
        const legal=el('details',undefined,'icon-pack-license');legal.append(el('summary','Lizenz des Pakets'),el('pre',licenses.join('\n\n---\n\n')||'Keine Lizenzangabe im Paket'));
        if(authors.length)legal.append(el('small',authors.join(' · ')));pack.append(legal);
        const actions=el('div',undefined,'icon-pack-actions');pack.append(actions);
        button(actions,'Paket entfernen',async()=>{
          if(changed)throw new Error('Zuerst Änderungen speichern oder abbrechen.');
          if(!confirm('Iconpaket „'+name+'“ entfernen? Vorher wird automatisch die Iconbibliothek gesichert. Verwendete Pakete bleiben geschützt.'))return;
          const result=await api('icons/remove',{package:name});iconList=await api('icons');render();notice('Paket entfernt. Sicherung: '+result.backup);
        },'danger');
        const groups=new Map();items.forEach(i=>{const path=i.subfolder&&i.subfolder!=='.'?i.subfolder:'';if(!groups.has(path))groups.set(path,[]);groups.get(path).push(i);});
        for(const [path,icons] of groups){
          if(path)pack.append(el('h3',path,'icon-folder'));
          const grid=el('div',undefined,'icons');pack.append(grid);
          for(const i of icons){
            const tile=el('article',undefined,'icon-card'),img=el('img');img.src='/icons/'+i.id+(i.animated?'.webp':'.png');img.alt=i.filename||i.name;img.loading='lazy';tile.tabIndex=0;
            tile.append(img,el('strong',i.filename||i.name));tile.setAttribute('aria-label',(i.filename||i.name)+(i.animated?' · animiert':''));
            tile.title=(i.filename||i.name)+' · '+name+(i.aliases?.length?' · Weitere Namen: '+iconAliasText(i):'')+(i.animated?' · animiert':'' );
            const show=()=>{popup.replaceChildren();const preview=el('img');preview.src=img.src;preview.alt=img.alt;popup.append(preview,el('strong',i.filename||i.name),el('small',name+(path?' / '+path:'')));if(i.animated)popup.append(el('small','Animiert · '+i.frames+' Bilder'));popup.hidden=false;};
            tile.onmouseenter=show;tile.onfocus=show;tile.onmouseleave=()=>popup.hidden=true;tile.onblur=()=>popup.hidden=true;
            grid.append(tile);
          }
        }
      }
      pack.addEventListener('toggle',()=>{if(!pack.isConnected)return;if(pack.open){opened.add(name);populate();}else{opened.delete(name);popup.hidden=true;pack.querySelectorAll('img').forEach(img=>img.removeAttribute('src'));pack.querySelectorAll('.icons,.icon-folder,.icon-pack-actions,.icon-pack-license').forEach(n=>n.remove());drawn=false;}});
      if(query||opened.has(name)){pack.open=true;populate();}
    }
    if(!packs.size)list.append(el('p',query?'Keine passenden Icons gefunden.':'Noch keine Icons importiert.'));
  }
  search.oninput=draw;draw();
}
function system() {
  const c=card('Weboberfläche nur bei Bedarf');c.append(el('p','Das Schließen dieses Browserfensters beendet den Webdienst nicht. Mit „web stop“ wird der HTTP-Listener beendet. USB und MQTT laufen unabhängig weiter.'));
  c.append(el('pre','sudo ugso-usbhub web start    # jetzt starten\nsudo ugso-usbhub web stop     # jetzt abschalten\nsudo ugso-usbhub web status   # Status\nsudo ugso-usbhub web enable   # mit Autostart\nsudo ugso-usbhub web disable  # stoppen, ohne Autostart\nsudo ugso-usbhub backup       # Einstellungen und Icons sichern\nsudo journalctl -u ugso-usbhub -n 50'));
  c.append(el('p','Die Oberfläche verwendet HTTP im lokalen Netz. Nicht ins Internet freigeben. Für fremde Netze VPN oder einen HTTPS-Reverse-Proxy verwenden.','warning'));
  const d=card('Geräte- und Verbindungsdiagnose');Object.entries(status.errors||{}).forEach(([k,v])=>d.append(el('p',k+': '+v,'warning')));if(!Object.keys(status.errors||{}).length)d.append(el('p','Keine Gerätefehler gemeldet.'));
  const e=card('Letzte Eingaben (nur im Arbeitsspeicher)'),log=el('div');log.id='event-log';e.append(log);renderEvents(log);
  const f=card('Datenspeicherung');f.append(el('p','Einstellungen, Zugangsdaten und Icons liegen auf dem Raspi unter /var/lib/ugso-usbhub. Die letzten zehn Konfigurationsstände werden automatisch gesichert. Passwörter werden in der Oberfläche nicht zurückgeliefert. Geräte ohne Seriennummer werden über ihren USB-Port zugeordnet.'));
}
async function enter() { config=await api('config'); savedConfig=cloneConfig(config);keyEditBaseline.clear(); status=await api('status');iconList=await api('icons');$('#login').hidden=true;$('#workspace').hidden=false;$('#logout').hidden=false;$('#error').hidden=true;render(); }
function showLogin(){closeIconPicker();config=null;$('#login').hidden=false;$('#workspace').hidden=true;$('#logout').hidden=true;}
$('#login-form').onsubmit=async e=>{e.preventDefault();try{await api('login',{password:$('#password').value});$('#password').value='';await enter();}catch(e){error(e);}};
$('#logout').onclick=async()=>{if(changed&&!confirm('Ungespeicherte Änderungen verwerfen?'))return;await endLearning();await api('logout',{});changed=false;learnedDraft=[];showLogin();};
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{if(learning){error(new Error('Anlernmodus zuerst beenden.'));return;}page=b.dataset.page;render();});
$('#save').onclick=async()=>{try{if(learning||learnedDraft.length)throw new Error('Anlernen zuerst beenden und die Tasten übernehmen oder verwerfen.');await api('config',config);config=await api('config');savedConfig=cloneConfig(config);keyEditBaseline.clear();changed=false;$('#save').disabled=true;$('#dirty').textContent='Gespeichert';$('#error').hidden=true;render();notice('Gespeichert. Der USB-/MQTT-Dienst übernimmt die Einstellungen innerhalb weniger Sekunden.');}catch(e){error(e);}};
let polling=false;
function deviceSignature(){return JSON.stringify([status.devices.map(d=>[d.id,d.observed_id,d.name,d.kind,d.identity_hint]),(status.mobile?.known_decks||[]).map(d=>d.id)]);}
setInterval(async()=>{if(!config||polling)return;polling=true;try{const previousDecks=deckSignature(),previousDevices=deviceSignature(),previousPage=page;status=await api('status');renderStorage();updateDeckTab();if(page!==previousPage)render();else if(page==='devices'&&!changed&&previousDevices!==deviceSignature())render();else if(page==='streamdeck'&&previousDecks!==deckSignature()){if(changed)refreshDeckGrid();else render();}if(page==='streamdeck')renderDeckConnection();await pollLearning();$('#connection').textContent=serviceAlive()?'● USB-/MQTT-Dienst aktiv':'○ Dienst nicht aktiv';if(page==='bindings'&&$('#learn-events'))renderEvents($('#learn-events'),true);if(page==='system'&&$('#event-log'))renderEvents($('#event-log'));if(page==='mobile'&&$('#mobile-status'))renderMobileStatus($('#mobile-status')); }catch(e){error(e);}finally{polling=false;}},2500);
window.addEventListener('beforeunload',e=>{if(changed||learning||learnedDraft.length){e.preventDefault();e.returnValue='';}});
enter().catch(()=>{});
