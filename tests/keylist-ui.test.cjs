// Optional DOM integration test: npm install --prefix .state/ui-test jsdom
const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const html=fs.readFileSync('ugso_usbhub/static/index.html','utf8');
const dom=new JSDOM(html,{url:'http://127.0.0.1:8098',runScripts:'outside-only'});
const w=dom.window;
const style=w.document.createElement('style');style.textContent=fs.readFileSync('ugso_usbhub/static/style.css','utf8');w.document.head.append(style);
let config={schema:1,hub_id:'demo',devices:{kbd:{enabled:true,name:'Trust Keyboard',targets:['broker1','broker2']}},
  brokers:[{id:'broker1',name:'HA',enabled:true,prefix:'test/ha'},{id:'broker2',name:'IOB',enabled:true,prefix:'test/iob'}],default_targets:['broker1'],bindings:[]};
let snapshot={active:true,devices:[],events:[],brokers:{},errors:{}};
let lease,interval;
w.setInterval=callback=>{interval=callback;};
w.fetch=async(path,options)=>{
  const body=options?.body&&JSON.parse(options.body);let result={ok:true};
  if(path==='/api/config'){if(body)config=JSON.parse(JSON.stringify(body));else result=config;}
  if(path==='/api/status')result=snapshot;
  if(path==='/api/icons')result=[];
  if(path==='/api/learning'){
    if(body.action==='start')lease={id:'session',device:body.device,topic_name:'trust-keyboard',expires:Date.now()/1000+15};
    if(body.action==='stop'){
      lease.expires=0;
      snapshot.events.push({sequence:2,learning_id:'session',device:'kbd',control:'KEY_F2',gesture:'press',time:Date.now()/1000});
    }
    result=lease;
  }
  return {ok:true,json:async()=>JSON.parse(JSON.stringify(result))};
};
vm.runInContext(fs.readFileSync('ugso_usbhub/static/keylist.js','utf8'),dom.getInternalVMContext());
vm.runInContext(fs.readFileSync('ugso_usbhub/static/streamdeck.js','utf8'),dom.getInternalVMContext());
vm.runInContext(fs.readFileSync('ugso_usbhub/static/mobile.js','utf8'),dom.getInternalVMContext());
vm.runInContext(fs.readFileSync('ugso_usbhub/static/app.js','utf8'),dom.getInternalVMContext());
const settle=()=>new Promise(r=>setImmediate(r));
const click=async text=>{const b=[...w.document.querySelectorAll('button')].find(b=>b.textContent===text);assert.ok(b,text);b.click();await settle();};
(async()=>{
  await vm.runInContext('enter()',dom.getInternalVMContext());
  await settle();w.document.querySelector('[data-page=bindings]').click();await settle();
  assert.equal(w.document.querySelector('#error').textContent,'',w.document.body.textContent);
  assert.ok(w.document.querySelector('#learned-draft'), w.document.body.textContent);
  await click('Anlernen starten');
  assert.ok(w.document.querySelector('#save').disabled);
  snapshot.events=[{sequence:1,learning_id:'session',device:'kbd',control:'KEY_VOLUMEUP',gesture:'press',time:Date.now()/1000}];
  await interval();
  assert.equal(w.document.querySelectorAll('#learned-draft .key-table').length,1);
  assert.ok([...w.document.querySelectorAll('#learned-draft input')].some(i=>i.value==='Lauter'));
  assert.ok(w.document.querySelector('#learned-draft').textContent.includes('IOB: trust-keyboard-key-volumeup/switch'));
  assert.ok([...w.document.querySelectorAll('#learned-draft input')].some(i=>i.value==='trust-keyboard-key-volumeup/press-plus'));
  await click('Anlernen beenden');await click('Tasten übernehmen');await click('Speichern');
  assert.equal(config.keys.length,2);
  assert.equal(config.keys[0].repeat,true);
  assert.equal(config.keys[0].switch,true);
  assert.equal(config.keys[0].switch_mode,'toggle');
  assert.equal(config.keys[0].button_plus,true);
  assert.equal(config.keys[0].button_topic,'trust-keyboard-key-volumeup/button');
  assert.equal(w.getComputedStyle(w.document.querySelector('main')).maxWidth,'none');
  assert.equal(config.keys[1].control,'KEY_F2');
  assert.equal(config.bindings.length,0);
  assert.equal(w.document.querySelector('#dirty').textContent,'Gespeichert');
  const entries=[...w.document.querySelectorAll('.key-entry')];
  assert.equal(entries.length,2);assert.ok(entries.every(e=>!e.open),'Initially compact');
  assert.match(entries[0].querySelector('summary').textContent,/Trust Keyboard – KEY_VOLUMEUP – Lauter/);
  entries[0].open=true;await new Promise(r=>setTimeout(r,15));
  assert.equal(entries[0].open,true);
  entries[1].open=true;await new Promise(r=>setTimeout(r,15));
  assert.equal(entries[0].open,false);assert.equal(entries[1].open,true);
  entries[0].open=true;await new Promise(r=>setTimeout(r,15));
  const name=entries[0].querySelector('input[type=text]');
  name.value='Volume';name.dispatchEvent(new w.Event('input',{bubbles:true}));
  assert.match(entries[0].querySelector('summary').textContent,/KEY_VOLUMEUP – Volume/);
  vm.runInContext('render()',dom.getInternalVMContext());await settle();
  assert.equal(w.document.querySelectorAll('.key-entry[open]').length,1,'Open entry survives rerender');
  assert.equal(w.document.querySelector('.key-entry[open]').dataset.keyId,config.keys[0].id);
  await click('Bearbeiten');
  assert.ok([...w.document.querySelectorAll('label')].some(l=>l.textContent.includes('Start nach (ms)')));
  let current=[...w.document.querySelectorAll('.key-entry')];
  assert.equal(current[0].querySelector('.key-edit-actions p').hidden,false);
  const secondName=current[1].querySelector('input[type=text]');secondName.value='Other draft';secondName.dispatchEvent(new w.Event('input',{bubbles:true}));
  current[0].querySelector('.key-edit-actions button:last-child').click();await settle();
  current=[...w.document.querySelectorAll('.key-entry')];
  assert.match(current[0].querySelector('summary').textContent,/Lauter$/);
  assert.match(current[1].querySelector('summary').textContent,/Other draft$/);
  assert.equal(w.document.querySelector('#dirty').textContent,'Ungespeicherte Änderungen','Cancel preserves other edits');
  current[1].querySelector('.key-edit-actions button').click();await settle();
  assert.equal(config.keys[0].name,'Lauter');assert.equal(config.keys[1].name,'Other draft');
  assert.equal(w.document.querySelector('#dirty').textContent,'Gespeichert');
  assert.ok([...w.document.querySelectorAll('.key-edit-actions button')].every(b=>b.disabled));
  console.log('DOM: Anlernen → Liste → Beenden → Übernehmen → Speichern → Bearbeiten erfolgreich.');
  dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
