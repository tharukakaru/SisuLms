export const localDate = (date=new Date()) => `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`
export function monthWindow(month=localDate().slice(0,7)) {
  if(!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) throw Error('Choose a valid month.')
  const [year,m]=month.split('-').map(Number)
  return {start_date:month+'-01',end_date:localDate(new Date(year,m,0))}
}
export function validWindow(start,end){return /^\d{4}-\d{2}-\d{2}$/.test(start||'')&&/^\d{4}-\d{2}-\d{2}$/.test(end||'')&&start<=end}
