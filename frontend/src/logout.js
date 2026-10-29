// Frappe 17 logout is POST-only. Verify the cookie session is gone before
// replacing the page, so network failures never look like successful logout.
export async function endSession(fetcher = fetch) {
  const current = await fetcher('/api/method/institute_lms.portal_session.current', {
    credentials: 'same-origin', cache: 'no-store',
  })
  if (!current.ok) throw Error('Could not check your session. Please try signing out again.')
  const identity = (await current.json()).message
  if (identity?.authenticated) {
    const response = await fetcher('/api/method/logout', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'X-Frappe-CSRF-Token': identity.csrf_token },
    })
    if (!response.ok) throw Error('Sign out failed. Please try again.')
  }
  const check = await fetcher('/api/method/institute_lms.portal_session.current', {
    credentials: 'same-origin', cache: 'no-store',
  })
  if (!check.ok || (await check.json()).message?.authenticated !== false)
    throw Error('Your session is still active. Please try signing out again.')
}

export function installSignOut() {
  let busy = false
  const channel = typeof BroadcastChannel === 'function' ? new BroadcastChannel('sisu-session') : null
  if (channel) channel.onmessage = event => {
    if (event.data === 'signed-out') window.location.replace('/campus')
  }
  window.addEventListener('pageshow', event => {
    if (event.persisted) window.location.reload()
  })
  document.addEventListener('click', async event => {
    const link = event.target.closest?.('a[href="/api/method/logout"]')
    if (!link) return
    event.preventDefault()
    if (busy) return
    busy = true
    link.setAttribute('aria-busy', 'true')
    try {
      await endSession()
      channel?.postMessage('signed-out')
      window.location.replace('/campus')
    } catch (error) {
      let notice = document.getElementById('sisu-signout-error')
      if (!notice) {
        notice = document.createElement('p')
        notice.id = 'sisu-signout-error'
        notice.setAttribute('role', 'alert')
        link.after(notice)
      }
      notice.textContent = error.message
      busy = false
      link.removeAttribute('aria-busy')
    }
  })
}
