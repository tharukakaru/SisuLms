import test from 'node:test'
import assert from 'node:assert/strict'
import {emptyQuestion,quizErrors,hasQuizErrors,completeAnswers} from '../src/native/classroomQuizRules.js'
const question=()=>({prompt:'Question',options:['A','B','C','D'],answer:0})
test('publish validates title and inclusive 1–50 question bounds',()=>{
  for(const n of [1,50])assert.equal(hasQuizErrors(quizErrors({title:'Quiz',questions:Array.from({length:n},question)})),false)
  for(const n of [0,51])assert.equal(hasQuizErrors(quizErrors({title:'Quiz',questions:Array.from({length:n},question)})),true)
  assert.ok(quizErrors({title:' ',questions:[question()]}).title)
})
test('editor requires four nonempty options and one integer key',()=>{
  for(const options of [[],['A','B','C'],['A','B','C','D','E'],['A','B','C',' ']])assert.ok(quizErrors({title:'Quiz',questions:[{...question(),options}]}).questions[0].options)
  for(const answer of [null,true,'0',[0,1],-1,4])assert.ok(quizErrors({title:'Quiz',questions:[{...question(),answer}]}).questions[0].answer)
})
test('validation retains entered values and questions do not share options',()=>{
  const draft={title:'',questions:[emptyQuestion()]};const before=JSON.stringify(draft)
  quizErrors(draft);assert.equal(JSON.stringify(draft),before)
  const other=emptyQuestion();draft.questions[0].options[0]='value';assert.equal(other.options[0],'')
})
test('review requires every single-select answer',()=>{
  assert.equal(completeAnswers([question(),question()],[0,3]),true)
  for(const answers of [[0],[0,null],[0,true],[0,4]])assert.equal(completeAnswers([question(),question()],answers),false)
})
