import test from 'node:test'
import assert from 'node:assert/strict'
import {trialCountdown} from '../src/shared/trialCountdown.js'
test('trial countdown decomposes real remaining time and rounds up the last minute',()=>{
 assert.deepEqual(trialCountdown(14*86400000),{days:14,hours:0,minutes:0,urgent:false,expired:false})
 assert.deepEqual(trialCountdown((13*1440+23*60+8)*60000),{days:13,hours:23,minutes:8,urgent:false,expired:false})
 assert.equal(trialCountdown(1).minutes,1)
})
test('red warning starts at exactly 24 hours; expiration never becomes negative',()=>{
 assert.equal(trialCountdown(86400001).urgent,false)
 assert.equal(trialCountdown(86400000).urgent,true)
 assert.deepEqual(trialCountdown(-1),{days:0,hours:0,minutes:0,urgent:true,expired:true})
 assert.equal(trialCountdown(NaN).expired,true)
})
