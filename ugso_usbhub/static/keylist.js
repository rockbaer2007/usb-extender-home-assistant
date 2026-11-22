'use strict';
let learning = null, learnedDraft = [], learningDevice = '', learnSequence = 0;
let openKeyEntry = null;
let openKeyDevice = null;
const stepKeys=['KEY_VOLUMEUP','KEY_VOLUMEDOWN','KEY_BRIGHTNESSUP','KEY_BRIGHTNESSDOWN','KEY_KBDILLUMUP','KEY_KBDILLUMDOWN','KEY_KBDILLUMTOGGLE'];
const keyEditBaseline = new Map();
function refreshKeyEditIndicators(){
  document.querySelectorAll('.key-entry').forEach(entry=>entry.updateEditState?.());
}
const keyNames = {KEY_VOLUMEUP:'Lauter',KEY_VOLUMEDOWN:'Leiser',KEY_MUTE:'Stumm',KEY_PLAYPAUSE:'Play/Pause',TOUCHPAD_SLIDE_LEFT:'Slide links',TOUCHPAD_SLIDE_RIGHT:'Slide rechts',TOUCHPAD_SLIDE_UP:'Slide hoch',TOUCHPAD_SLIDE_DOWN:'Slide runter',TOUCHPAD_SLIDE_UP_LEFT:'Slide links oben',TOUCHPAD_SLIDE_UP_RIGHT:'Slide rechts oben',TOUCHPAD_SLIDE_DOWN_LEFT:'Slide links unten',TOUCHPAD_SLIDE_DOWN_RIGHT:'Slide rechts unten'};
function keyId() { return Array.from(crypto.getRandomValues(new Uint8Array(12)), n=>n.toString(16).padStart(2,'0')).join(''); }
function learnedKey(device, control, topicName=learning?.topic_name) {
  if(!topicName)throw new Error('Gerätename für Topics fehlt. Anlernmodus neu starten.');
  const base=topicName+'-'+control.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  return {id:'key-'+keyId(),device,control,name:keyNames[control]||control.replace(/^KEY_/,''),enabled:true,
    topic_version:2,device_topic:topicName,
    press:true,release:true,switch:true,press_plus:true,release_plus:true,switch_mode:'toggle',
    state:true,button:true,button_plus:true,click:true,double_click:true,hold:true,
    press_topic:base+'/press',release_topic:base+'/release',switch_topic:base+'/switch',
    press_plus_topic:base+'/press-plus',release_plus_topic:base+'/release-plus',
    state_topic:base+'/state',button_topic:base+'/button',button_plus_topic:base+'/button-plus',
    click_topic:base+'/click',double_click_topic:base+'/double-click',hold_topic:base+'/hold',
    double_ms:300,hold_ms:700,targets:null,icon:'',
    repeat:['KEY_VOLUMEUP','KEY_VOLUMEDOWN'].includes(control),repeat_delay:500,repeat_interval:150};
}
function collectLearned() {
  if(!learning)return false;
  let added=false;
  const events=status.events.filter(e=>e.learning_id===learning.id&&e.sequence>learnSequence).sort((a,b)=>a.sequence-b.sequence);
  for(const event of events){
    learnSequence=Math.max(learnSequence,event.sequence);
    if(event.gesture!=='press')continue;
    const known=[...(config.keys||[]),...config.bindings,...learnedDraft];
    if(known.some(k=>k.device===event.device&&k.control===event.control))continue;
    learnedDraft.push(learnedKey(event.device,event.control));added=true;
  }
  return added;
}
function deviceKeyGroup(parent,id){
  const existing=[...document.querySelectorAll('.key-device')].find(g=>g.dataset.deviceId===id);
  if(existing)return existing;
  const name=config.devices[id]?.name||id,group=el('details',undefined,'key-device');
  group.dataset.deviceId=id;group.name='usb-key-devices';
  const count=[...(config.keys||[]),...config.bindings].filter(k=>k.device===id).length;
  group.append(el('summary',name+' · '+count+' Tasten / Belegungen'));group.open=openKeyDevice===id;
  group.addEventListener('toggle',()=>{if(!group.isConnected)return;if(group.open){openKeyDevice=id;document.querySelectorAll('.key-device').forEach(other=>{if(other!==group)other.open=false;});}else if(openKeyDevice===id)openKeyDevice=null;});
  parent.append(group);
  [...parent.querySelectorAll(':scope > .key-device')].sort((a,b)=>(config.devices[a.dataset.deviceId]?.name||a.dataset.deviceId).localeCompare(config.devices[b.dataset.deviceId]?.name||b.dataset.deviceId,'de',{numeric:true})).forEach(g=>parent.append(g));
  return group;
}
function drawKeyList(parent, rows, draft=false, grouped=false) {
  if(!rows.length){parent.append(el('p',draft?'Noch keine neue Taste angelernt.':'Noch keine Tastenliste. Anlernmodus starten; vorhandene Einzelbelegungen bleiben unten erhalten.'));return;}
  if(!draft&&!grouped){
    const groups=new Map();for(const row of rows){if(!groups.has(row.device))groups.set(row.device,[]);groups.get(row.device).push(row);}
    const names=id=>config.devices[id]?.name||id;
    for(const [id,keys] of [...groups].sort(([a],[b])=>names(a).localeCompare(names(b),'de',{numeric:true})||a.localeCompare(b))){
      const group=deviceKeyGroup(parent,id);drawKeyList(group,keys,false,true);
    }
    return;
  }
  const list=el('div',undefined,'key-list');parent.append(list);
  rows.forEach(k=>{
    if(!keyEditBaseline.has(k.id))keyEditBaseline.set(k.id,cloneConfig(k));
    const entry=el('details',undefined,'key-entry');entry.dataset.keyId=k.id;entry.name='usb-key-entries';
    const summary=el('summary'),title=el('span',undefined,'key-entry-title');summary.append(title);entry.append(summary);
    function updateTitle(){title.textContent=(config.devices[k.device]?.name||k.device)+' – '+k.control+' – '+(k.name||'Ohne Namen');}
    updateTitle();entry.open=openKeyEntry===k.id;
    entry.addEventListener('toggle',()=>{
      if(!entry.isConnected)return;
      if(entry.open){
        openKeyEntry=k.id;
        document.querySelectorAll('.key-entry').forEach(other=>{if(other!==entry)other.open=false;});
      }else if(openKeyEntry===k.id)openKeyEntry=null;
    });
    const wrap=el('div',undefined,'table-wrap'),table=el('table',undefined,'key-table'),head=el('tr');
    ['Aktiv','USB-Gerät · Taste / Name','Press / Press+','Release / Release+','Switch / Tastenzustand','Button / Button+','Einzelne Gesten','Icon / Bearbeiten'].forEach(x=>head.append(el('th',x)));table.append(head);
    const tr=el('tr');
    function cell(){const td=el('td');tr.append(td);return td;}
    field(cell(),'Aktiv',k.enabled,v=>k.enabled=v,'checkbox');
    const name=cell();name.append(el('small',config.devices[k.device]?.name||k.device),el('div',k.control,'device-id'));field(name,'Name',k.name,v=>{k.name=v;k.deck_auto_label=false;updateTitle();});
    const groups=[['press','press_plus'],['release','release_plus'],['switch','state'],['button','button_plus'],['click','double_click','hold']];
    const labels={press:'Press',press_plus:'Press+ · danach leer',release:'Release',release_plus:'Release+ · danach leer',
      switch:'Switch · Drücken schaltet um',state:'Tastenzustand · gedrückt ON',button:'Button · alle Gesten',button_plus:'Button+ · danach leer',
      click:'Klick',double_click:'Doppelklick',hold:'Halten'};
    groups.forEach(group=>{
      const td=cell();
      function channel(channel,label){
        const extras=['state','button','button_plus','click','double_click','hold'];
        const entry=el('div',undefined,'key-channel');td.append(entry);
        field(entry,label,k[channel]??!extras.includes(channel),v=>k[channel]=v,'checkbox');
        const fallbackTopic=k.topic_version===2?k.device_topic+'-'+k.control.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'/'+channel.replace('_','-'):'';
        const input=field(entry,'Topic',k[channel+'_topic']??fallbackTopic,v=>{k[channel+'_topic']=v;preview();});input.placeholder='Automatisch';
        input.title=input.value;
        const targetDetails=el('details',undefined,'key-targets');targetDetails.append(el('summary','Ziele'));const targetText=el('div');targetDetails.append(targetText);entry.append(targetDetails);
        function preview(){
          input.title=input.value;
          targetText.replaceChildren();const targets=k.targets??config.devices[k.device]?.targets??config.default_targets;
          targets.forEach(id=>{const b=config.brokers.find(b=>b.id===id);if(!b)return;
            const fallback=k.topic_version===2?k.device_topic+'-'+k.control.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'/'+channel.replace('_','-'):b.prefix+'/'+k.device+'/'+k.control.toLowerCase().replace(/[^a-z0-9_-]/g,'-')+'/'+channel;
            targetText.append(el('small',b.name+': '+(k[channel+'_topic']||fallback),'topic-preview'));
          });
        }preview();
      }
      group.forEach(mode=>{
        if(k.topic_version===2||['press','release','switch'].includes(mode))channel(mode,labels[mode]);
        else if(['press_plus','release_plus'].includes(mode))field(td,labels[mode],k[mode],v=>k[mode]=v,'checkbox');
      });
      if(group[0]==='switch'&&k.switch_mode==='momentary')td.append(el('small','Kompatibilität: bisheriger Switch folgt Drücken/Loslassen. Umschaltung unter Bearbeiten wählen.'));
    });
    const icon=cell();
    iconField(icon,'Icon',k.icon,v=>k.icon=v);
    button(icon,'Bearbeiten',()=>{detailRow.hidden=!detailRow.hidden;});table.append(tr);
    const detailRow=el('div',undefined,'key-options');detailRow.hidden=true;const details=detailRow;
    field(details,'Switch-Verhalten',k.switch_mode||'toggle',v=>k.switch_mode=v,'select',[['toggle','Umschalter: Drücken ON, nächstes Drücken OFF'],['momentary','Kompatibilität: Drücken ON, Loslassen OFF']]);
    if(k.topic_version===2){
      const times=el('div',undefined,'fields');details.append(times);
      const double=field(times,'Doppelklick-Zeit (ms)',k.double_ms??300,v=>k.double_ms=v,'number');double.min=150;double.max=1000;
      const hold=field(times,'Halten ab (ms)',k.hold_ms??700,v=>k.hold_ms=v,'number');hold.min=400;hold.max=5000;
      details.append(el('small','Button: click, double_click oder hold. Ein Einzelklick wartet das Doppelklick-Fenster ab. Doppelklick und Halten erzeugen keinen zusätzlichen Klick.'));
    }
    field(details,'Geräteziele übernehmen',k.targets==null,v=>{k.targets=v?null:[];render();},'checkbox');
    if(k.targets!=null)routes(details,k.targets,v=>k.targets=v);
    if(['KEY_VOLUMEUP','KEY_VOLUMEDOWN'].includes(k.control)){
      field(details,'Wiederholen beim Halten (Press-Topic)',k.repeat,v=>k.repeat=v,'checkbox');
      const fields=el('div',undefined,'fields');details.append(fields);
      const delay=field(fields,'Start nach (ms)',k.repeat_delay,v=>k.repeat_delay=v,'number');delay.min=200;delay.max=5000;
      const interval=field(fields,'Abstand (ms)',k.repeat_interval,v=>k.repeat_interval=v,'number');interval.min=100;interval.max=2000;
      details.append(el('small','Wiederholt die aktiven Press-/Press+-Kanäle, nicht Release oder Switch. Das Zielsystem legt den Lautstärkeschritt fest. Sicherheitsstopp nach 30 Sekunden ohne Loslassen.'));
    }
    if(stepKeys.includes(k.control))field(details,'Jeden … Schritt senden',k.step_every??1,v=>k.step_every=Number(v),'select',[1,2,3,4,5].map(n=>[String(n),n===1?'1 · jeden Schritt':n+' · jeden '+n+'. Schritt']));
    button(details,'Aus Liste entfernen',()=>{const source=draft?learnedDraft:config.keys;source.splice(source.indexOf(k),1);dirty();render();},'danger');
    wrap.append(table);entry.append(wrap,detailRow);
    const actions=el('div',undefined,'key-edit-actions');
    const reminder=el('p','Änderungen noch nicht gespeichert. Speichern übernimmt alle geänderten Einstellungen.','warning');reminder.setAttribute('role','status');
    if(!draft){
      const buttons=el('div',undefined,'row');
      const save=button(buttons,'Speichern',()=>$('#save').onclick(),'primary');
      const cancel=button(buttons,'Abbrechen',()=>{
        const original=(savedConfig?.keys||[]).find(row=>row.id===k.id)||keyEditBaseline.get(k.id);
        const source=draft?learnedDraft:config.keys;source[source.indexOf(k)]=cloneConfig(original);
        changed=JSON.stringify(config)!==JSON.stringify(savedConfig);
        $('#save').disabled=!changed||!!learning;$('#dirty').textContent=changed?'Ungespeicherte Änderungen':'Gespeichert';
        render();
      });
      actions.append(reminder,buttons);entry.append(actions);
      entry.updateEditState=()=>{
        const original=(savedConfig?.keys||[]).find(row=>row.id===k.id)||keyEditBaseline.get(k.id);
        const modified=JSON.stringify(k)!==JSON.stringify(original);
        reminder.hidden=!modified;save.disabled=!modified||!!learning||!!learnedDraft.length;cancel.disabled=!modified;
        entry.classList.toggle('key-modified',modified);
        summary.title=modified?'Ungespeicherte Änderungen – bitte speichern.':'';
      };
      entry.updateEditState();
    }
    list.append(entry);
  });
}
function learningPanel() {
  const c=card('Anlernmodus · Tastenliste');
  c.append(el('p','Gerät freigeben und speichern. Anlernen starten und jede Taste einmal drücken. Gleiche Tasten werden nur einmal erfasst; vorhandene Belegungen bleiben erhalten. Währenddessen sendet dieses Gerät keine MQTT-Aktionen.'));
  const row=el('div',undefined,'toolbar');c.append(row);
  const select=el('select');select.setAttribute('aria-label','USB-Gerät zum Anlernen');
  Object.entries(config.devices).filter(([,d])=>d.enabled).forEach(([id,d])=>{const o=el('option',d.name||id);o.value=id;select.append(o);});
  select.value=learning?.device||learningDevice||select.options[0]?.value||'';select.disabled=!!learning;select.onchange=()=>learningDevice=select.value;row.append(select);
  if(!learning){
    button(row,'Anlernen starten',async()=>{
      if(changed)throw new Error('Vor dem Anlernen vorhandene Änderungen speichern.');
      if(learnedDraft.length)throw new Error('Die vorige Liste zuerst übernehmen oder verwerfen.');
      if(!serviceAlive())throw new Error('USB-/MQTT-Dienst ist nicht aktiv.');
      learning=await api('learning',{action:'start',device:select.value});learnSequence=0;render();
      $('#save').disabled=true;
    },'primary');
  }else{
    row.append(el('strong','Anlernmodus aktiv · MQTT für dieses Gerät pausiert'));
    button(row,'Anlernen beenden',async()=>{await endLearning();render();});
  }
  const draft=el('div');draft.id='learned-draft';c.append(draft);drawKeyList(draft,learnedDraft,true);
  if(!learning&&learnedDraft.length){
    button(c,'Tasten übernehmen',()=>{config.keys||=[];config.keys.push(...learnedDraft);learnedDraft=[];dirty();render();notice('Tasten übernommen. Jetzt speichern, um MQTT zu aktivieren.');},'primary');
    button(c,'Anlernliste verwerfen',()=>{learnedDraft=[];render();});
  }
  c.append(el('small','Neue Tasten erhalten alle Topics: press/release und Plus, switch als Umschalter, state als Tastenzustand, button/button-plus sowie click/double-click/hold. Alle Kanäle sind einzeln abschaltbar. Bestehende Zusatzkanäle bleiben aus, bis du sie aktivierst.'));
  const list=card('Gespeicherte Tasten');list.id='saved-keys';drawKeyList(list,config.keys||[]);
}
async function endLearning() {
  if(!learning)return;
  if(learning.stopping)return;
  learning.stopping=true;
  const lease=learning;
  try{
    const stopped=await api('learning',{action:'stop',id:lease.id});
    // Status snapshots are written every two seconds. Include the final key even
    // when the user ends learning immediately after pressing it (Pi clock only).
    for(let attempt=0;attempt<13;attempt++){
      status=await api('status');collectLearned();
      if((status.updated||0)>=(stopped.stopped_at||0))break;
      await new Promise(resolve=>setTimeout(resolve,250));
    }
    learning=null;
  }catch(e){lease.stopping=false;throw e;}
  $('#save').disabled=!changed;
}
async function pollLearning() {
  if(!learning||learning.stopping)return;
  try{
    const updated=await api('learning',{action:'heartbeat',id:learning.id});
    if(!learning||learning.stopping)return;
    learning=updated;
    if(collectLearned()&&page==='bindings')render();
  }catch(e){learning=null;$('#save').disabled=!changed;render();error(new Error('Anlernmodus unterbrochen. Neue Tasten bleiben als Entwurf erhalten. '+e.message));}
}
