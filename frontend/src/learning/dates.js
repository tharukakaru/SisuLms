export function localDate(date=new Date()){return [date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-')}
export function daysUntil(target,today=localDate()){
 const parse=s=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(s||''))return NaN;const [y,m,d]=s.split('-').map(Number),v=new Date(Date.UTC(y,m-1,d));return v.toISOString().slice(0,10)===s?v.getTime():NaN}
 const delta=(parse(target)-parse(today))/86400000;return Number.isFinite(delta)?delta:null
}

