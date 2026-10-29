"""Electronic provider invoices and receipts; queued only on trusted transitions."""
import json
from html import escape
import frappe
from frappe.utils import now_datetime

def document_html(bill,account,kind='invoice'):
    receipt=kind=='receipt'
    if receipt and bill.status!='Paid':raise ValueError('Payment must be confirmed before issuing a receipt')
    e=lambda v:escape(str(v or ''))
    money=lambda v:'LKR {:,.2f}'.format(int(v or 0)/100)
    from .provider_cards import safe_account
    identity=safe_account(account)
    number=(bill.receipt_number or 'RC-'+bill.name) if receipt else bill.name
    groups={}
    for row in json.loads(bill.line_snapshot or '[]'):
        key=row.get('product_key') or row.get('title');g=groups.setdefault(key,{'title':row.get('title') or key,'count':0});g['count']+=1
    rows=''.join('<tr><td>'+e(g['title'])+'</td><td>'+str(g['count'])+'</td><td>'+money(g['count']*bill.unit_minor)+'</td></tr>' for g in groups.values())
    return '''<!doctype html><html><head><meta charset="utf-8"><title>'''+e(number)+'''</title><style>
    @page{size:A4;margin:17mm}body{font:13px/1.7 Arial,sans-serif;color:#2c2435;max-width:800px;margin:30px auto;padding:30px}h1{color:#592a8d;font-size:38px;margin:0}h2{letter-spacing:2px}table{border-collapse:collapse;width:100%;margin:22px 0}td,th{padding:12px;text-align:left;border-bottom:1px solid #e5ddeb}th{background:#f5f0fa}td:last-child,th:last-child{text-align:right}.total{padding:22px;background:#f5f0fa;font-size:22px;text-align:right}.muted{color:#84758e;font-size:11px}.columns{display:flex;justify-content:space-between;gap:25px;border-top:2px solid #6b3b9e;padding-top:25px}.note{white-space:pre-line;padding:18px;background:#f8f5fb}tr{break-inside:avoid}footer{border-top:1px solid #e6ddee;margin-top:35px;padding-top:15px}
    </style></head><body><h1>sisu.</h1><p class="muted">SISU ACADEMY · MONTHLY PLATFORM BILLING</p><h2>'''+('PAYMENT RECEIPT' if receipt else 'INVOICE')+'''</h2><p>'''+e(number)+''' · '''+e(bill.status)+'''</p><div class="columns"><div><b>'''+e(identity['display_name'])+'''</b><p>'''+e(identity['lms_id'])+'''<br>'''+e(account.billing_email)+'''</p></div><div>Period: '''+e(str(bill.period_start)[:10])+''' – '''+e(str(bill.period_end)[:10])+''' (exclusive)<br>Issued: '''+e(str(bill.issued_at)[:10])+'''<br>Due: '''+e(str(bill.due_at)[:10])+'''</div></div><table><thead><tr><th>Description</th><th>Quantity</th><th>Rate</th><th>Amount</th></tr></thead><tbody><tr><td>'''+e(bill.plan)+''' monthly package</td><td>1</td><td>'''+money(bill.base_minor)+'''</td><td>'''+money(bill.base_minor)+'''</td></tr><tr><td>'''+('30-day student access periods' if bill.get('billing_policy')=='access-30-v1' else 'Active class / course enrolments')+'''</td><td>'''+str(bill.units)+'''</td><td>'''+money(bill.unit_minor)+'''</td><td>'''+money(bill.units*bill.unit_minor)+'''</td></tr></tbody></table><div class="total">'''+('Amount received' if receipt else 'Invoice total')+''' · '''+money(bill.total_minor)+'''<br><small>Balance due · '''+money(0 if bill.status=='Paid' else bill.total_minor)+'''</small></div>'''+(
        '<p>Paid '+e(bill.paid_at)+' · '+e(bill.payment_channel or 'Bank transfer')+'</p><p>Reference: '+e(bill.payment_reference)+'</p><p>Thank you. No further payment is due on this invoice.</p>' if receipt else
        '<h3>Class-by-class calculation</h3><table><thead><tr><th>Class / course</th><th>Enrolments</th><th>Fee</th></tr></thead><tbody>'+rows+'</tbody></table><p class="note">'+e(account.bank_instructions or 'Open Plans & billing in SISU to pay by card or submit bank transfer proof.')+'</p><p>Use the invoice number as your payment reference. Proof uploads remain under review until verified.</p>')+'''<footer class="muted">SISU Academy · Electronic billing document · No signature required<br>Platform fees are separate from student tuition collections.</footer></body></html>'''

def queue_document(bill,kind):
    from .commercial import save
    if kind=='receipt' and bill.receipt_queued_at:return
    account=frappe.get_doc('IL Provider Account',bill.provider_account)
    html=document_html(bill,account,kind)
    frappe.sendmail(recipients=[account.billing_email],subject='SISU '+kind+' '+bill.name,
        message=html,attachments=[{'fname':'SISU-'+kind+'-'+bill.name+'.html','fcontent':html}],delayed=True)
    if kind=='receipt':bill.receipt_queued_at=now_datetime();save(bill)
