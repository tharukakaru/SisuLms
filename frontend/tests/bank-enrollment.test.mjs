import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import vm from 'node:vm'
const source=readFileSync(new URL('../src/native/BankPayments.vue',import.meta.url),'utf8')
function harness({intent='course-invoice',bills=[],shared=true,selectedClass=null}={}){
 const calls=[]
 const props={member:{role:'Student'},sharedCampus:shared,general:false,invoices:[],rooms:[],selectedClass}
 const context=vm.createContext({ref:value=>({value}),computed:fn=>({get value(){return fn()}}),watch(){},onMounted(){},defineExpose(){},defineProps:()=>props,defineEmits:()=>()=>{},sessionStorage:{getItem:()=>intent},
 directRequest:async(module,method,args)=>{calls.push({module,method,args});if(method==='billing')return {invoices:bills,slips:[]};if(method==='invoices')return bills;if(method==='slips')return [];return {instructions:'Shared institute account',recipient:'Institute'}}})
 vm.runInContext(source.match(/<script setup>([\s\S]*?)<\/script>/)[1].replace(/^import .*$/gm,'')+'\nglobalThis.ui={load,form,bank,invoices};',context)
 return {ui:context.ui,calls}
}
test('programme invoice loads despite empty parent list and stale class selection',async()=>{
 const h=harness({selectedClass:{name:'old-room'},bills:[{name:'old',classroom:'old-room',status:'Unpaid',amount:50},{name:'course-invoice',classroom:'module-one',programme:'course',status:'Unpaid',amount:12000}]})
 await h.ui.load();await Promise.resolve()
 assert.equal(h.ui.form.value.invoice,'course-invoice');assert.equal(h.ui.form.value.amount,12000)
 assert.equal(h.calls[0].module,'public_student');assert.equal(h.calls[0].args.invoice,'course-invoice')
 assert.equal(h.calls.at(-1).args.args.classroom,'module-one')
 assert.equal(h.ui.bank.value.instructions,'Shared institute account')
})
test('class selects its unpaid invoice with multiple balances',async()=>{
 const h=harness({intent:'',shared:false,selectedClass:{name:'target'},bills:[{name:'paid',classroom:'target',status:'Paid',amount:1},{name:'other',classroom:'other',status:'Unpaid',amount:100},{name:'target-invoice',classroom:'target',status:'Unpaid',amount:200}]})
 await h.ui.load();assert.equal(h.ui.form.value.invoice,'target-invoice');assert.equal(h.ui.form.value.amount,200)
})
test('no accessible invoice leaves payment selection empty',async()=>{
 const h=harness();await h.ui.load();assert.equal(h.ui.form.value.invoice,'');assert.equal(h.ui.form.value.amount,'');assert.equal(h.ui.bank.value,null)
})
