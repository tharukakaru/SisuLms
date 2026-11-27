// Frappe's timezone-free timestamps are stored in the campus timezone.
export function notificationTime(value) {
  if (typeof value !== 'string' || !value.trim()) return 'Time unavailable'
  let normalized = value.trim().replace(' ', 'T')
  normalized = normalized.replace(/(\.\d{3})\d+/, '$1')
  if (!/(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized)) normalized += '+05:30'
  const date = new Date(normalized)
  if (!Number.isFinite(date.getTime())) return 'Time unavailable'
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Colombo', day: 'numeric', month: 'short', year: 'numeric',
    hour: 'numeric', minute: '2-digit', hour12: true,
  }).format(date) + ' · Sri Lanka time'
}
