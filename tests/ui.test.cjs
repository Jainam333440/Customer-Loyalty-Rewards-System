const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
test('Reset reward editor clears the hidden ID before creating another reward',()=>{
  const nodes={};
  const get=s=>nodes[s]??=(s==='#reward-form'?{elements:{reward_id:{value:'7'}}}:{});
  const context={document:{querySelector:get,querySelectorAll:()=>[]},fetch:()=>new Promise(()=>{}),console};
  vm.createContext(context);vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
  vm.runInContext('bind()',context);
  get('#reset-reward').onclick();
  assert.equal(get('#reward-form').elements.reward_id.value,'');
  assert.equal(get('#reward-title').textContent,'Add a reward');
});
test('Untrusted display text is HTML escaped',()=>{
  const context={document:{querySelector:()=>({})},fetch:()=>new Promise(()=>{})};
  vm.createContext(context);vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
  assert.equal(vm.runInContext('esc("<img src=x onerror=alert(1)>")',context),'&lt;img src=x onerror=alert(1)&gt;');
});
