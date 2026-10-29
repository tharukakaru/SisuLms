import unittest
from institute_lms.provider_card_rules import valid_charge
class ProviderCardBindings(unittest.TestCase):
    def test_card_reference_amount_currency_and_mode_are_bound(self):
        b={'name':'INV1','total_minor':1510000,'gateway_card_id':'card_'+24*'x'}
        p={'id':'pay_'+24*'a','object':'payment','reference':'INV1','amountCents':1510000,'currency':'LKR','mode':'test','savedCardId':b['gateway_card_id']}
        self.assertTrue(valid_charge(p,b,'test'))
        for key,value in [('reference','OTHER'),('amountCents',1510001),('currency','USD'),('mode','live'),('savedCardId','card_wrong'),('object','checkout'),('id','pay_invalid')]:
            self.assertFalse(valid_charge({**p,key:value},b,'test'),key)
        self.assertFalse(valid_charge({**p,'amountCents':True},b,'test'))
    def test_checkout_binding_does_not_accept_saved_card_alone(self):
        b={'name':'INV1','total_minor':10000,'gateway_checkout_id':'chk_'+24*'b'}
        p={'id':'pay_'+24*'a','object':'payment','reference':'INV1','amountCents':10000,'currency':'LKR','mode':'test','checkoutId':b['gateway_checkout_id']}
        self.assertTrue(valid_charge(p,b,'test'));self.assertFalse(valid_charge({**p,'checkoutId':None},b,'test'))
