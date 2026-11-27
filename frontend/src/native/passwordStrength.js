export function passwordStrength(value = '') {
  const length = Array.from(value).length
  if (!length) return { score: 0, label: 'Not entered' }
  if (length < 8) return { score: 1, label: 'Too short' }
  const common = /^(password|123456|qwerty|letmein|welcome|admin)/i.test(value)
  if (common || new Set(value.toLowerCase()).size < 4) return { score: 1, label: 'Weak' }
  const variety = [/[a-z]/, /[A-Z]/, /[0-9]/, /[^a-zA-Z0-9]/].filter(rule => rule.test(value)).length
  const score = Math.min(4, 1 + Number(length >= 12) + Number(length >= 16) + Number(variety >= 3))
  return { score, label: ['', 'Weak', 'Fair', 'Good', 'Strong'][score] }
}
