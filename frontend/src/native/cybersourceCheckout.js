// Only the browser UI library is used. Session creation/authentication stays in Python.
export const libraryURL = 'https://apitest.cybersource.com/uc/v1/assets/1.0.0/UnifiedCheckout.js'
let loading
export function loadCheckoutLibrary() {
  if (window.VAS?.UnifiedCheckout) return Promise.resolve(window.VAS)
  if (!loading) loading = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = libraryURL
    script.onload = () => { if (window.VAS?.UnifiedCheckout) resolve(window.VAS); else { script.remove(); loading = null; reject(Error('Checkout library unavailable.')) } }
    script.onerror = () => { script.remove(); loading = null; reject(Error('Unable to load secure checkout.')) }
    document.head.appendChild(script)
  })
  return loading
}
export function paymentMessage(value) {
  if (value?.status === 'succeeded') return 'Payment verified. Your invoice and access have been updated.'
  if (value?.status === 'failed') return 'Payment declined. Your invoice remains unpaid.'
  if (value?.status === 'review') return 'This payment needs review. Please contact SISU before paying again.'
  if (value?.browser_event === 'cancelled') return 'Checkout closed. We will verify whether a payment was processed before allowing another attempt.'
  return value?.message || 'Payment verification pending. Check again in five minutes; please do not pay again.'
}
