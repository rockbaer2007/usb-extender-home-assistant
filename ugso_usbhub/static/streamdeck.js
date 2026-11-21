'use strict';
let deckDevice = '', deckKey = 0, deckPreviewTimer, deckPreviewSequence = 0;
let deckPreviewPressed = false;
const deckPreviewCache=new Map();
let seenMobileDecks=new Set(),pendingMobileEditor='';
const knownDecks=new Map();
function connectedDecks() { return serviceAlive() ? status.devices.filter(d=>d.kind==='streamdeck') : []; }
function availableDecks() {
  for(const [id,settings] of Object.entries(config?.devices||{})){
    if(settings.deck_info&&!knownDecks.has(id))knownDecks.set(id,{id,kind:'streamdeck',name:settings.name||'Stream Deck',connection:settings.deck_connection,deck:settings.deck_info});
  }
  for(const d of status.mobile?.known_decks||[])knownDecks.set(d.id,{...knownDecks.get(d.id),...d});
  for(const d of connectedDecks())knownDecks.set(d.id,{...knownDecks.get(d.id),...d,deck:d.deck||knownDecks.get(d.id)?.deck});
  return [...knownDecks.values()];
}
function deckSignature() { return JSON.stringify(availableDecks().map(d=>[d.id,d.deck?.keys,d.deck?.layout,d.deck?.visual])); }
function renderDeckConnection() {
  const box=$('#deck-connection');if(!box)return;
  const online=connectedDecks().some(d=>d.id===deckDevice);
  box.textContent=online?'Online · Gerät verbunden':'Offline · Editor und Einstellungen bleiben erhalten. Änderungen werden gespeichert und bei Wiederverbindung übernommen.';
  box.className=online?'badge':'warning';
}
function drawDeckKeys(grid,device) {
  grid.className='deck-grid deck-columns-'+device.deck.layout[1];grid.replaceChildren();
  for(let key=0;key<device.deck.keys;key++){
    const tile=button(grid,'',()=>{deckKey=key;render();},'deck-key'+(deckKey===key?' selected':''));tile.dataset.key=key;tile.setAttribute('aria-pressed',String(deckKey===key));tile.setAttribute('aria-label','Taste '+(key+1));
    const image=el('img');image.alt='';image.dataset.previewKey=key;tile.append(image,el('span',String(key+1),'deck-key-number'));
  }
}
function refreshDeckGrid() {
  const device=availableDecks().find(d=>d.id===deckDevice),grid=$('.deck-grid');
  if(!device?.deck||!grid)return;
  ensureDeckKeys(device);drawDeckKeys(grid,device);
  const description=$('#deck-grid-description');
  if(description)description.textContent=device.deck.layout[0]+' Zeilen hoch × '+device.deck.layout[1]+' Spalten breit';
  scheduleDeckPreview(device);
}
function updateDeckTab() {
  const tab=$('[data-page=streamdeck]');
  const connected=connectedDecks(),mobile=connected.filter(d=>d.connection==='mobile'&&d.deck);
  const online=new Set(mobile.map(d=>d.id));
  if(pendingMobileEditor&&!online.has(pendingMobileEditor))pendingMobileEditor='';
  const fresh=mobile.find(d=>!seenMobileDecks.has(d.id));
  if(fresh)pendingMobileEditor=fresh.id;
  online.forEach(id=>seenMobileDecks.add(id));
  if(pendingMobileEditor&&!changed&&!learning&&!learnedDraft.length&&['overview','mobile','devices'].includes(page)){
    if(deckDevice!==pendingMobileEditor){deckDevice=pendingMobileEditor;deckKey=0;}
    pendingMobileEditor='';page='streamdeck';
  }
  tab.hidden=false;
  availableDecks();
}
function deckArtwork(device,key) {
  const saved=config.devices[device]?.deck_keys?.[String(key)];
  if(saved)return saved;
  const b=config.bindings.find(b=>b.device===device&&b.control==='key:'+key) ||
    (config.keys||[]).find(k=>k.device===device&&k.control==='key:'+key);
  return {text:b?.text??b?.name??'',icon:b?.icon||'',background:'#000000',background_image:'',text_color:'#ffffff',font_size:14,text_position:'bottom',fit:'contain'};
}
function ensureDeckKeys(device) {
  if(!config.devices[device.id]?.enabled||!device.deck)return false;
  config.keys||=[];
  const names=new Map(config.keys.filter(k=>k.device_topic).map(k=>[k.device,k.device_topic])),used=new Set(names.values());
  const slug=name=>String(name).toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').normalize('NFKD').replace(/[^\x00-\x7f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,64).replace(/-$/,'')||'usb-device';
  for(const [id,settings] of Object.entries(config.devices)){
    if(names.has(id))continue;
    const stem=slug(settings.name||'USB-Gerät');let name=stem,n=2;
    while(used.has(name))name=stem+'-'+n++;
    names.set(id,name);used.add(name);
  }
  let added=false;
  for(let index=0;index<device.deck.keys;index++){
    const control='key:'+index;
    if(config.keys.some(k=>k.device===device.id&&k.control===control))continue;
    const row=learnedKey(device.id,control,names.get(device.id));row.name='Taste '+(index+1);
    config.keys.push(row);added=true;
  }
  if(added)dirty();return added;
}
function streamdeck() {
  const decks=availableDecks();
  if(!decks.length){empty($('#content'),'Stream Deck','Noch kein Deck eingerichtet. Gerät verbinden, freigeben und speichern.');return;}
  if(!decks.some(d=>d.id===deckDevice)){deckDevice=decks[0].id;deckKey=0;}
  const d=decks.find(d=>d.id===deckDevice);
  const settings=config.devices[d.id] ||= {name:d.name,enabled:false,targets:[...config.default_targets],receive_broker:'',brightness:30};
  const top=card('Stream Deck · Gerät und Anzeige');
  field(top,'Eingerichtetes Gerät',d.id,v=>{deckDevice=v;deckKey=0;render();},'select',decks.map(d=>[d.id,config.devices[d.id]?.name||d.name]));
  const connection=el('p');connection.id='deck-connection';connection.setAttribute('role','status');top.append(connection);renderDeckConnection();
  top.append(el('p','Taste im Gerätebild auswählen. Gestaltung und MQTT-Zuordnung bearbeiten und oben speichern. Die Vorschau sendet keine MQTT-Aktion. Beim Abziehen bleiben alle Einstellungen erhalten.'));
  field(top,'Gerät für Eingaben und Anzeige freigeben',settings.enabled,v=>{settings.enabled=v;if(v)ensureDeckKeys(d);render();},'checkbox');
  if(!d.deck){
    top.append(el('p','Für das genaue Tastenlayout zuerst das Gerät freigeben und speichern. Falls es bereits freigegeben ist: USB-/MQTT-Dienst und Gerätefehler unter System prüfen.','warning'));
    return;
  }
  if(deckKey>=d.deck.keys)deckKey=0;
  ensureDeckKeys(d);
  const header=el('div',undefined,'fields');top.append(header);
  if(d.connection!=='mobile'){const bright=field(header,'Helligkeit (0–100)',settings.brightness??30,v=>settings.brightness=v,'number');bright.min=0;bright.max=100;}
  else {
    header.append(el('p','Mobile-Bildschirmhelligkeit direkt am Android-Gerät einstellen.'));
    header.append(el('small','Das Raster wird ausschließlich von der Android-App übernommen. Dort Zeilen und Spalten ändern. Offline bleibt das zuletzt empfangene Raster erhalten.'));
  }
  field(header,'Empfangsbroker für MQTT-Anzeige',settings.receive_broker||'',v=>settings.receive_broker=v,'select',[['','Keiner'],...config.brokers.map(b=>[b.id,b.name])]);
  const layout=el('div',undefined,'deck-workspace');$('#content').append(layout);
  const view=card(d.deck.model,layout),grid=el('div',undefined,'deck-grid deck-columns-'+d.deck.layout[1]);grid.setAttribute('role','group');grid.setAttribute('aria-label','Stream-Deck-Tasten');view.append(grid);
  const description=el('p',d.deck.layout[0]+' Zeilen hoch × '+d.deck.layout[1]+' Spalten breit');description.id='deck-grid-description';view.append(description);
  drawDeckKeys(grid,d);
  if(!d.deck.visual)view.append(el('p','Dieses Modell hat keine Tastenbildschirme. Die Tasten dienen zur MQTT-Zuordnung; Bilder können auf dem Gerät nicht angezeigt werden.','warning'));
  const editor=card('Taste '+(deckKey+1)+' · Gestaltung',layout),style={...deckArtwork(d.id,deckKey)};
  function edit(name,value){style[name]=value;settings.deck_keys||={};settings.deck_keys[String(deckKey)]={...style};scheduleDeckPreview(d);}
  if(d.deck.visual){
    const fields=el('div',undefined,'fields');editor.append(fields);
    field(fields,'Beschriftung',style.text||'',v=>edit('text',v)).maxLength=80;
    const choices=[['','Kein Bild'],...iconList.map(i=>[i.id,i.collection+' · '+i.name])];
    field(fields,'Icon / Vordergrundbild',style.icon||'',v=>edit('icon',v),'select',choices);
    field(fields,'Hintergrundbild',style.background_image||'',v=>edit('background_image',v),'select',choices);
    field(fields,'Hintergrundfarbe',style.background||'#000000',v=>edit('background',v),'color');
    field(fields,'Schriftfarbe',style.text_color||'#ffffff',v=>edit('text_color',v),'color');
    const font=field(fields,'Schriftgröße (bei 72 px)',style.font_size??14,v=>edit('font_size',v),'number');font.min=8;font.max=32;
    field(fields,'Textposition',style.text_position||'bottom',v=>edit('text_position',v),'select',[['top','Oben'],['center','Mitte'],['bottom','Unten']]);
    field(fields,'Vordergrundbild anpassen',style.fit||'contain',v=>edit('fit',v),'select',[['contain','Vollständig einpassen'],['cover','Fläche füllen / zuschneiden']]);
    const pressedFields=el('div',undefined,'fields');editor.append(el('h3','Gedrückt'),pressedFields);
    field(pressedFields,'Icon bei gedrückter Taste',style.pressed_icon||'',v=>edit('pressed_icon',v),'select',
      [['','Normales Icon übernehmen'],...iconList.map(i=>[i.id,i.collection+' · '+i.name])]);
    for(const [name,label,fallback] of [['background','Hintergrundfarbe gedrückt','#000000'],['text_color','Schriftfarbe gedrückt','#ffffff']]){
      field(pressedFields,label+' verwenden',!!style['pressed_'+name],v=>{edit('pressed_'+name,v?(style[name]||fallback):'');render();},'checkbox');
      const color=field(pressedFields,label,style['pressed_'+name]||style[name]||fallback,v=>edit('pressed_'+name,v),'color');
      color.disabled=!style['pressed_'+name];
    }
    field(editor,'Vorschau: Taste gedrückt',deckPreviewPressed,v=>{deckPreviewPressed=v;scheduleDeckPreview(d);},'checkbox');
    editor.append(el('small','Gilt während des Drückens. Beim Loslassen erscheint wieder die normale Darstellung. Ohne eigene Auswahl werden normales Icon und normale Farben übernommen. Die Vorschau sendet keine MQTT-Aktion.'));
    button(editor,'Bilder importieren …',()=>{page='icons';render();});
    editor.append(el('small','GIF-/WebP-Icons werden normal und gedrückt animiert. Hintergründe bleiben statisch. Nur Animationen senden fortlaufend neue Bilder.'));
  }else editor.append(el('p','Für dieses Modell ist keine Bildgestaltung verfügbar.'));
  const mqtt=card('Taste '+(deckKey+1)+' · MQTT-Zuordnung');mqtt.classList.add('deck-mqtt');
  const control='key:'+deckKey,rows=config.bindings.filter(b=>b.device===d.id&&b.control===control),keys=(config.keys||[]).filter(k=>k.device===d.id&&k.control===control);
  if(!rows.length&&!keys.length)mqtt.append(el('p','Noch keine MQTT-Zuordnung. Eine Aktion hinzufügen oder die Taste unter „Tasten & Anzeigen“ anlernen.'));
  if(keys.length){
    mqtt.append(el('p','Diese Taste ist bereits in der Tastenliste gespeichert. Press/Release, Switch und Gesten werden dort verwaltet; die vorhandenen Topics bleiben erhalten.'));
    button(mqtt,'Tastenliste öffnen',()=>{page='bindings';render();});
  }
  rows.forEach(b=>{
    const box=el('div',undefined,'deck-binding');mqtt.append(box);
    const fields=el('div',undefined,'fields');box.append(fields);
    field(fields,'Ereignis',b.gesture,v=>b.gesture=v,'select',[['press','Drücken'],['release','Loslassen'],['hold','Halten'],['repeat','Wiederholen']]);
    field(fields,'Sende-Topic (leer = bisherige Automatik)',b.topic||'',v=>b.topic=v);
    field(fields,'Nutzdaten (leer = Ereignis als JSON)',b.payload||'',v=>b.payload=v);
    field(fields,'Geräteziele übernehmen',b.targets==null,v=>{b.targets=v?null:[];render();},'checkbox');
    if(b.targets!=null)routes(box,b.targets,v=>b.targets=v);
    const feedback=el('details');feedback.append(el('summary','MQTT-Rückmeldung und aktives Icon'));box.append(feedback);
    field(feedback,'Zustands-Topic',b.state_topic||'',v=>b.state_topic=v);
    field(feedback,'JSON-Feld (optional)',b.state_path||'',v=>b.state_path=v);
    field(feedback,'Aktiver Wert',b.on_value??'ON',v=>b.on_value=v);
    field(feedback,'Aktives Icon',b.on_icon||'',v=>b.on_icon=v,'select',[['','Kein aktives Icon'],...iconList.map(i=>[i.id,i.name])]);
    feedback.append(el('small','Der gewählte Empfangsbroker liefert den Zustand. Bei Rückmeldungen erscheint der empfangene Wert als Text.'));
    button(box,'Diese MQTT-Aktion entfernen',()=>{config.bindings.splice(config.bindings.indexOf(b),1);dirty();render();},'danger');
  });
  button(mqtt,'MQTT-Aktion hinzufügen',()=>{
    const stem=(settings.name||d.name).toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'stream-deck';
    config.bindings.push({id:'deck-'+keyId(),device:d.id,control,gesture:'press',topic:stem+'-key-'+deckKey+'/press',payload:'press',targets:null});dirty();render();
  });
  mqtt.append(el('small','Nach Freigabe werden fehlende Tastenkanäle automatisch angelegt. Oben speichern: Press/Release, Plus, Switch, Tastenzustand, Button und Klick/Doppelklick/Halten. In der Tastenliste einzeln ändern. Zusätzliche Einzelaktionen bleiben zusätzlich aktiv.'));
  scheduleDeckPreview(d);
}
function scheduleDeckPreview(device) {
  clearTimeout(deckPreviewTimer);const sequence=++deckPreviewSequence;
  deckPreviewTimer=setTimeout(async()=>{
    try{
      const tiles=[...document.querySelectorAll('[data-preview-key]')];
      for(const tile of tiles){
        if(sequence!==deckPreviewSequence||page!=='streamdeck')return;
        const key=Number(tile.dataset.previewKey),style=deckArtwork(device.id,key);
        const request={style,size:device.deck.size,pressed:deckPreviewPressed},cacheKey=JSON.stringify(request);
        let image=deckPreviewCache.get(cacheKey);
        if(!image){const result=await api('deck/preview',request);image=(result.mime||'image/png')+';base64,'+result.image;if(deckPreviewCache.size>=256)deckPreviewCache.clear();deckPreviewCache.set(cacheKey,image);}
        if(sequence!==deckPreviewSequence||!tile.isConnected)return;
        const source='data:'+image;if(tile.src!==source)tile.src=source;
      }
    }catch(e){if(sequence===deckPreviewSequence&&page==='streamdeck')error(e);}
  },180);
}
