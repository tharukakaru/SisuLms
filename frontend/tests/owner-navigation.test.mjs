import test from 'node:test'
import assert from 'node:assert/strict'
import {ownerSection,ownerSections,campusAdminUrl} from '../src/native/ownerNavigation.js'
const local={protocol:'http:',hostname:'127.0.0.1',port:'5401'}
test('local campus administration links stay local',()=>{
 for(const [site,port] of [['sisuacademylk.com',5400],['teen.sisuacademylk.com',5403],['staging.sisuacademylk.com',5402]])
  assert.equal(campusAdminUrl({site,url:`https://${site}/campus`},local),`http://127.0.0.1:${port}/campus`)
 assert.equal(campusAdminUrl({site:'other.example',url:'https://other.example/campus'},local),null)
})
test('hosted links remain validated HTTPS destinations',()=>{
 const hosted={protocol:'https:',hostname:'platform.sisuacademylk.com',port:''}
 assert.equal(campusAdminUrl({site:'sisuacademylk.com',url:'https://sisuacademylk.com/campus'},hosted),'https://sisuacademylk.com/campus')
 for(const url of ['javascript:alert(1)','https://other.example/campus','https://user@ sisuacademylk.com/campus'])
  assert.equal(campusAdminUrl({site:'sisuacademylk.com',url},hosted),null)
})
test('section links restore known pages and reject malformed fragments',()=>{
 assert.equal(new Set(ownerSections.map(s=>s.name)).size,ownerSections.length)
 assert.equal(ownerSection('#Student-count%20payments'),'Student-count payments')
 assert.equal(ownerSections.find(s=>s.name==='Student-count payments').managersOnly,true)
 assert.equal(ownerSection('#Profile'),'Profile')
 assert.equal(ownerSection('#Admin%20access'),'Admin access')
 assert.equal(ownerSection('#%XX'),'Overview')
 assert.equal(ownerSection('#unknown'),'Overview')
})
