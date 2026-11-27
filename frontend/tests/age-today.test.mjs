import test from 'node:test'
import assert from 'node:assert/strict'
import {ageToday} from '../src/native/ageToday.js'

test('age changes on the birthday, not at the start of the year',()=>{
  assert.equal(ageToday('2005-11-14',new Date(2026,10,13)),20)
  assert.equal(ageToday('2005-11-14',new Date(2026,10,14)),21)
  assert.equal(ageToday('2005-11-14',new Date(2026,10,15)),21)
})
test('invalid, incomplete and future birthdays have no age',()=>{
  for(const value of ['',null,'2005-02-29','2005-13-01','0000-01-01','01/02/2005','2026-11-15'])
    assert.equal(ageToday(value,new Date(2026,10,14)),null)
  assert.equal(ageToday('2026-11-14',new Date(2026,10,14)),0)
})
test('leap-day birthdays and local dates are handled without UTC conversion',()=>{
  assert.equal(ageToday('2004-02-29',new Date(2025,1,28)),20)
  assert.equal(ageToday('2004-02-29',new Date(2025,2,1)),21)
  assert.equal(ageToday('2000-12-31',new Date(2026,0,1)),25)
})
