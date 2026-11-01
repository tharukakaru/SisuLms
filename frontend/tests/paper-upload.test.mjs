import test from 'node:test'
import assert from 'node:assert/strict'
import {validatePaperUpload,PAPER_MAX_BYTES} from '../src/native/paperUploadRules.js'
import {readFile,writeFile,unlink} from 'node:fs/promises'

test('paper upload requires title and nonempty file within existing 10 MB limit',()=>{
  for(const [title,file] of [['', {name:'a.pdf',size:1}],['Paper',null],['Paper',{name:'a.pdf',size:0}],['Paper',{name:'a.pdf',size:PAPER_MAX_BYTES+1}]])assert.throws(()=>validatePaperUpload(title,file))
  validatePaperUpload('Paper',{name:'a.pdf',size:PAPER_MAX_BYTES})
})
test('paper upload accepts supported document formats and rejects active content',()=>{
  for(const ext of ['pdf','doc','docx','xls','xlsx','ppt','pptx','txt','png','jpg','jpeg','webp'])validatePaperUpload('Paper',{name:'paper.'+ext,size:100})
  for(const ext of ['html','svg','exe','docm','xlsm','pptm'])assert.throws(()=>validatePaperUpload('Paper',{name:'paper.'+ext,size:100}))
})

test('upload sends private service payload, reports progress and preserves retry identity',async()=>{
  const output=new URL('../src/native/.paper-upload-test.mjs',import.meta.url)
  const source=(await readFile(new URL('../src/native/paperUpload.js',import.meta.url),'utf8'))
    .replace("import {csrf,decode,request} from './client.js'","const csrf=()=> 'csrf-test'; const request=async()=>({storage:{remaining:10000}}); const decode=async r=>(await r.json()).message")
  await writeFile(output,source)
  const old=globalThis.XMLHttpRequest;const sent=[]
  globalThis.XMLHttpRequest=class {
    upload={};headers={};status=200;responseText=JSON.stringify({message:{name:'paper-upload-test',uploaded:true}})
    open(method,url){this.method=method;this.url=url}
    setRequestHeader(k,v){this.headers[k]=v}
    getResponseHeader(){return 'application/json'}
    send(body){sent.push({body,headers:this.headers,url:this.url});this.upload.onprogress({lengthComputable:true,loaded:5,total:10});this.onload()}
  }
  try{
    const {uploadPaperDocument}=await import(output.href)
    const progress=[];const args={classroom:'room-A',title:'Paper',description:'Instructions',file:new File(['%PDF-1.7'],'paper.pdf'),requestId:'12345678-1234-1234-1234-123456789abc',onProgress:p=>progress.push(p)}
    assert.equal((await uploadPaperDocument(args)).uploaded,true)
    await uploadPaperDocument(args)
    assert.deepEqual(progress,[50,50]);assert.equal(sent[0].body.get('classroom'),'room-A')
    assert.equal(sent[0].body.get('request_id'),sent[1].body.get('request_id'))
    assert.equal(sent[0].headers['X-Frappe-CSRF-Token'],'csrf-test')
    assert.equal(sent[0].url,'/api/method/institute_lms.materials.upload_paper')
  }finally{globalThis.XMLHttpRequest=old;await unlink(output)}
})

test('missing tenant provisioning fails preflight without sending file or guessing tenant',async()=>{
  const output=new URL('../src/native/.paper-provisioning-test.mjs',import.meta.url)
  const source=(await readFile(new URL('../src/native/paperUpload.js',import.meta.url),'utf8'))
    .replace("import {csrf,decode,request} from './client.js'",`const csrf=()=>'';const decode=()=>{};
      const request=async(module,method)=>{
        if(module!=='release'||method!=='workspace')throw Error('Unexpected context');
        throw Error('SaaS tenant must be provisioned before use');
      }`)
  await writeFile(output,source)
  const old=globalThis.XMLHttpRequest;let uploads=0
  globalThis.XMLHttpRequest=class {constructor(){uploads++}}
  try{
    const {uploadPaperDocument}=await import(output.href)
    await assert.rejects(uploadPaperDocument({classroom:'IT',title:'Paper',description:'',file:new File(['%PDF-1.7'],'paper.pdf'),requestId:'12345678-1234-1234-1234-123456789abc',onProgress(){}}),/SaaS tenant must be provisioned before use/)
    assert.equal(uploads,0)
  }finally{globalThis.XMLHttpRequest=old;await unlink(output)}
})
