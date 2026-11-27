export function trialCountdown(remainingMs) {
  const remaining = Number.isFinite(remainingMs) ? Math.max(0, remainingMs) : 0
  const minutes = Math.ceil(remaining / 60000)
  return {
    days: Math.floor(minutes / 1440),
    hours: Math.floor(minutes % 1440 / 60),
    minutes: minutes % 60,
    urgent: remaining <= 86400000,
    expired: remaining === 0,
  }
}
