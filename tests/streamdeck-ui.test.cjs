const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,context=dom.getInternalVMContext();
let config={schema:1,devices:{deck:{enabled:true,name:'Office',targets:['broker1'],brightness:30}},brokers:[{id:'broker1',name:'HA',enabled:true}],default_targets:['broker1'],bindings:[{id:'original',device:'deck',control:'key:0',gesture:'press',topic:'existing/topic',payload:'original'}]};
let snapshot={active:true,devices:[],events:[],brokers:{},errors:{}},poll,previews=0;
w.setInterval=callback=>{poll=callback;};
w.fetch=async(path,options)=>{
  const body=options?.body&&JSON.parse(options.body);let result={ok:true};
  if(path==='/api/config'){if(body)config=structuredClone(body);else result=config;}
  if(path==='/api/status')result=snapshot;
  if(path==='/api/icons')result=[{id:'a'.repeat(32),name:'Light',collection:'Own',tags:[]}];
  if(path==='/api/icons/catalog')result={items:[{id:'a'.repeat(32),name:'Light',collection:'Own',tags:[]}],licenses:{}};
  if(path==='/api/deck/preview'){previews++;result={image:'fake-test-image'};}
  return {ok:true,json:async()=>structuredClone(result)};
};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),context);
const settle=()=>new Promise(r=>setImmediate(r));
const click=async text=>{const b=[...w.document.querySelectorAll('button')].find(b=>b.textContent===text);assert.ok(b,text);b.click();await settle();};
function input(label,value,event='input'){
  const node=[...w.document.querySelectorAll('label')].find(l=>l.firstChild?.textContent===label)?.querySelector('input,select');assert.ok(node,label);node.value=value;node.dispatchEvent(new w.Event(event,{bubbles:true}));
}
(async()=>{
  await vm.runInContext('enter()',context);await settle();
  const tab=w.document.querySelector('[data-page=streamdeck]');assert.equal(tab.hidden,false);
  snapshot.devices=[{id:'deck',kind:'streamdeck',name:'Mini',deck:{model:'Stream Deck Mini',keys:6,layout:[2,3],visual:true,size:[80,80]}}];
  await poll();assert.equal(tab.hidden,false);tab.click();await settle();
  assert.equal(w.document.querySelectorAll('.deck-key').length,6);
  assert.ok(w.document.querySelector('.deck-columns-3'));
  assert.equal(config.bindings.length,1);
  input('Beschriftung','Kitchen');input('Hintergrundfarbe','#224466','change');
  async function chooseIcon(label){const trigger=w.document.querySelector('.icon-picker-trigger[aria-label="'+label+'"]');trigger.click();await settle();const pack=w.document.querySelector('.icon-picker-package');pack.open=true;await new Promise(r=>setTimeout(r,20));w.document.querySelector('.icon-picker-tile').click();await settle();await click('Übernehmen');}
  await chooseIcon('Icon / Vordergrundbild');
  await click('Speichern');
  assert.equal(config.devices.deck.deck_keys['0'].text,'Kitchen');
  assert.equal(config.devices.deck.deck_keys['0'].background,'#224466');
  assert.equal(config.bindings[0].topic,'existing/topic');
  assert.equal(config.bindings[0].payload,'original');
  assert.equal(config.keys.length,6,'All deck keys receive standard channels');
  assert.equal(config.keys[0].press_topic,'office-key-0/press');
  assert.equal(config.keys[0].button_plus_topic,'office-key-0/button-plus');
  await chooseIcon('Icon bei gedrückter Taste');
  const check=label=>[...w.document.querySelectorAll('label.check')].find(l=>l.textContent===label).querySelector('input');
  check('Hintergrundfarbe gedrückt verwenden').click();await settle();
  input('Hintergrundfarbe gedrückt','#556677','change');
  check('Schriftfarbe gedrückt verwenden').click();await settle();
  input('Schriftfarbe gedrückt','#ffee00','change');
  check('Vorschau: Taste gedrückt').click();await settle();
  await click('Speichern');
  assert.equal(config.devices.deck.deck_keys['0'].pressed_icon,'a'.repeat(32));
  assert.equal(config.devices.deck.deck_keys['0'].pressed_background,'#556677');
  assert.equal(config.devices.deck.deck_keys['0'].pressed_text_color,'#ffee00');
  const savedKeys=JSON.stringify(config.keys);
  await poll();assert.equal(JSON.stringify(config.keys),savedKeys,'Polling does not duplicate or rename mappings');
  w.document.querySelector('[data-key="1"]').click();await settle();await click('MQTT-Aktion hinzufügen');
  input('Sende-Topic (leer = bisherige Automatik)','office/light/set');input('Nutzdaten (leer = Ereignis als JSON)','ON');
  await click('Speichern');assert.equal(config.bindings.length,2);assert.equal(config.bindings[1].control,'key:1');assert.equal(config.bindings[1].topic,'office/light/set');
  // Device disappears without losing saved artwork/actions. Reconnect and render again.
  const selected=w.document.querySelector('.deck-key.selected'),editor=w.document.querySelector('.deck-workspace');
  snapshot.devices=[];await poll();assert.equal(tab.hidden,false);assert.equal(w.document.querySelector('#page-title').textContent,'Stream Deck');
  assert.equal(w.document.querySelector('.deck-workspace'),editor);assert.equal(w.document.querySelector('.deck-key.selected'),selected);
  assert.match(w.document.querySelector('#deck-connection').textContent,/Offline/);
  assert.equal(config.devices.deck.deck_keys['0'].text,'Kitchen');
  input('Beschriftung','Offline draft');
  snapshot.devices=[{id:'deck',kind:'streamdeck',name:'Mini',deck:{model:'Stream Deck Mini',keys:6,layout:[2,3],visual:true,size:[80,80]}}];
  await poll();assert.equal(w.document.querySelector('.deck-workspace'),editor);assert.match(w.document.querySelector('#deck-connection').textContent,/Online/);
  assert.equal([...w.document.querySelectorAll('label')].find(l=>l.firstChild?.textContent==='Beschriftung').querySelector('input').value,'Offline draft');
  await click('Speichern');assert.equal(config.devices.deck.deck_keys['1'].text,'Offline draft');
  snapshot.devices=[{id:'deck',kind:'streamdeck',name:'Pedal',deck:{model:'Stream Deck Pedal',keys:3,layout:[1,3],visual:false,size:[72,72]}}];
  await poll();tab.click();await settle();assert.ok(w.document.body.textContent.includes('keine Tastenbildschirme'));
  snapshot.active=false;await poll();assert.equal(tab.hidden,false);assert.match(w.document.querySelector('#deck-connection').textContent,/Offline/);
  snapshot.active=true;snapshot.devices=[];await poll();
  w.document.querySelector('[data-page=mobile]').click();await settle();
  vm.runInContext('dirty()',context);
  snapshot.devices=[{id:'tablet',kind:'streamdeck',connection:'mobile',name:'Tablet',deck:{model:'Mobile',keys:15,layout:[3,5],visual:true,size:[72,72]}}];
  await poll();assert.equal(w.document.querySelector('#page-title').textContent,'Stream Deck Mobile','Keep dirty form');
  await click('Speichern');
  assert.equal(w.document.querySelector('#page-title').textContent,'Stream Deck');
  assert.equal(w.document.querySelectorAll('.deck-key').length,15);assert.ok(w.document.querySelector('.deck-columns-5'));
  assert.equal(config.devices.tablet,undefined,'Opening an editor does not auto-save or enable MQTT');
  assert.equal(w.document.querySelector('[aria-label="Spalten (X) erweitern"]'),null);
  vm.runInContext("config.devices.tablet.mobile_layout={rows:8,columns:8}",context); // Old setting must be inert.
  input('Beschriftung','Draft across native resize');
  const draftField=[...w.document.querySelectorAll('label')].find(l=>l.firstChild?.textContent==='Beschriftung').querySelector('input');
  snapshot.devices[0].deck={...snapshot.devices[0].deck,keys:24,layout:[4,6]};await poll();
  assert.equal(w.document.querySelectorAll('.deck-key').length,24);
  assert.equal([...w.document.querySelectorAll('label')].find(l=>l.firstChild?.textContent==='Beschriftung').querySelector('input'),draftField);
  assert.equal(draftField.value,'Draft across native resize');
  await click('Speichern');assert.deepEqual(config.devices.tablet.mobile_layout,{rows:8,columns:8});
  const mobileEditor=w.document.querySelector('.deck-workspace');snapshot.devices=[];await poll();
  assert.equal(w.document.querySelector('.deck-workspace'),mobileEditor);assert.equal(w.document.querySelectorAll('.deck-key').length,24);
  vm.runInContext("config.devices.tablet.deck_info={model:'Mobile',keys:24,layout:[4,6],visual:true,size:[72,72]};config.devices.tablet.deck_connection='mobile';knownDecks.clear();render()",context);
  assert.equal(w.document.querySelectorAll('.deck-key').length,24,'Saved geometry reopens while offline');
  w.document.querySelector('[data-page=mobile]').click();await settle();await poll();
  assert.equal(w.document.querySelector('#page-title').textContent,'Stream Deck Mobile','No repeated automatic navigation');
  console.log('Stream Deck DOM: hotplug, layout, artwork save, existing topics, MQTT assignment, pedal and stale service OK');
  dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
