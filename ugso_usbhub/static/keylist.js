'use strict';
let learning = null, learnedDraft = [], learningDevice = '', learnSequence = 0;
const keyNames = {KEY_VOLUMEUP:'Lauter',KEY_VOLUMEDOWN:'Leiser',KEY_MUTE:'Stumm',KEY_PLAYPAUSE:'Play/Pause'};
function keyId() { return Array.from(crypto.getRandomValues(new Uint8Array(12)), n=>n.toString(16).padStart(2,'0')).join(''); }
function learnedKey(device, control) {
  if(!learning?.topic_name)throw new Error('Gerätename für Topics fehlt. Anlernmodus neu starten.');
  const base=learning.topic_name+'-'+control.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  return {id:'key-'+keyId(),device,control,name:keyNames[control]||control.replace(/^KEY_/,''),enabled:true,
    topic_version:2,device_topic:learning.topic_name,
    press:true,release:true,switch:true,press_plus:true,release_plus:true,
    press_topic:base+'/press',release_topic:base+'/release',switch_topic:base+'/switch',
    press_plus_topic:base+'/press-plus',release_plus_topic:base+'/release-plus',targets:null,icon:'',
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
function drawKeyList(parent, rows, draft=false) {
  if(!rows.length){parent.append(el('p',draft?'Noch keine neue Taste angelernt.':'Noch keine Tastenliste. Anlernmodus starten; vorhandene Einzelbelegungen bleiben unten erhalten.'));return;}
  const wrap=el('div',undefined,'table-wrap'),table=el('table',undefined,'key-table'),head=el('tr');
  ['Aktiv','USB-Gerät · Taste / Name','Topic Press','Topic Release','Topic Switch · ON/OFF','Icon',''].forEach(x=>head.append(el('th',x)));table.append(head);
  rows.forEach(k=>{
    const tr=el('tr');
    function cell(){const td=el('td');tr.append(td);return td;}
    field(cell(),'Aktiv',k.enabled,v=>k.enabled=v,'checkbox');
    const name=cell();name.append(el('small',config.devices[k.device]?.name||k.device),el('div',k.control,'device-id'));field(name,'Name',k.name,v=>k.name=v);
    ['press','release','switch'].forEach(mode=>{
      const td=cell();
      function channel(channel,label){
        field(td,label,k[channel],v=>k[channel]=v,'checkbox');
        const input=field(td,'Topic',k[channel+'_topic'],v=>{k[channel+'_topic']=v;preview();});input.placeholder='Automatisch';
        const targetText=el('div');td.append(targetText);
        function preview(){
          targetText.replaceChildren();const targets=k.targets??config.devices[k.device]?.targets??config.default_targets;
          targets.forEach(id=>{const b=config.brokers.find(b=>b.id===id);if(!b)return;
            const fallback=k.topic_version===2?k.device_topic+'-'+k.control.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'/'+channel.replace('_','-'):b.prefix+'/'+k.device+'/'+k.control.toLowerCase().replace(/[^a-z0-9_-]/g,'-')+'/'+channel;
            targetText.append(el('small',b.name+': '+(k[channel+'_topic']||fallback),'topic-preview'));
          });
        }preview();
      }
      channel(mode,'Senden');
      if(mode!=='switch'){
        if(k.topic_version===2)channel(mode+'_plus',mode==='press'?'Press+ · eigener Kanal':'Release+ · eigener Kanal');
        else field(td,mode==='press'?'Press+ · danach leer':'Release+ · danach leer',k[mode+'_plus'],v=>k[mode+'_plus']=v,'checkbox');
      }
    });
    const icon=cell();if(k.icon){const image=el('img');image.src='/icons/'+k.icon+'.png';image.alt=k.name;image.className='key-icon';icon.append(image);}
    field(icon,'Icon',k.icon,v=>k.icon=v,'select',[['','Kein Icon'],...iconList.map(i=>[i.id,i.name])]);
    button(cell(),'Bearbeiten',()=>{const details=tr.nextElementSibling;details.hidden=!details.hidden;});table.append(tr);
    const detailRow=el('tr');detailRow.hidden=true;const details=el('td');details.colSpan=7;detailRow.append(details);table.append(detailRow);
    field(details,'Geräteziele übernehmen',k.targets==null,v=>{k.targets=v?null:[];render();},'checkbox');
    if(k.targets!=null)routes(details,k.targets,v=>k.targets=v);
    if(['KEY_VOLUMEUP','KEY_VOLUMEDOWN'].includes(k.control)){
      field(details,'Wiederholen beim Halten (Press-Topic)',k.repeat,v=>k.repeat=v,'checkbox');
      const fields=el('div',undefined,'fields');details.append(fields);
      const delay=field(fields,'Start nach (ms)',k.repeat_delay,v=>k.repeat_delay=v,'number');delay.min=200;delay.max=5000;
      const interval=field(fields,'Abstand (ms)',k.repeat_interval,v=>k.repeat_interval=v,'number');interval.min=100;interval.max=2000;
      details.append(el('small','Wiederholt die aktiven Press-/Press+-Kanäle, nicht Release oder Switch. Das Zielsystem legt den Lautstärkeschritt fest. Sicherheitsstopp nach 30 Sekunden ohne Loslassen.'));
    }
    button(details,'Aus Liste entfernen',()=>{rows.splice(rows.indexOf(k),1);dirty();render();},'danger');
  });wrap.append(table);parent.append(wrap);
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
  c.append(el('small','Neue Tasten: Gerätename-key-taste/press, /release, /switch, /press-plus und /release-plus. Alle fünf Kanäle sind vorbereitet und aktiv. Nur die Plus-Kanäle werden nach 50 ms leer zurückgesetzt. Switch sendet ON/OFF. Bestehende Topics bleiben erhalten.'));
  const list=card('Gespeicherte Tasten');drawKeyList(list,config.keys||[]);
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
