import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {dailyAffirmationIndex} from '../src/study/dailyAffirmation.js'
const thoughts=JSON.parse(readFileSync(new URL('../src/study/affirmations.json',import.meta.url)))
test('365 distinct, nonempty daily learning affirmations',()=>{
  assert.equal(thoughts.length,365)
  assert.equal(new Set(thoughts).size,365)
  assert.ok(thoughts.every(s=>typeof s==='string'&&s.trim().length>0))
})
test('each date in a normal year selects a different thought',()=>{
  const indices=Array.from({length:365},(_,i)=>dailyAffirmationIndex(new Date(Date.UTC(2026,0,i+1,6))))
  assert.deepEqual(indices,Array.from({length:365},(_,i)=>i))
})
test('calendar year resets at Sri Lankan midnight',()=>{
  assert.equal(dailyAffirmationIndex(new Date('2026-12-31T18:29:59Z')),364)
  assert.equal(dailyAffirmationIndex(new Date('2026-12-31T18:30:00Z')),0)
})
test('leap day shares February 28 without shifting later dates',()=>{
  assert.equal(dailyAffirmationIndex(new Date('2028-02-28T12:00:00Z')),58)
  assert.equal(dailyAffirmationIndex(new Date('2028-02-29T12:00:00Z')),58)
  assert.equal(dailyAffirmationIndex(new Date('2028-03-01T12:00:00Z')),59)
  assert.equal(dailyAffirmationIndex(new Date('2028-12-31T12:00:00Z')),364)
})
