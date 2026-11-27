import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
import {ref,computed} from 'vue'
const source=readFileSync(new URL('../src/native/PlanEditor.vue',import.meta.url),'utf8')
function harness(){
 const calls=[];const catalog={revision:2,editable_features:['news'],feature_labels:{news:'News'},plans:{Individual:{monthly_lkr:2500,description:'',card_features:['Lessons','Quizzes'],features:{news:false}}}}
 const ctx=vm.createContext({ref,computed,onMounted(){},request:async(...args)=>{calls.push(args);return {...catalog,revision:3}}})
 vm.runInContext(source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')+'\nglobalThis.ui={accept,data,move,changes,review,ready,publish,reason};',ctx)
 ctx.ui.accept(catalog);return {ui:ctx.ui,calls}
}
test('card feature additions, removal and ordering do not alter access',()=>{
 const {ui}=harness();const p=ui.data.value.plans.Individual
 p.card_features.push('Support');ui.move(p.card_features,2,-1);p.card_features.splice(0,1)
 assert.deepEqual([...p.card_features],['Support','Quizzes']);assert.equal(p.features.news,false)
 assert.equal(ui.changes.value.length,1)
})
test('publishing requires review of latest edits and preserves revision',async()=>{
 const {ui,calls}=harness();ui.data.value.plans.Individual.features.news=true
 assert.match(ui.changes.value[0],/current subscribers/)
 await ui.publish();assert.equal(calls.length,0)
 ui.review();assert.equal(ui.ready.value,true)
 ui.data.value.plans.Individual.monthly_lkr=3000;assert.equal(ui.ready.value,false)
 ui.review();ui.reason.value='Approved catalogue update';await ui.publish()
 assert.equal(calls[0][2].revision,2);assert.equal(calls[0][2].plans.Individual.monthly_lkr,3000)
 assert.equal(ui.ready.value,false)
})
