import test from 'node:test'
import assert from 'node:assert/strict'
import {classroomNavigation,classroomDestination} from '../src/classroomNavigation.js'
test('student navigation has classroom destinations and a user guide',()=>{
 assert.deepEqual(classroomNavigation('Student').map(x=>x.id),['dashboard','classrooms','schedule','study','connections','payments','subscription','news','profile','guide'])
})
test('teacher and institute tools remain without duplicate learning destinations',()=>{
 for(const role of ['Student','Teacher','Admin']) {
  const ids=classroomNavigation(role).map(x=>x.id)
  assert.equal(new Set(ids).size,ids.length)
  for(const removed of ['programmes','hub','liveclasses','library','lessons','purchases','pricing']) assert.ok(!ids.includes(removed))
 }
 assert.ok(classroomNavigation('Teacher').some(x=>x.id==='subscription'))
 assert.ok(classroomNavigation('Admin').some(x=>x.id==='team'))
})
test('old lesson bookmarks retain their classroom intent',()=>{
 assert.deepEqual(classroomDestination('programmes'),{group:'Programmes',tab:'Overview'})
 assert.equal(classroomDestination('liveclasses').tab,'Sessions')
 assert.equal(classroomDestination('purchases').tab,'Recordings')
 assert.equal(classroomDestination('papers').tab,'Papers & assignments')
 assert.equal(classroomDestination('study'),null)
})
