import {readFileSync} from 'node:fs'
import test from 'node:test'
import assert from 'node:assert/strict'

const source=readFileSync(new URL('../src/App.vue',import.meta.url),'utf8')
test('internal classroom action precedes the original and requires active Admin membership',()=>{
  assert.match(source,/internalAdmin=computed\(\(\)=>admin.value && !!boot.value\?\.member.name && !!boot.value\?\.member.active\)/)
  assert.match(source,/@click="createClassroom2"[^]*?Create classroom2[^]*?<\/button><button v-if="manager" class="button primary" @click="edit\('classroom'\)"/)
  assert.match(source,/function createClassroom2\(\)\{edit\('classroom'\);internalCreation.value=true\}/)
})
test('shared form hides public controls and uses the separate internal endpoint',()=>{
  assert.match(source,/internalCreation.value\?'create_internal_classroom':methods\[modal.value\]/)
  assert.match(source,/<label v-if="!internalCreation">Provider<select/)
  assert.match(source,/<label v-if="!internalCreation">Public timetable/)
  assert.match(source,/<label v-if="!internalCreation" class="checkbox-label"><input v-model="form.published"/)
  assert.match(source,/Create an internal institute classroom\. Public provider publishing is configured separately\./)
})
