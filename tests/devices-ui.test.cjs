const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,ctx=dom.getInternalVMContext();
const key=(id,device,control)=>({id,device,control,name:id,enabled:true,targets:null,step_every:1});
let config={schema:1,devices:{z:{name:'Zulu',enabled:true},a:{name:'Alpha',enabled:true}},brokers:[],default_targets:[],bindings:[{id:'old',device:'z',control:'KEY_F1',gesture:'press',text:'Legacy'}],keys:[key('vol','a','KEY_VOLUMEUP'),key('bright','z','KEY_BRIGHTNESSUP')]};
let status={active:true,updated:Date.now()/1000,devices:[{id:'new',name:'Fresh',kind:'input',observed_id:'physical',vendor:'046d'}],events:[],brokers:{},errors:{}};
let confirmation=false;const actions=[];
w.confirm=()=>confirmation;w.setInterval=()=>{};
w.fetch=async(path,options)=>{
  const body=options?.body&&JSON.parse(options.body);let result={ok:true};
  if(path==='/api/config'){if(body)config=structuredClone(body);else result=config;}
  if(path==='/api/status')result=status;
  if(path==='/api/icons/catalog')result={items:[],licenses:{}};
  if(path==='/api/devices'){actions.push(body);result.backup='/test/backup.tar.gz';if(body.action==='remove'){delete config.devices[body.device];config.keys=config.keys.filter(k=>k.device!==body.device);config.bindings=config.bindings.filter(k=>k.device!==body.device);}}
  return {ok:true,json:async()=>structuredClone(result)};
};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),ctx);
const settle=()=>new Promise(r=>setTimeout(r,20));
(async()=>{
  await vm.runInContext('enter()',ctx);w.document.querySelector('[data-page=bindings]').click();await settle();
  let groups=[...w.document.querySelectorAll('.key-device')];assert.deepEqual(groups.map(g=>g.dataset.deviceId),['a','z']);assert.ok(groups.every(g=>!g.open));
  assert.equal(groups[1].querySelectorAll('.key-entry').length,2,'legacy entry in same group');
  groups[0].open=true;await settle();groups[1].open=true;await settle();assert.equal(groups[0].open,false);assert.equal(groups[1].open,true);
  const filter=w.document.querySelector('[aria-label="Jeden … Schritt senden"]');assert.equal(filter.options.length,5);filter.value='3';filter.dispatchEvent(new w.Event('change'));
  w.document.querySelector('#save').click();await settle();assert.equal(config.keys[0].step_every,3);
  w.document.querySelector('[data-page=devices]').click();await settle();
  assert.ok(w.document.querySelector('[aria-label="Vorhandenem Gerät zuordnen"]'));
  for(const [label,value] of [['Slide-Empfindlichkeit (1–10)','7'],['Slide-/X/Y-Senderate (1–30/s)','20'],['X-Topic','office/slide/x'],['Y-Topic','office/slide/y']]){
    const input=w.document.querySelector('[aria-label="'+label+'"]');assert.ok(input);input.value=value;input.dispatchEvent(new w.Event('input'));
  }
  const xy=w.document.querySelector('[aria-label="X/Y-Werte zusätzlich per MQTT senden (0–100)"]');xy.checked=true;xy.dispatchEvent(new w.Event('change'));
  w.document.querySelector('#save').click();await settle();
  assert.equal(config.devices.new.touchpad_sensitivity,7);assert.equal(config.devices.new.touchpad_rate,20);
  assert.equal(config.devices.new.touchpad_xy,true);assert.equal(config.devices.new.touchpad_x_topic,'office/slide/x');assert.equal(config.devices.new.touchpad_y_topic,'office/slide/y');
  let remove=w.document.querySelector('[aria-label="Gerät entfernen: Alpha"]');assert.ok(remove);remove.click();await settle();assert.equal(actions.length,0,'cancel preserves data');
  confirmation=true;remove.click();await settle();assert.equal(actions.at(-1).action,'remove');assert.equal(actions.at(-1).device,'a');assert.equal(config.keys.length,1);assert.equal(config.keys[0].id,'bright');
  assert.ok(w.document.querySelector('#notice').textContent.includes('backup.tar.gz'));
  assert.equal(w.document.querySelector('#error').textContent,'');
  console.log('Device DOM: groups, steps, slide sensitivity/rate/XY/topics save, assignment and confirmed scoped removal OK');
  dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
