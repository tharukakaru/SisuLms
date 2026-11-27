// Only the browser UI library is used. Session creation/authentication stays in Python.
let loading, loadedKey
export function libraryMetadata(session, mode="sandbox") {
  // Backend verifies the session signature; enforce its script origin and SRI too.
  const segment=String(session).split('.')[1]
  const claims=JSON.parse(atob(segment.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(segment.length/4)*4,'=')))
  const entries=(claims.ctx||[]).map(c=>c?.data).filter(d=>d?.clientLibrary)
  if(entries.length!==1)throw Error('Checkout library metadata unavailable.')
  const {clientLibrary,clientLibraryIntegrity}=entries[0]
  const url=new URL(clientLibrary)
  const trustedHosts=mode==='live'?['https://up.cybersource.com','https://api.cybersource.com']:mode==='sandbox'?['https://testup.cybersource.com','https://apitest.cybersource.com']:[]
  if(!trustedHosts.includes(url.origin)||url.username||url.password||url.search||url.hash||!/^\/uc\/v1\/assets\/[A-Za-z0-9_-]+\/UnifiedCheckout\.js$/.test(url.pathname)||!/^sha(256|384|512)-[A-Za-z0-9+/]+={0,2}$/.test(clientLibraryIntegrity||''))throw Error('Checkout library metadata rejected.')
  return {url:url.href,integrity:clientLibraryIntegrity}
}
export function loadCheckoutLibrary(session, mode="sandbox", timeoutMs=20000) {
  const {url,integrity}=libraryMetadata(session, mode)
  // Session-specific asset URLs may change while the signed SDK bytes do not.
  // Validate every URL above, then reuse only the same SRI-verified version in
  // the same environment. Never replace a running SDK with a different version.
  const key=mode+' '+integrity
  if(loadedKey&&loadedKey!==key){
    const error=Error('The secure checkout library was updated. Reload this page, then open your checkout again.')
    error.code='CHECKOUT_RELOAD_REQUIRED'
    throw error
  }
  loadedKey=key
  if (!loading) loading = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    let settled=false
    const fail=message=>{if(settled)return;settled=true;clearTimeout(timer);script.onload=null;script.onerror=null;script.remove();loading=null;loadedKey=null;reject(Error(message))}
    const timer=setTimeout(()=>fail('Secure checkout is taking longer than expected. Retry loading in this tab.'),timeoutMs)
    script.src = url
    script.integrity=integrity
    script.crossOrigin='anonymous'
    script.onload = () => { if(settled)return; if (window.VAS?.UnifiedCheckout) {settled=true;clearTimeout(timer);resolve(window.VAS)} else fail('Checkout library unavailable.') }
    script.onerror = () => fail('Unable to load secure checkout.')
    document.head.appendChild(script)
  })
  return loading
}
export function paymentMessage(value, kind, now = Date.now()) {
  if (value?.session_unavailable) return 'Secure checkout could not connect. No payment was submitted. Choose Retry opening checkout.'
  if (value?.session_rejected) return 'Secure checkout could not be opened. No payment session was created. Contact SISU support.'
  if (value?.status === 'cancelled' && value?.retry_allowed) return 'Checkout closed without a recorded payment. You can open a new checkout safely.'
  if (kind === 'gateway_test') {
    if (value?.status === 'succeeded') return 'LKR 50 gateway test payment verified successfully. This transaction does not pay any subscription invoice or activate subscription access.'
    if (value?.status === 'failed') return 'LKR 50 gateway test payment declined. No subscription invoice was paid.'
    if (value?.status === 'review') return 'The LKR 50 gateway test needs review. Do not attempt another payment. Contact SISU support.'
    if (value?.browser_event === 'cancelled') return 'Gateway test checkout closed. Payment status must be verified before further action. Do not pay again.'
    return value?.message || 'LKR 50 gateway test verification pending. Do not pay again.'
  }
  if (value?.status === 'succeeded') return 'Payment verified. Your invoice and access have been updated.'
  if (value?.status === 'failed') return value.message || 'Payment declined. Your paid plan was not activated.'
  if (value?.status === 'review') return 'This payment needs review. Please contact SISU before paying again.'
  if (value?.resume_allowed) return 'Payment has not been submitted. Continue to reopen your checkout.'
  if (value?.message) return value.message
  if (['processing','completed'].includes(value?.browser_event) || value?.transaction_id) return 'Payment verification pending. Check payment status before attempting another payment.'
  if (value?.retry_after) {
    const time = new Date(value.retry_after * 1000).toLocaleTimeString([], {hour:'numeric', minute:'2-digit', second:'2-digit'})
    return now < value.retry_after * 1000
      ? `An earlier checkout is reserved until ${time}. If its original window is still open, continue there. Otherwise, wait for the countdown, then check and reopen. No payment is confirmed.`
      : 'The previous checkout has expired. Choose Check and reopen checkout to verify its status before trying again.'
  }
  return 'Checkout has not been confirmed as paid. Check payment status before opening another payment.'
}

// Keep the same SDK checkout while a dialog is hidden. Never persist capture
// contexts in storage. A reload uses server recovery with a fresh submission grant.
export function reusableCheckout(client, checkout, expires, now = Date.now) {
  let revision = 0, terminal = false
  return {
    canResume: () => !terminal && now() < expires * 1000,
    async mount(target) {
      if (terminal || now() >= expires * 1000) throw Error('Checkout expired. Check payment status before reopening.')
      const current = ++revision
      try {
        const result = await checkout.mount(target)
        if (current !== revision) return {detached:true}
        terminal = true
        return {result}
      } catch (error) {
        if (current !== revision) return {detached:true}
        throw error
      }
    },
    pause() { revision++; checkout.unmount() },
    complete(token) { return checkout.complete(token) },
    destroy() { revision++; terminal = true; try { checkout.destroy() } finally { client.destroy() } },
  }
}
