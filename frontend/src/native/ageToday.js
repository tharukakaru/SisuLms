// Calendar dates stay in local time; never parse a birthday as a UTC timestamp.
export function ageToday(value, today = new Date()) {
  if (!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value || '')) return null
  const [year, month, day] = value.split('-').map(Number)
  const birthday = new Date(0)
  birthday.setFullYear(year, month - 1, day)
  birthday.setHours(0, 0, 0, 0)
  if (year < 1 || birthday.getFullYear() !== year || birthday.getMonth() !== month - 1 || birthday.getDate() !== day) return null
  let age = today.getFullYear() - year
  if (today.getMonth() < month - 1 || (today.getMonth() === month - 1 && today.getDate() < day)) age--
  return age < 0 ? null : age
}
