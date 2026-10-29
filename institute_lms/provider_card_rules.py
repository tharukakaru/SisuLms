"""Pure binding checks for SISU provider charges (not student tuition)."""
import re

def valid_charge(payment,bill,mode):
    if not isinstance(payment,dict):return False
    binding=(payment.get('checkoutId')==bill.get('gateway_checkout_id')) if bill.get('gateway_checkout_id') else (payment.get('savedCardId')==bill.get('gateway_card_id') and bool(bill.get('gateway_card_id')))
    return bool(binding and payment.get('object')=='payment' and payment.get('mode')==mode
        and payment.get('currency')=='LKR' and type(payment.get('amountCents')) is int
        and payment['amountCents']==bill.get('total_minor') and payment.get('reference')==bill.get('name')
        and re.fullmatch(r'pay_[A-Za-z0-9]{24}',str(payment.get('id',''))))
