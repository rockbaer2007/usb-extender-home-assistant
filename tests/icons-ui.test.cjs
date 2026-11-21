const {JSDOM}=require('../.state/ui-test/node_modules/jsdom');
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const dom=new JSDOM(fs.readFileSync('ugso_usbhub/static/index.html','utf8'),{url:'http://127.0.0.1:8098',runScripts:'outside-only'}),w=dom.window,context=dom.getInternalVMContext();
w.TextEncoder=TextEncoder;
function unzipStored(payload){const data=Buffer.from(payload,'base64'),entries=[];let at=0;while(data.readUInt32LE(at)===0x04034b50){const size=data.readUInt32LE(at+18),length=data.readUInt16LE(at+26),extra=data.readUInt16LE(at+28),start=at+30+length+extra;entries.push({name:data.subarray(at+30,at+30+length).toString(),data:data.subarray(start,start+size)});at=start+size;}return entries;}
const config={schema:1,devices:{old:{name:'Existing'}},brokers:[],default_targets:[],bindings:[]},original=JSON.stringify(config),uploads=[];
let library=[];
w.setInterval=()=>{};
w.fetch=async(path,options)=>{
  let result={ok:true};const body=options?.body&&JSON.parse(options.body);
  if(path==='/api/config')result=config;
  if(path==='/api/status')result={active:true,devices:[],events:[],brokers:{},errors:{},storage:{free:2*1024**3,total:8*1024**3}};
  if(path==='/api/icons')result=library;
  if(path==='/api/icons/remove'){library=library.filter(i=>(i.package_folder||i.collection)!==body.package);result={ok:true,backup:'test-backup.zip'};}
  if(path==='/api/icons/upload'){
    uploads.push(body);
    if(body.name.endsWith('.zip')){const entries=unzipStored(body.data);return {ok:true,json:async()=>({imported:entries.filter(e=>/\.(png|svg)$/i.test(e.name)&&!e.name.endsWith('/broken.png')).length,skipped:entries.filter(e=>e.name.endsWith('/broken.png')).map(e=>({file:e.name,reason:'Defekte Bilddatei'}))})};}
    if(body.name==='broken.png')return {ok:false,json:async()=>({error:'Defekte Bilddatei'})};
    result={imported:1,skipped:[]};
  }
  return {ok:true,json:async()=>structuredClone(result)};
};
for(const file of ['archive.js','keylist.js','streamdeck.js','mobile.js','app.js'])vm.runInContext(fs.readFileSync('ugso_usbhub/static/'+file,'utf8'),context);
const settle=()=>new Promise(r=>setImmediate(r));
const fake=(name,path='',size=3)=>({name,webkitRelativePath:path,size,arrayBuffer:async()=>Uint8Array.from([1,2,3]).buffer});
async function run(files,folder){
  const input=w.document.querySelector(folder?'input[webkitdirectory]':'input[type=file]:not([webkitdirectory])');
  Object.defineProperty(input,'files',{configurable:true,value:files});
  [...w.document.querySelectorAll('button')].find(b=>b.textContent===(folder?'Ordner importieren':'Dateien importieren')).click();
  for(let i=0;i<100;i++){await settle();if(!w.document.querySelector('#notice').hidden||!w.document.querySelector('#error').hidden)return;}
  throw Error('Import did not finish');
}
(async()=>{
  await vm.runInContext('enter()',context);w.document.querySelector('[data-page=icons]').click();
  assert.match(w.document.querySelector('#storage-space').textContent,/2 GiB von 8 GiB/);
  vm.runInContext('status.storage.free=1024**2;renderStorage()',context);
  assert.equal(w.document.querySelector('#storage-space').classList.contains('storage-low'),true);
  assert.equal(w.document.querySelector('input[webkitdirectory]').multiple,true);
  await run([fake('lamp.png')],false);
  assert.equal(uploads.length,1);assert.equal(uploads[0].data,'AQID');assert.equal(uploads[0].collection,undefined);
  await run([fake('a.png','Meine Icons/a.png'),fake('b.svg','Meine Icons/sub/b.svg'),fake('note.txt','Meine Icons/note.txt'),fake('broken.png','Meine Icons/broken.png')],true);
  assert.equal(uploads.length,2);assert.equal(uploads[1].name,'Meine Icons.zip');assert.ok(unzipStored(uploads[1].data).some(e=>e.name==='Meine Icons/sub/b.svg'));
  assert.match(w.document.querySelector('#notice').textContent,/2 Icons importiert\. 2 übersprungen/);
  assert.match(w.document.querySelector('#notice').textContent,/Defekte Bilddatei/);
  await run([fake('one.jpg'),fake('two.webp')],false);
  assert.equal(uploads.length,4);
  await run([fake('huge.png','Huge/huge.png',97*1024*1024)],true);
  assert.equal(uploads.length,4);assert.match(w.document.querySelector('#error').textContent,/Importlimit/);
  assert.equal(JSON.stringify(config),original);
  await run([fake('b.svg','IconPacks/fluentui-system-icons-filled.sdIconPack/icons/b.svg'),
    {name:'manifest.json',webkitRelativePath:'IconPacks/fluentui-system-icons-filled.sdIconPack/manifest.json',size:100,arrayBuffer:async()=>new TextEncoder().encode(JSON.stringify({Name:'Fluent UI System Icons (Filled)',Author:'Example',License:'MIT'})).buffer}],true);
  assert.equal(uploads.at(-1).name,'IconPacks.zip');
  const manifest=unzipStored(uploads.at(-1).data).find(e=>e.name.endsWith('/manifest.json'));
  assert.equal(JSON.parse(manifest.data).Name,'Fluent UI System Icons (Filled)');
  assert.equal(JSON.parse(manifest.data).License,'MIT');
  library=[{id:'a'.repeat(32),name:'Signal',filename:'Signal.gif',animated:true,frames:2,collection:'Audio Pack',package_folder:'audio.sdIconPack',subfolder:'icons/Audio',tags:['sound'],license:'MIT',author:'Example'},
    {id:'b'.repeat(32),name:'Bell',filename:'Bell.png',collection:'Audio Pack',package_folder:'audio.sdIconPack',tags:[],license:'MIT',author:'Example'},
    {id:'c'.repeat(32),name:'Lamp',filename:'Lamp.png',collection:'Light Pack',package_folder:'light.sdIconPack',tags:[]}];
  vm.runInContext('iconList='+JSON.stringify(library)+';render()',context);
  assert.equal(w.document.querySelectorAll('.icon-package').length,2);
  assert.equal(w.document.querySelectorAll('.icon-card img').length,0,'No huge image gallery until opened');
  const pack=w.document.querySelector('.icon-package');pack.open=true;await new Promise(r=>setTimeout(r,20));
  assert.equal(pack.querySelectorAll('.icon-card').length,2);
  assert.equal(pack.querySelectorAll('.icon-card details').length,0,'No repeated licence controls per icon');
  assert.equal(pack.querySelectorAll('.icon-pack-license').length,1);
  assert.equal(pack.querySelector('.icon-pack-license pre').textContent,'MIT');
  assert.equal(pack.querySelector('.icon-package-license-label').textContent,'Lizenz: MIT');
  const tile=pack.querySelector('.icon-card');tile.onmouseenter();
  assert.equal(w.document.querySelector('.icon-hover').hidden,false);
  assert.match(w.document.querySelector('.icon-hover').textContent,/Signal.gif/);
  assert.match(tile.querySelector('img').src,/\.webp$/);
  tile.onmouseleave();assert.equal(w.document.querySelector('.icon-hover').hidden,true);
  library[1].license='BSD';vm.runInContext('iconList='+JSON.stringify(library)+';render()',context);
  const narrowSearch=w.document.querySelector('[aria-label=Iconsuche]');narrowSearch.value='Signal';narrowSearch.oninput();
  assert.equal(w.document.querySelector('.icon-package-license-label').textContent,'Lizenzhinweise (2)');
  assert.match(w.document.querySelector('.icon-pack-license pre').textContent,/MIT[\s\S]*BSD/,'Filtering icons preserves all package licences');
  const search=w.document.querySelector('[aria-label=Iconsuche]');search.value='Lamp';search.oninput();
  assert.equal(w.document.querySelectorAll('.icon-package').length,1);
  assert.equal(w.document.querySelector('.icon-package').open,true);
  assert.match(w.document.querySelector('.icon-card').textContent,/Lamp.png/);
  assert.ok(!w.document.querySelector('.icon-card').textContent.includes('c'.repeat(32)));
  w.confirm=()=>true;
  [...w.document.querySelectorAll('button')].find(b=>b.textContent==='Paket entfernen').click();
  for(let i=0;i<10;i++)await settle();
  assert.equal(library.length,2);assert.equal(JSON.stringify(config),original);
  console.log('Icon DOM: single/multiple files, nested folder, collection, skipped formats/errors, size limit and settings preserved OK');
  dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});
