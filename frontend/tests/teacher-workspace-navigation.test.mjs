import test from 'node:test'
import assert from 'node:assert/strict'
import {classroomNavigation,teacherWorkspacePage} from '../src/classroomNavigation.js'
const pages=(role,options)=>classroomNavigation(role,options).map(x=>x.id)
test('institute teacher retains teaching routes without personal business billing',()=>{
 const nav=pages('Teacher',{instituteTeacher:true})
 for(const id of ['dashboard','classrooms','schedule','connections','profile','subscription'])assert.ok(nav.includes(id))
 for(const id of ['study','wallet','workspace','payments'])assert.ok(!nav.includes(id))
})
test('independent teacher keeps own subscription and wallet; study stays student-only',()=>{
 const nav=pages('Teacher')
 assert.ok(nav.includes('subscription'));assert.ok(nav.includes('wallet'));assert.ok(!nav.includes('study'))
 assert.ok(pages('Student').includes('study'));assert.ok(pages('Admin').includes('subscription'))
})

test('institute teacher business bookmarks return to assigned teaching overview',()=>{
 for(const page of ['payments','pricing','plans','wallet','workspace']){
  assert.equal(teacherWorkspacePage(page,true),'dashboard')
  assert.equal(teacherWorkspacePage(page,false),page)
 }
 for(const page of ['classrooms','schedule','profile','news','subscription'])assert.equal(teacherWorkspacePage(page,true),page)
})
