const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,ctx=dom.getInternalVMContext();
let config={devices:{pad:{name:'Generic USB Joystick',enabled:true,targets:['broker1']},keyboard:{name:'Keyboard',enabled:true}},brokers:[],default_targets:[],keys:[],bindings:[],mobile:{trusted:[{name:'Tablet',public_key:'preserved'}]}};
const status={active:true,devices:[{id:'pad',name:'Generic USB Joystick',kind:'input',vendor:'0079',product_id:'0006'},{id:'keyboard',name:'Keyboard',kind:'input',vendor:'046d',product_id:'c31c'}],events:[],brokers:{},errors:{}};
w.setInterval=()=>{};
w.fetch=async(path,options)=>{
  const body=options?.body&&JSON.parse(options.body);let result={ok:true};
  if(path==='/api/config'){if(body)config=structuredClone(body);else result=config;}
  if(path==='/api/status')result=status;
  if(path==='/api/icons/catalog')result={items:[],licenses:{}};
  return {ok:true,json:async()=>structuredClone(result)};
};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),ctx);
const settle=()=>new Promise(r=>setTimeout(r,20));
const input=(label,value)=>{const e=w.document.querySelector('[aria-label="'+label+'"]');assert.ok(e,label);e[e.type==='checkbox'?'checked':'value']=value;e.dispatchEvent(new w.Event(e.type==='checkbox'?'change':'input'));return e;};
(async()=>{
  await vm.runInContext('enter()',ctx);w.document.querySelector('[data-page=devices]').click();await settle();
  assert.equal(w.document.querySelectorAll('.gamepad-options').length,1,'profile only for tested USB ID');
  assert.equal(w.document.querySelectorAll('.gamepad-axis-tile').length,4);
  assert.ok([...w.document.querySelectorAll('.gamepad-axis-tile output')].every(e=>e.textContent==='Pausiert'));
  input('Stickwerte per MQTT senden (0–100)',true);
  assert.ok([...w.document.querySelectorAll('.gamepad-axis-tile output')].every(e=>e.textContent==='Vorschau'));
  input('Gamepad-Senderate je Achse (1–30/s)','5');input('Linker Stick X · Topic','custom/stick/x');input('Rechter Stick Y · Wert senden',false);
  w.document.querySelector('#save').click();await settle();
  const settings=config.devices.pad;
  assert.equal(settings.gamepad_profile,'dragonrise-0079-0006');assert.equal(settings.gamepad_axes_enabled,true);assert.equal(settings.gamepad_rate,5);
  assert.equal(settings.gamepad_axes.left_x.topic,'custom/stick/x');assert.equal(settings.gamepad_axes.right_y.enabled,false);
  assert.equal(config.mobile.trusted[0].public_key,'preserved');
  for(const [control,name] of [['BTN_BASE','L1'],['BTN_BASE2','R1'],['BTN_TOP2','L2'],['BTN_PINKIE','R2'],['BTN_BASE5','Linker Stick-Klick'],['BTN_BASE6','Rechter Stick-Klick']]){
    const learned=vm.runInContext(`learnedKey('pad',${JSON.stringify(control)},'Generic USB Joystick')`,ctx);assert.equal(learned.name,name);assert.equal(learned.control,control);
  }
  assert.equal(vm.runInContext("learnedName('keyboard','BTN_BASE')",ctx),'BTN_BASE');
  status.events=[{device:'pad',control:'GAMEPAD_LEFT_X',gesture:'value',value:75,time:Date.now()/1000}];
  vm.runInContext('status='+JSON.stringify(status)+';refreshGamepadVisuals()',ctx);
  assert.equal(w.document.querySelector('[data-axis=left_x] output').textContent,'75');
  assert.equal(w.document.querySelector('[data-axis=left_x] meter').value,75);
  assert.equal(w.document.querySelector('[data-axis=right_y] output').textContent,'Pausiert');
  input('Stickwerte per MQTT senden (0–100)',false);w.document.querySelector('#save').click();await settle();
  assert.equal(config.devices.pad.gamepad_axes.left_x.topic,'custom/stick/x');
  assert.equal(w.document.querySelector('#error').textContent,'');
  console.log('Gamepad DOM: opt-in, four axes, labels, rate/topics, save, live values and preserved pairing OK');dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
