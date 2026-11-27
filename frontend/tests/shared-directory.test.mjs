import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
const source=fs.readFileSync(new URL('../src/commerce/Connections.vue',import.meta.url),'utf8')
const handlers=source.slice(source.indexOf('const directoryLoading='),source.indexOf('\nlet viewRequest='))
function harness(){
 const pending=[],timers=new Map();let id=0
 const c={ref:value=>({value}),isDemo:false,db:{value:{profiles:[],pending:[]}},owner:{value:false},query:{value:''},directoryPage:{value:0},directoryKind:{value:'All'},onUnmounted:fn=>{c.dispose=fn},community:()=>({profiles:[]}),clearTimeout:n=>timers.delete(n),setTimeout:fn=>{timers.set(++id,fn);return id},call:()=>new Promise((resolve,reject)=>pending.push({resolve,reject}))}
 vm.createContext(c);vm.runInContext(handlers+'\nglobalThis.state={directoryLoading,directoryError}',c)
 return {c,pending,timers}
}
test('latest directory search wins when requests finish out of order',async()=>{
 const {c,pending}=harness();const first=c.load(),second=c.load();pending[1].resolve([{name:'new'}]);await second;pending[0].resolve([{name:'old'}]);await first
 assert.equal(c.db.value.profiles[0].name,'new');assert.equal(c.state.directoryLoading.value,false)
})
test('stale errors do not replace the latest successful directory results',async()=>{
 const {c,pending}=harness();const first=c.load(),second=c.load();pending[1].resolve([{name:'new'}]);await second;pending[0].reject(new Error('old error'));await first
 assert.equal(c.state.directoryError.value,'');assert.equal(c.db.value.profiles[0].name,'new')
})
test('rapid typing is debounced and cancels obsolete search timers',()=>{
 const {c,timers,pending}=harness();c.directoryPage.value=3;c.searchDirectory();c.searchDirectory();c.searchDirectory()
 assert.equal(timers.size,1);assert.equal(c.directoryPage.value,0);assert.equal(pending.length,0)
 ;[...timers.values()][0]();assert.equal(pending.length,1)
 c.dispose();assert.equal(timers.size,0)
})
test('current errors end loading and allow a clean retry',async()=>{
 const {c,pending}=harness();let work=c.load();pending[0].reject(new Error('Offline'));await work
 assert.equal(c.state.directoryError.value,'Offline');assert.equal(c.state.directoryLoading.value,false)
 work=c.load();pending[1].resolve([{name:'recovered'}]);await work
 assert.equal(c.state.directoryError.value,'');assert.equal(c.db.value.profiles[0].name,'recovered')
})
