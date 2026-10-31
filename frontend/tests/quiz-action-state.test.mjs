import test from 'node:test'
import assert from 'node:assert/strict'
import {quizActionState} from '../src/native/quizActionState.js'

const teacher={classroom:'room-1',role:'Teacher',permission:true}
test('authorized teacher has an enabled action with zero quizzes in every filter',()=>{
  for(const filter of ['All','Manual','Quizzes']){
    const action=quizActionState({...teacher,filter,items:[],readiness:{status:'ready',can_manage:true}})
    assert.equal(action.visible,true);assert.equal(action.disabled,false)
  }
})
test('missing quiz schema preserves the action with setup explanation',()=>{
  const action=quizActionState({...teacher,readiness:{status:'setup',can_manage:true}})
  assert.equal(action.visible,true);assert.equal(action.disabled,true)
  assert.match(action.message,/Quiz setup required/);assert.match(action.message,/IL Classroom Quiz Submission/)
  assert.equal(action.retry,true)
})
test('metadata failure and loading never silently hide a manager action',()=>{
  for(const status of ['loading','error']){
    const action=quizActionState({...teacher,readiness:{status,can_manage:null,error:'Network unavailable'}})
    assert.equal(action.visible,true);assert.equal(action.disabled,true);assert.ok(action.message)
    assert.equal(action.retry,status==='error')
  }
})
test('students and known nonmanagers receive no action; denial cannot enable it',()=>{
  assert.equal(quizActionState({...teacher,role:'Student',readiness:{status:'ready',can_manage:false}}).visible,false)
  assert.equal(quizActionState({...teacher,permission:false,readiness:{status:'ready',can_manage:false}}).visible,false)
  assert.equal(quizActionState({...teacher,readiness:{status:'ready',can_manage:false}}).disabled,true)
})
