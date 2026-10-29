export function receiptHtml(receipt) {
  const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
  const rows = [['Receipt',receipt.receipt_number||receipt.name],['Item',receipt.title||receipt.plan],['Amount',`${receipt.currency} ${(Number(receipt.amount_minor)/100).toFixed(2)}`],['Paid',receipt.paid_at],['Period start',receipt.period_start],['Period end',receipt.period_end],['Reference',receipt.transaction_reference],['Status',receipt.status||'Verified payment']]
  return '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>SISU payment receipt</title><style>body{font:16px system-ui;max-width:720px;margin:40px auto;padding:24px}h1{color:#6C6AEE}dt{font-weight:bold;margin-top:16px}dd{margin:4px 0;overflow-wrap:anywhere}</style></head><body><h1>SISU payment receipt</h1><p>Payment receipt — not a tax invoice.</p><dl>'+rows.filter(([,v])=>v).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')+'</dl><p>Print this document or save as PDF using your browser.</p></body></html>'
}
export function downloadHtml(html,filename) {
  const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
