const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,ctx=dom.getInternalVMContext();
let config={devices:{old:{name:'Saved drive',enabled:false,targets:['broker1'],hardware:{usb_class:'mass-storage'}},key:{name:'Keyboard',enabled:true,targets:['broker1']}},brokers:[{id:'broker1',name:'HA'}],default_targets:['broker1'],keys:[],bindings:[],mobile:{trust:'keep'}};
const status={active:true,devices:[{id:'new',name:'SanDisk',kind:'inventory',usb_storage:true},{id:'key',name:'Keyboard',kind:'input'}],events:[],brokers:{},errors:{}};
w.setInterval=()=>{};
w.fetch=async(path,options)=>{if(path==='/api/config'&&options?.body)config=JSON.parse(options.body);return {ok:true,json:async()=>structuredClone(path==='/api/config'?config:path==='/api/status'?status:path==='/api/icons/catalog'?{items:[],licenses:{}}:{ok:true})};};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),ctx);
const settle=()=>new Promise(r=>setTimeout(r,20));
const drive=()=>w.document.querySelector('.usb-drive[data-device=new]');
function change(label,on){const input=drive().querySelector('[aria-label="'+label+'"]');input.checked=on;input.dispatchEvent(new w.Event('change'));}
(async()=>{
 await vm.runInContext('enter()',ctx);w.document.querySelector('[data-page=devices]').click();await settle();
 assert.equal(drive().querySelectorAll('input:checked').length,0,'new storage has no input or MQTT defaults');
 assert.equal(drive().querySelector('[aria-label="Gerät für Eingaben freigeben"]'),null);
 assert.equal(drive().querySelector('[aria-label="Stream-Deck-Helligkeit (0–100)"]'),null);
 change('System',true);assert.equal(drive().querySelector('details').open,false);assert.match(drive().querySelector('summary').textContent,/SanDiskSystemlaufwerk/);
 drive().querySelector('details').open=true;change('Hidden',true);
 assert.equal(drive().querySelector('[aria-label=System]').checked,false);assert.equal(drive().querySelector('details').open,false);assert.equal(drive().querySelector('summary strong').textContent,'SanDisk');assert.ok(drive().querySelector('summary .badge').hidden);
 w.document.querySelector('#save').click();await settle();assert.equal(config.devices.new.device_view,'hidden');assert.deepEqual(config.devices.new.targets,[]);
 assert.equal(drive().querySelector('details').open,false);assert.deepEqual(config.devices.old.targets,['broker1']);assert.equal(config.devices.key.enabled,true);assert.equal(config.mobile.trust,'keep');
 assert.ok(w.document.querySelector('.usb-drive[data-device=old]'),'saved disconnected drive classified');
 drive().querySelector('details').open=true;change('System',true);w.document.querySelector('#save').click();await settle();assert.equal(config.devices.new.device_view,'system');assert.equal(drive().querySelector('[aria-label=Hidden]').checked,false);
 drive().querySelector('details').open=true;change('System',false);assert.equal(drive().querySelector('details').open,true);
 w.document.querySelector('#save').click();await settle();assert.equal(config.devices.new.device_view,'normal');
 assert.equal(w.document.querySelector('#error').textContent,'');dom.window.close();console.log('USB drive DOM: defaults, exclusive System/Hidden, collapse/reopen, offline state, save/reload and preserved settings OK');
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
