import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
import {ref,computed} from 'vue'
const source=readFileSync(new URL('../src/native/ControlPlane.vue',import.meta.url),'utf8')
function harness(fail=false){
 const calls=[]
 const context=vm.createContext({ref,computed,nextTick:async()=>{},onMounted(){},document:{getElementById:()=>null},object:v=>v||{},
 request:async(module,method,args)=>{calls.push({module,method,args});if(method==='register'&&fail)throw Error('Duplicate institute code');if(method==='control_room')return {organizations:[]};if(method==='admin_get')return {plans:Object.fromEntries(['Individual','Silver','Gold','Platinum'].map(p=>[p,{monthly_lkr:2500}]))};if(method==='summary')return {offer:{amount_minor:20000,available:true},receipts:[]};return {}}})
 vm.runInContext(source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')+'\nglobalThis.ui={action,form,error,choose,monthlyLkr,monthlyPrice,saveOffer,tenant,reason,state,selectedCommercialPlan,saveCommercialPlan,commercialPlanNames};',context)
 return {ui:context.ui,calls}
}
test('successful registration resets all fields and reloads organizations',async()=>{
 const {ui,calls}=harness();ui.form.value={title:'Test',code:'ABC',site_hostname:'abc.example.com',admin_contact:'test@example.com',plan:'Individual'}
 await ui.action('register',ui.form.value)
 assert.equal(ui.form.value.title,'');assert.equal(ui.form.value.code,'');assert.equal(ui.form.value.site_hostname,'');assert.equal(ui.form.value.admin_contact,'');assert.equal(ui.form.value.plan,'Individual')
 assert.equal(calls[0].args.title,'Test');assert.equal(calls[1].method,'control_room')
})
test('failed registration retains entered fields for correction',async()=>{
 const {ui}=harness(true);ui.form.value.title='Keep this';await ui.action('register',ui.form.value)
 assert.equal(ui.form.value.title,'Keep this');assert.equal(ui.error.value,'Duplicate institute code')
})
test('manage clears stale action state and uses LKR while sending exact minor units',async()=>{
 const {ui,calls}=harness();ui.reason.value='old institute reason';ui.state.value='cancelled'
 await ui.choose({name:'org-test',subscription:{overrides:{}}})
 assert.equal(ui.reason.value,'');assert.equal(ui.state.value,'');assert.equal(ui.monthlyLkr.value,200)
 ui.monthlyLkr.value=1250.50;ui.reason.value='Requested monthly offer';await ui.saveOffer()
 const saved=calls.find(c=>c.method==='configure_offer');assert.equal(saved.args.amount_minor,125050);assert.equal(saved.args.tenant,'org-test')
})

test('live commercial plan selection is preserved and does not call payment activation',async()=>{
 const {ui,calls}=harness();await ui.choose({name:'org-live',plan:'Silver',subscription:{overrides:{}}})
 assert.equal(ui.selectedCommercialPlan.value,'Silver');ui.selectedCommercialPlan.value='Gold';ui.reason.value='Change selected package for review'
 await ui.saveCommercialPlan();const saved=calls.find(c=>c.method==='update_commercial_plan')
 assert.equal(saved.args.plan,'Gold');assert.equal(saved.args.tenant,'org-live');assert.equal(ui.commercialPlanNames.value.length,4)
 assert.equal(calls.some(c=>['reactivate','settle','checkout'].includes(c.method)),false)
})
