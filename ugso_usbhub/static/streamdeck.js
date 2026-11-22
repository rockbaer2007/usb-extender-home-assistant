'use strict';
let deckDevice = '', deckKey = 0, deckPreviewTimer, deckPreviewSequence = 0;
let deckPreviewPressed = false;
const deckPreviewCache=new Map();
let seenMobileDecks=new Set(),pendingMobileEditor='';
const knownDecks=new Map();
const forgottenDecks=new Set();
const editorPages=new Map();
function editorPage(ident){return Math.max(0,Math.min(editorPages.get(ident)||0,(config.devices[ident]?.deck_page_count||1)-1));}
function editorPageSlots(ident){return config.devices[ident]?.deck_page_order||Array.from({length:config.devices[ident]?.deck_page_count||1},(_,i)=>i);}
function editorLogicalKey(ident,key){return editorPageSlots(ident)[editorPage(ident)]*128+key;}
function deckColorField(parent,label,value,change){
  const input=field(parent,label,value,change,'color'),wrap=input.parentElement;
  input.setAttribute('aria-label',label);
  wrap.classList.add('deck-color');wrap.firstChild.replaceWith(el('span',label));
  const hex=el('code',value.toUpperCase());hex.setAttribute('aria-hidden','true');wrap.append(hex);
  for(const event of ['input','change'])input.addEventListener(event,()=>hex.textContent=input.value.toUpperCase());
  return input;
}
function connectedDecks() { return serviceAlive() ? status.devices.filter(d=>d.kind==='streamdeck') : []; }
function availableDecks() {
  for(const [id,settings] of Object.entries(config?.devices||{})){
    if(settings.deck_info&&!knownDecks.has(id))knownDecks.set(id,{id,kind:'streamdeck',name:settings.name||'Stream Deck',connection:settings.deck_connection,deck:settings.deck_info});
  }
  for(const d of status.mobile?.known_decks||[])knownDecks.set(d.id,{...knownDecks.get(d.id),...d});
  for(const d of connectedDecks())knownDecks.set(d.id,{...knownDecks.get(d.id),...d,deck:d.deck||knownDecks.get(d.id)?.deck});
  return [...knownDecks.values()].filter(d=>!forgottenDecks.has(d.id));
}
function deckSignature() { return JSON.stringify(availableDecks().map(d=>[d.id,d.deck?.keys,d.deck?.layout,d.deck?.visual])); }
function renderDeckConnection() {
  const box=$('#deck-connection');if(!box)return;
  const online=connectedDecks().some(d=>d.id===deckDevice);
  const current=status.deck_pages?.[deckDevice];
  box.textContent=online?'Online · Gerät verbunden'+(current?' · Am Gerät: Seite '+current.page+' / '+current.pages:''):'Offline · Editor und Einstellungen bleiben erhalten. Änderungen werden gespeichert und bei Wiederverbindung übernommen.';
  box.className=online?'badge':'warning';
}
function drawDeckKeys(grid,device) {
  grid.className='deck-grid deck-columns-'+device.deck.layout[1];grid.replaceChildren();
  for(let key=0;key<device.deck.keys;key++){
    const number=editorPage(device.id)*device.deck.keys+key+1;
    const tile=button(grid,'',()=>{deckKey=key;render();},'deck-key'+(deckKey===key?' selected':''));tile.dataset.key=key;tile.setAttribute('aria-pressed',String(deckKey===key));tile.setAttribute('aria-label','Taste '+number);
    const image=el('img');image.alt='';image.dataset.previewKey=key;tile.append(image,el('span',String(number),'deck-key-number'));
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
  const logical=editorLogicalKey(device,key),saved=config.devices[device]?.deck_keys?.[String(logical)];
  if(saved)return saved;
  const b=config.bindings.find(b=>b.device===device&&b.control==='key:'+logical) ||
    (config.keys||[]).find(k=>k.device===device&&k.control==='key:'+logical);
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
  const known=new Map(config.keys.filter(k=>k.device===device.id).map(k=>[k.control,k]));
  for(let index=0;index<(config.devices[device.id]?.deck_page_count||1)*device.deck.keys;index++){
    const pageNumber=Math.floor(index/device.deck.keys),slot=index%device.deck.keys,storagePage=editorPageSlots(device.id)[pageNumber],logical=storagePage*128+slot,control='key:'+logical;
    const existing=known.get(control),caption='Taste '+(pageNumber*device.deck.keys+slot+1);
    if(existing){if(existing.deck_auto_label&&existing.name!==caption){existing.name=caption;added=true;}continue;}
    const row=learnedKey(device.id,control,names.get(device.id));row.name=caption;row.deck_auto_label=true;
    if(storagePage)for(const mode of ['press','release','switch','press_plus','release_plus','state','button','button_plus','click','double_click','hold'])row[mode+'_topic']=names.get(device.id)+'-page-'+(storagePage+1)+'-key-'+slot+'/'+mode.replaceAll('_','-');
    config.keys.push(row);known.set(control,row);added=true;
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
  const pagebar=el('div',undefined,'deck-pagebar');top.append(pagebar);
  const selectedPage=editorPage(d.id),pageCount=settings.deck_page_count||1;
  field(pagebar,'Seite im Editor',selectedPage,v=>{editorPages.set(d.id,Number(v));deckKey=0;render();},'select',Array.from({length:pageCount},(_,i)=>[i,'Seite '+(i+1)+' / '+pageCount]));
  const browse=el('div',undefined,'row');pagebar.append(browse);
  function browsePage(next){editorPages.set(d.id,Math.max(0,Math.min(pageCount-1,next)));deckKey=0;render();}
  button(browse,'‹ Zurück',()=>browsePage(selectedPage-1)).disabled=selectedPage===0;
  button(browse,'Home',()=>browsePage(0)).disabled=selectedPage===0;
  button(browse,'Vor ›',()=>browsePage(selectedPage+1)).disabled=selectedPage===pageCount-1;
  const manage=el('div',undefined,'row');pagebar.append(manage);
  button(manage,'Neue Seite',()=>{
    const order=[...editorPageSlots(d.id)],slot=Array.from({length:8},(_,i)=>i).find(i=>!order.includes(i));
    if(slot===undefined)throw new Error('Maximal 8 Seiten je Deck.');
    order.push(slot);settings.deck_page_order=order;settings.deck_page_count=order.length;editorPages.set(d.id,order.length-1);deckKey=0;ensureDeckKeys(d);dirty();render();
  }).disabled=pageCount>=8;
  button(manage,'Aktuelle Seite löschen',()=>{
    if(selectedPage===0)return;
    if(!confirm('Seite '+(selectedPage+1)+' mit ihren Tasten und MQTT-Belegungen löschen? Sprünge auf diese Seite führen danach zu Seite 1. Alle anderen Seiten bleiben erhalten. Erst Speichern übernimmt die Löschung.'))return;
    const order=[...editorPageSlots(d.id)],slot=order[selectedPage],matches=control=>/^key:\d+$/.test(control)&&Math.floor(Number(control.slice(4))/128)===slot;
    for(const key of Object.keys(settings.deck_keys||{}))if(Math.floor(Number(key)/128)===slot)delete settings.deck_keys[key];
    config.keys=(config.keys||[]).filter(k=>!(k.device===d.id&&matches(k.control)));
    config.bindings=config.bindings.filter(b=>!(b.device===d.id&&matches(b.control)));
    for(const art of Object.values(settings.deck_keys||{}))if(art.action==='goto'){
      if(art.target_page===selectedPage+1)art.target_page=1;
      else if(art.target_page>selectedPage+1)art.target_page--;
    }
    order.splice(selectedPage,1);settings.deck_page_order=order;settings.deck_page_count=order.length;editorPages.set(d.id,selectedPage-1);deckKey=0;dirty();render();
  },'danger').disabled=selectedPage===0;
  top.append(el('small','Bis zu 8 Seiten je Deck. Tasten werden fortlaufend nummeriert. Seitenwechsel hier ist eine Editorvorschau; am Gerät navigieren zugewiesene Vor-/Zurück-/Home-Tasten.'));
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
  const number=selectedPage*d.deck.keys+deckKey+1;
  const editor=card('Seite '+(selectedPage+1)+' · Taste '+number+' · Gestaltung',layout),style={...deckArtwork(d.id,deckKey)},logical=editorLogicalKey(d.id,deckKey);
  editor.classList.add('deck-artwork');
  function edit(name,value){style[name]=value;settings.deck_keys||={};settings.deck_keys[String(logical)]={...style};scheduleDeckPreview(d);}
  const actionFields=el('div',undefined,'fields');editor.append(actionFields);
  field(actionFields,'Tastenfunktion',style.action||'mqtt',v=>{if(v!=='mqtt'){edit('show_page',true);if(!style.text||/^Taste \d+$/.test(style.text))edit('text','');}if(v==='goto')edit('target_page',Math.min(style.target_page||1,pageCount));edit('action',v);dirty();render();},'select',[['mqtt','MQTT / normale Taste'],['next','Vor · nächste Seite'],['previous','Zurück · vorherige Seite'],['home','Home · erste Seite'],['goto','Gehe zu · bestimmte Seite']]);
  if(style.action==='goto')field(actionFields,'Zielseite',Math.min(style.target_page||1,pageCount),v=>{edit('target_page',Number(v));dirty();},'select',Array.from({length:pageCount},(_,i)=>[String(i+1),'Seite '+(i+1)]));
  field(actionFields,'Seitennummer anzeigen',!!style.show_page,v=>edit('show_page',v),'checkbox');
  if(d.deck.visual){
    const fields=el('div',undefined,'fields');editor.append(fields);
    const caption=field(fields,'Beschriftung',style.text||'',v=>edit('text',v));caption.maxLength=80;caption.placeholder=({next:'Vor',previous:'Zurück',home:'Home'})[style.action]||'';
    iconField(fields,'Icon / Vordergrundbild',style.icon||'',v=>edit('icon',v),'Kein Bild');
    iconField(fields,'Hintergrundbild',style.background_image||'',v=>edit('background_image',v),'Kein Bild');
    deckColorField(fields,'Hintergrundfarbe',style.background||'#000000',v=>edit('background',v));
    deckColorField(fields,'Schriftfarbe',style.text_color||'#ffffff',v=>edit('text_color',v));
    const font=field(fields,'Schriftgröße (bei 72 px)',style.font_size??14,v=>edit('font_size',v),'number');font.min=8;font.max=32;
    field(fields,'Textposition',style.text_position||'bottom',v=>edit('text_position',v),'select',[['top','Oben'],['center','Mitte'],['bottom','Unten']]);
    field(fields,'Vordergrundbild anpassen',style.fit||'contain',v=>edit('fit',v),'select',[['contain','Vollständig einpassen'],['cover','Fläche füllen / zuschneiden']]);
    const pressedFields=el('div',undefined,'fields');editor.append(el('h3','Gedrückt'),pressedFields);
    iconField(pressedFields,'Icon bei gedrückter Taste',style.pressed_icon||'',v=>edit('pressed_icon',v),'Normales Icon übernehmen');
    for(const [name,label,fallback] of [['background','Hintergrundfarbe gedrückt','#000000'],['text_color','Schriftfarbe gedrückt','#ffffff']]){
      field(pressedFields,label+' verwenden',!!style['pressed_'+name],v=>{edit('pressed_'+name,v?(style[name]||fallback):'');render();},'checkbox');
      const color=deckColorField(pressedFields,label,style['pressed_'+name]||style[name]||fallback,v=>edit('pressed_'+name,v));
      color.disabled=!style['pressed_'+name];
    }
    field(editor,'Vorschau: Taste gedrückt',deckPreviewPressed,v=>{deckPreviewPressed=v;scheduleDeckPreview(d);},'checkbox');
    editor.append(el('small','Gilt während des Drückens. Beim Loslassen erscheint wieder die normale Darstellung. Ohne eigene Auswahl werden normales Icon und normale Farben übernommen. Die Vorschau sendet keine MQTT-Aktion.'));
    button(editor,'Bilder importieren …',()=>{page='icons';render();});
    editor.append(el('small','GIF-/WebP-Icons werden normal und gedrückt animiert. Hintergründe bleiben statisch. Nur Animationen senden fortlaufend neue Bilder.'));
  }else editor.append(el('p','Für dieses Modell ist keine Bildgestaltung verfügbar.'));
  const mqtt=card('Seite '+(selectedPage+1)+' · Taste '+number+' · MQTT-Zuordnung');mqtt.classList.add('deck-mqtt');
  if((style.action||'mqtt')!=='mqtt'){
    mqtt.append(el('p','Diese Taste navigiert ausschließlich zwischen Deck-Seiten. Bestehende MQTT-Belegungen bleiben gespeichert und werden mit „MQTT / normale Taste“ wieder aktiv.'));
    scheduleDeckPreview(d);return;
  }
  const control='key:'+logical,rows=config.bindings.filter(b=>b.device===d.id&&b.control===control),keys=(config.keys||[]).filter(k=>k.device===d.id&&k.control===control);
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
    iconField(feedback,'Aktives Icon',b.on_icon||'',v=>b.on_icon=v,'Kein aktives Icon');
    feedback.append(el('small','Der gewählte Empfangsbroker liefert den Zustand. Bei Rückmeldungen erscheint der empfangene Wert als Text.'));
    button(box,'Diese MQTT-Aktion entfernen',()=>{config.bindings.splice(config.bindings.indexOf(b),1);dirty();render();},'danger');
  });
  button(mqtt,'MQTT-Aktion hinzufügen',()=>{
    const stem=(settings.name||d.name).toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'stream-deck';
    const slot=editorPageSlots(d.id)[selectedPage];
    config.bindings.push({id:'deck-'+keyId(),device:d.id,control,gesture:'press',topic:stem+(slot?'-page-'+(slot+1):'')+'-key-'+deckKey+'/press',payload:'press',targets:null});dirty();render();
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
        const request={style,size:device.deck.size,pressed:deckPreviewPressed,page:editorPage(device.id),pages:config.devices[device.id]?.deck_page_count||1},cacheKey=JSON.stringify(request);
        let image=deckPreviewCache.get(cacheKey);
        if(!image){const result=await api('deck/preview',request);image=(result.mime||'image/png')+';base64,'+result.image;if(deckPreviewCache.size>=256)deckPreviewCache.clear();deckPreviewCache.set(cacheKey,image);}
        if(sequence!==deckPreviewSequence||!tile.isConnected)return;
        const source='data:'+image;if(tile.src!==source)tile.src=source;
      }
    }catch(e){if(sequence===deckPreviewSequence&&page==='streamdeck')error(e);}
  },180);
}
