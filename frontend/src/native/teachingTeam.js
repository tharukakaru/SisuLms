// One person per institute, with their invitation history on the membership card.
export function teachingTeam(memberships = [], invitations = []) {
  const people = new Map()
  const key = value => String(value || '').trim().toLowerCase()
  for (const membership of memberships) {
    people.set(key(membership.user || membership.profile), {...membership, invitations: []})
  }
  for (const invitation of [...invitations].sort((a, b) => String(b.creation).localeCompare(String(a.creation)))) {
    const email = key(invitation.invite_email)
    let person = people.get(email)
    if (!person) {
      person = {name: 'invitation:' + email, user: invitation.invite_email, invitations: [],
        status: invitation.expired ? 'Expired' : ({Pending:'Invited', Declined:'Rejected', Accepted:'Disconnected'})[invitation.status] || invitation.status}
      people.set(email, person)
    }
    person.invitations.push(invitation)
  }
  return [...people.values()]
}

export function invitationResponseLabel(invitation) {
  if (invitation.status === 'Declined') return 'Rejected on'
  if (invitation.status === 'Cancelled') return 'Cancelled on'
  if (invitation.status === 'Accepted') return invitation.connected ? 'Connected on' : 'Accepted on'
  return 'Respond by'
}
