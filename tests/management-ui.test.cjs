const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,ctx=dom.getInternalVMContext();
let config={devices:{keyboard:{name:'Keyboard',enabled:true,targets:['broker1']}},brokers:[{id:'broker1',name:'HA',host:'127.0.0.1',port:1883,prefix:'keep',enabled:true,password_set:true}],default_targets:['broker1'],keys:[],bindings:[],mobile:{trust:'preserved'}};
const status={active:true,devices:[],events:[],brokers:{broker1:'online'},errors:{},management:{webrun:'ON',autorun:'OFF',state:'Webfrontend erreichbar'}};
w.setInterval=()=>{};w.fetch=async(path,options)=>{if(path==='/api/config'&&options?.body)config=JSON.parse(options.body);return {ok:true,json:async()=>structuredClone(path==='/api/config'?config:path==='/api/status'?status:path==='/api/icons/catalog'?{items:[],licenses:{}}:{ok:true})};};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),ctx);
const settle=()=>new Promise(r=>setTimeout(r,20));
(async()=>{
 await vm.runInContext('enter()',ctx);w.document.querySelector('[data-page=brokers]').click();await settle();
 const label='MQTT-Systemsteuerung erlauben (Web/Autostart/Backup)',check=w.document.querySelector('[aria-label="'+label+'"]');assert.equal(check.checked,false);
 check.checked=true;check.dispatchEvent(new w.Event('change'));w.document.querySelector('#save').click();await settle();assert.equal(config.brokers[0].control_enabled,true);assert.equal(config.brokers[0].prefix,'keep');assert.equal(config.devices.keyboard.enabled,true);assert.equal(config.mobile.trust,'preserved');
 w.document.querySelector('[data-page=system]').click();await settle();const content=w.document.querySelector('#content').textContent;
 for(const term of ['usb-extender/global/web/set','usb-extender/global/state/webrun','usb-extender/global/state/autorun','usb-extender/global/state/backup','Home-Assistant-Kartenpaket','USB Extender Cards'])assert.ok(content.includes(term),term);
 const link=w.document.querySelector('a[href="https://github.com/rockbaer2007/usb-extender-cards"]');assert.ok(link);assert.equal(link.target,'_blank');assert.match(link.rel,/noopener/);
 assert.match(w.document.querySelector('#management-status').textContent,/Web: ON · Autostart: OFF/);
 assert.equal(w.document.querySelector('#error').textContent,'');dom.window.close();console.log('MQTT management DOM: opt-in/save, topics, live state, card-package link and settings preserved OK');
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
