// Local-only Chromium UI check. The HTTP fixture never contacts a broker/Pi.
const {chromium}=require('../.state/ui-test/node_modules/playwright');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve('ugso_usbhub/static');
const config={schema:1,devices:{kbd:{name:'Büro Tastatur',enabled:true,targets:[]},pad:{name:'T650',enabled:false,targets:[]}},keys:[{id:'vol',device:'kbd',control:'KEY_VOLUMEUP',name:'Lauter',enabled:true,targets:null,step_every:1}],bindings:[],brokers:[],default_targets:[]};
const snapshot={active:true,devices:[{id:'kbd',kind:'input',name:'Büro Tastatur',inputs:[]}],events:[],brokers:{},errors:{}};
const server=http.createServer((req,res)=>{
  if(req.url.startsWith('/api/')){res.setHeader('Content-Type','application/json');res.end(JSON.stringify(req.url==='/api/config'?config:req.url==='/api/status'?snapshot:req.url.includes('icons')?{items:[],licenses:{}}:{ok:true}));return;}
  const target=path.join(root,req.url==='/'?'index.html':req.url.split('?')[0]);
  if(!target.startsWith(root+path.sep)||!fs.existsSync(target)){res.writeHead(404);res.end();return;}
  const types={'.html':'text/html','.js':'text/javascript','.css':'text/css'};res.setHeader('Content-Type',types[path.extname(target)]||'application/octet-stream');res.end(fs.readFileSync(target));
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:'+server.address().port);await page.locator('#workspace').waitFor({state:'visible'});
    await page.locator('[data-page=bindings]').click();const group=page.locator('.key-device');
    assert.equal(await group.count(),1);assert.equal(await group.getAttribute('open'),null);
    await group.locator(':scope > summary').click();await page.locator('.key-entry > summary').click();
    await page.getByRole('button',{name:'Bearbeiten',exact:true}).click();
    await page.getByLabel('Jeden … Schritt senden',{exact:true}).selectOption('5');
    assert.equal(await page.getByLabel('Jeden … Schritt senden',{exact:true}).inputValue(),'5');
    await page.screenshot({path:'.state/devices-029-keys.png',fullPage:true});
    await page.locator('[data-page=devices]').click();await page.getByLabel('Gerät entfernen: T650',{exact:true}).waitFor({state:'visible'});
    assert.ok(await page.getByLabel('Vorhandenem Gerät zuordnen',{exact:true}).count());
    await page.locator('.touchpad-options > summary').first().click();
    await page.getByLabel('Slide-Empfindlichkeit (1–10)',{exact:true}).first().fill('8');
    await page.getByLabel('Slide-/X/Y-Senderate (1–30/s)',{exact:true}).first().fill('12');
    await page.getByLabel('X/Y-Werte zusätzlich per MQTT senden (0–100)',{exact:true}).first().check();
    await page.getByLabel('X-Topic',{exact:true}).first().fill('t650-touchpad/x');
    await page.getByLabel('Y-Topic',{exact:true}).first().fill('t650-touchpad/y');
    await page.screenshot({path:'.state/devices-029-desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'device page fits mobile');
    await page.screenshot({path:'.state/devices-029-mobile.png',fullPage:true});
    assert.deepEqual(errors,[]);console.log('Chromium local UI: device/key accordions, step select, reassignment, removal and mobile width OK');
  }finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
