import test from 'node:test'
import assert from 'node:assert/strict'
import {teachingTeam,invitationResponseLabel} from '../src/native/teachingTeam.js'

test('an invitation and its membership produce one teacher card',()=>{
 const member={name:'membership',user:'teacher@example.com',status:'Active',person:{display_name:'Teacher'}}
 const invite={name:'invite',invite_email:'TEACHER@example.com',status:'Accepted',connected:true,creation:'2026-11-16 12:00:00',responded_at:'2026-11-16 13:00:00'}
 const result=teachingTeam([member],[invite])
 assert.equal(result.length,1)
 assert.equal(result[0].name,'membership')
 assert.equal(result[0].status,'Active')
 assert.equal(result[0].invitations[0].responded_at,invite.responded_at)
 assert.equal(invitationResponseLabel(invite),'Connected on')
 assert.equal(member.invitations,undefined,'Source membership is not mutated')
})

test('sending creates a card before membership and rejection retains its date',()=>{
 const invite={name:'first',invite_email:'teacher@example.com',status:'Pending',creation:'2026-11-16 12:00:00'}
 assert.equal(teachingTeam([],[invite])[0].status,'Invited')
 const rejected={...invite,status:'Declined',responded_at:'2026-11-16 13:00:00'}
 const result=teachingTeam([],[rejected])
 assert.equal(result[0].status,'Rejected')
 assert.equal(invitationResponseLabel(result[0].invitations[0]),'Rejected on')
 assert.equal(result[0].invitations[0].responded_at,'2026-11-16 13:00:00')
 const newer={...invite,name:'second',creation:'2026-11-17 12:00:00'}
 const history=teachingTeam([],[rejected,newer])
 assert.equal(history.length,1)
 assert.equal(history[0].status,'Invited')
 assert.deepEqual(history[0].invitations.map(r=>r.name),['second','first'])
 assert.equal(history[0].invitations[1].responded_at,rejected.responded_at)
})

test('expired invites are history and incoming requests keep their approval actions',()=>{
 const pending={name:'request',user:'teacher@example.com',status:'Pending'}
 const invite={invite_email:pending.user,status:'Pending',expired:true}
 assert.equal(teachingTeam([],[invite])[0].status,'Expired')
 assert.equal(teachingTeam([pending],[invite])[0].status,'Pending')
})
