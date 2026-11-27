import test from 'node:test'
import assert from 'node:assert/strict'
import {notificationTime} from '../src/shared/notificationTime.js'

test('database microseconds display as a readable Sri Lanka date and time',()=>{
  assert.equal(notificationTime('2026-11-15 00:04:07.069673'),'15 Nov 2026, 12:04 am · Sri Lanka time')
})
test('explicit UTC and offset timestamps represent the same instant',()=>{
  const local=notificationTime('2026-11-15 18:30:00')
  assert.equal(notificationTime('2026-11-15T13:00:00Z'),local)
  assert.equal(notificationTime('2026-11-15T18:30:00.123456+05:30'),local)
  assert.equal(notificationTime('2026-11-15T13:00:00.123Z'),local)
})
test('missing and malformed timestamps never leak raw values',()=>{
  for(const value of [null,undefined,'','bad-time']) assert.equal(notificationTime(value),'Time unavailable')
})
