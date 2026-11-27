import test from 'node:test'
import assert from 'node:assert/strict'
import {rememberTeacherPath,resolveTeacherPath,teacherEntryView} from '../src/native/teacherEntryPath.js'
const storage=()=>{const values=new Map();return {getItem:key=>values.get(key)??null,setItem:(key,value)=>values.set(key,value),removeItem:key=>values.delete(key)}}
const teacher={authenticated:true,user:'teacher@example.invalid',role:'Teacher',member:{role:'Teacher'}}

test('approved registration supplies a choice in a fresh browser without granting access',()=>{
  const session={authenticated:true,user:teacher.user,role:'Campus',member:null,onboarding_kind:'Teacher',shared_campus:true,teaching_path:'institute'}
  assert.equal(resolveTeacherPath(storage(),session),'institute')
  assert.equal(teacherEntryView(session,'institute'),'institute')
  assert.equal(teacherEntryView({...session,member:{role:'Teacher'}},'institute'),'')
  assert.equal(resolveTeacherPath(storage(),{...session,onboarding_kind:'Student'}),'')
})

test('teacher navigation choice survives guest sign-in and reload for the same identity',()=>{
  const tab=storage()
  rememberTeacherPath(tab,'institute',100)
  assert.equal(resolveTeacherPath(tab,{authenticated:false},110),'')
  assert.equal(resolveTeacherPath(tab,teacher,120),'institute')
  assert.equal(resolveTeacherPath(tab,teacher,130),'institute')
  assert.equal(teacherEntryView(teacher,'institute'),'')
  assert.equal(teacherEntryView(teacher,'individual'),'')
})
test('choice cannot grant another role or carry over to another signed-in account',()=>{
  for(const identity of [{...teacher,user:'other@example.invalid'},{...teacher,role:'Student'},{...teacher,role:'Admin',onboarding_kind:'Teacher'},{...teacher,control_plane:true}]){
    const tab=storage();rememberTeacherPath(tab,'institute',100);resolveTeacherPath(tab,teacher,110)
    assert.equal(resolveTeacherPath(tab,identity,120),'')
    assert.equal(resolveTeacherPath(tab,teacher,130),'')
  }
  assert.equal(teacherEntryView({...teacher,role:'Student'},'institute'),'')
  assert.equal(teacherEntryView({...teacher,control_plane:true},'institute'),'')
})
test('logout, expired choices and unavailable storage fall back to existing routing',()=>{
  const tab=storage();rememberTeacherPath(tab,'individual',100);resolveTeacherPath(tab,teacher,110)
  resolveTeacherPath(tab,{authenticated:false},120)
  assert.equal(resolveTeacherPath(tab,teacher,130),'')
  rememberTeacherPath(tab,'institute',100)
  assert.equal(resolveTeacherPath(tab,teacher,100+24*60*60*1000+1),'')
  const blocked={setItem(){throw Error('blocked')},getItem(){throw Error('blocked')}}
  assert.doesNotThrow(()=>rememberTeacherPath(blocked,'institute'))
  assert.equal(resolveTeacherPath(blocked,teacher),'')
})
test('Google completion and non-shared onboarding retain existing verification gates',()=>{
  assert.equal(teacherEntryView(teacher,'institute',true),'')
  const onboarding={authenticated:true,user:teacher.user,role:'Campus',member:null,onboarding_kind:'Teacher',shared_campus:true}
  assert.equal(teacherEntryView(onboarding,'institute'),'institute')
  assert.equal(teacherEntryView(onboarding,'individual'),'setup')
  assert.equal(teacherEntryView({...onboarding,shared_campus:false},'institute'),'')
  assert.equal(teacherEntryView({...onboarding,shared_campus:false},'individual'),'')
  assert.equal(teacherEntryView({authenticated:false},'institute'),'')
})
