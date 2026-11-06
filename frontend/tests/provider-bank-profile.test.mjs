import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
const source=readFileSync(new URL('../src/native/InstituteBankDetails.vue',import.meta.url),'utf8')
for(const teacher of [false,true])test(`${teacher?'teacher':'institute'} profile loads and saves its own receiving account`,async()=>{
 const calls=[];let mount
 const context=vm.createContext({ref:value=>({value}),defineProps:()=>({teacher}),onMounted:fn=>mount=fn,
 request:async(...args)=>{calls.push(args);return {instructions:'Existing bank account'}}})
 vm.runInContext(source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')+'\nglobalThis.ui={save,instructions,saved};',context)
 await mount();assert.equal(context.ui.instructions.value,'Existing bank account')
 context.ui.instructions.value='Updated receiving account';await context.ui.save()
 assert.equal(calls[0][1],teacher?'teacher_bank_details':'institute_bank_details')
 assert.equal(calls[1][1],teacher?'save_teacher_bank_details':'save_institute_bank_details')
 assert.equal(calls[1][2].instructions,'Updated receiving account');assert.equal(context.ui.saved.value,true)
})
