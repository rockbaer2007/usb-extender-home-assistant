const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {webcrypto} = require('node:crypto');
const context = vm.createContext({crypto:webcrypto});
vm.runInContext(fs.readFileSync('ugso_usbhub/static/keylist.js','utf8'),context);
vm.runInContext(`
  const config={keys:[],bindings:[{device:'kbd',control:'KEY_F1'}]};
  let status={events:[]};
  learning={id:'session',device:'kbd',topic_name:'trust-keyboard'};
  status.events=[
    {learning_id:'old',sequence:1,device:'kbd',control:'KEY_A',gesture:'press'},
    {learning_id:'session',sequence:2,device:'kbd',control:'KEY_F1',gesture:'press'},
    {learning_id:'session',sequence:3,device:'kbd',control:'KEY_TAB',gesture:'press'},
    {learning_id:'session',sequence:4,device:'kbd',control:'KEY_TAB',gesture:'release'},
    {learning_id:'session',sequence:5,device:'kbd',control:'KEY_TAB',gesture:'press'},
    {learning_id:'session',sequence:6,device:'kbd',control:'KEY_VOLUMEUP',gesture:'press'}
  ];
  collectLearned(); collectLearned();
  globalThis.result=JSON.stringify(learnedDraft);
`,context);
const rows = JSON.parse(context.result);
assert.deepEqual(rows.map(k=>k.control),['KEY_TAB','KEY_VOLUMEUP']);
assert.equal(rows[0].repeat,false);
assert.equal(rows[1].repeat,true);
assert.equal(rows[1].name,'Lauter');
assert.ok(rows.every(k=>k.press&&k.release&&k.switch&&k.enabled));
assert.ok(rows.every(k=>k.press_plus&&k.release_plus));
assert.equal(rows[0].press_topic,'trust-keyboard-key-tab/press');
assert.equal(rows[0].press_plus_topic,'trust-keyboard-key-tab/press-plus');
assert.equal(rows[0].switch_mode,'toggle');
for(const mode of ['state','button','button_plus','click','double_click','hold'])assert.equal(rows[0][mode],true);
assert.equal(rows[0].button_topic,'trust-keyboard-key-tab/button');
assert.equal(rows[0].button_plus_topic,'trust-keyboard-key-tab/button-plus');
assert.equal(rows[0].double_click_topic,'trust-keyboard-key-tab/double-click');
assert.notEqual(rows[0].id,rows[1].id);
console.log('Anlernliste: Sitzungsfilter, Duplikate, Altbelegungen und Medienvorgaben erfolgreich.');
