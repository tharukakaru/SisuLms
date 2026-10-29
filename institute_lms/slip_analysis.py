"""Local evidence checks only. This never approves or claims a bank transfer."""
import re
def compare_text(text,amount_minor,reference,transfer_date):
    compact=re.sub(r'[^a-z0-9]','',str(text).casefold())
    amounts=set()
    for item in re.findall(r'(?<![\d.])(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}(?!\d)',text):
        from decimal import Decimal
        amounts.add(int(Decimal(item.replace(',',''))*100))
    ref=re.sub(r'[^a-z0-9]','',str(reference).casefold())
    day=str(transfer_date)[:10];parts=day.split('-')
    dates=[day,day.replace('-','/')]
    if len(parts)==3:dates+=['/'.join(reversed(parts)),'-'.join(reversed(parts))]
    return dict(amount_match=amount_minor in amounts,reference_match=bool(ref and ref in compact),date_match=any(x in text for x in dates),has_text=bool(text.strip()))
