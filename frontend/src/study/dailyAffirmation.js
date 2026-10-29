// Fixed calendar mapping: leap day repeats February 28 without shifting March.
export function dailyAffirmationIndex(date = new Date(), timeZone = 'Asia/Colombo') {
  const parts = new Intl.DateTimeFormat('en-US', {timeZone, month:'numeric', day:'numeric'}).formatToParts(date)
  const month = Number(parts.find(p => p.type === 'month').value)
  const day = Math.min(Number(parts.find(p => p.type === 'day').value), month === 2 ? 28 : 31)
  const starts = [0,31,59,90,120,151,181,212,243,273,304,334]
  return starts[month - 1] + day - 1
}
