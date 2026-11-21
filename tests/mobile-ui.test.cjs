const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,context=dom.getInternalVMContext();
let config={schema:1,devices:{},brokers:[],default_targets:[],bindings:[]};
let snapshot={active:true,devices:[],events:[],brokers:{},errors:{},mobile:{active:false,pending:[],clients:[]}},poll;
const commands=[];
w.setInterval=callback=>{poll=callback;};
w.fetch=async(path,options)=>{
  const body=options?.body&&JSON.parse(options.body);let result={ok:true};
  if(path==='/api/config'){if(body){config=structuredClone(body);snapshot.mobile.active=config.mobile.enabled;}else result=config;}
  if(path==='/api/status')result=snapshot;
  if(path==='/api/icons')result=[];
  if(path==='/api/mobile/qr')result={url:'https://streamdeck.elgato.com/c/?w=test&av2=127.0.0.1:28198',qr:'test'};
  if(path==='/api/mobile/control')commands.push(body);
  return {ok:true,json:async()=>structuredClone(result)};
};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),context);
const settle=()=>new Promise(r=>setImmediate(r));
const click=async text=>{const button=[...w.document.querySelectorAll('button')].find(b=>b.textContent===text);assert.ok(button,text);button.click();await settle();};
(async()=>{
  await vm.runInContext('enter()',context);await settle();
  w.document.querySelector('[data-page=mobile]').click();await settle();
  const enable=[...w.document.querySelectorAll('label')].find(l=>l.textContent.includes('Stream-Deck-Mobile-Server aktivieren')).querySelector('input');
  assert.equal(enable.checked,false);enable.checked=true;enable.dispatchEvent(new w.Event('change'));
  await click('Speichern');assert.equal(config.mobile.enabled,true);await poll();
  await click('Kopplung starten · QR-Code');assert.equal(commands.at(-1).action,'open');assert.ok(w.document.querySelector('.mobile-qr'));
  snapshot.mobile.pending=[{name:'Android test',fingerprint:'12AB34',token:'a'.repeat(32)}];await poll();
  assert.ok(w.document.querySelector('#mobile-status').textContent.includes('12AB34'));
  await click('Gerät vertrauen');assert.deepEqual(commands.at(-1),{action:'allow',token:'a'.repeat(32)});
  await click('Kopplungsfenster schließen');assert.equal(commands.at(-1).action,'close');assert.equal(w.document.querySelector('.mobile-qr'),null);
  console.log('Mobile DOM: default off, enable/save, QR, pending fingerprint, approval and pairing close OK');
  dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
