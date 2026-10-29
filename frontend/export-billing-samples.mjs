import {writeFile} from 'node:fs/promises'
import {invoiceHtml} from './src/native/invoiceDocument.js'
globalThis.location={origin:'http://127.0.0.1:5206'}
const store=new Map();globalThis.sessionStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)}
const {loadWorkbook,selectPreviewRole,previewRequest}=await import('./src/preview/adapter.js')
loadWorkbook();selectPreviewRole('Admin')
const billing=await previewRequest('commercial','summary')
await writeFile('D:/Preview/SISU_Invoice_Sample.html',invoiceHtml(billing.invoices.find(i=>i.status==='Unpaid')))
await writeFile('D:/Preview/SISU_Receipt_Sample.html',invoiceHtml(billing.invoices.find(i=>i.status==='Paid'),'receipt'))
console.log(JSON.stringify({institute:billing.accounts[0].display_name,units:billing.accounts[0].estimate.units,total:billing.accounts[0].estimate.total_minor/100,files:2}))
