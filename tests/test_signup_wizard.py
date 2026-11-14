import unittest
from types import SimpleNamespace as NS
from contextlib import nullcontext
from unittest.mock import Mock
from institute_lms.signup_rules import password
from test_upload_provisioning import function

class SignupWizard(unittest.TestCase):
    def test_signup_accepts_eight_but_rejects_seven(self):
        password('Ab3!xyzw','Ab3!xyzw',minimum=8)
        with self.assertRaises(ValueError):password('Ab3!xyz','Ab3!xyz',minimum=8)
        with self.assertRaises(ValueError):password('Ab3!xyzw','different',minimum=8)
        with self.assertRaises(ValueError):password('x'*129,'x'*129,minimum=8)
        # The unrelated password-reset default remains unchanged.
        with self.assertRaises(ValueError):password('Ab3!xyzw','Ab3!xyzw')

    def harness(self):
        state={'email_verified':True,'phone_verified':True,'phone_last':100,'phone_digest':'old','details':{'phone':'+94761234567'}}
        def fail(message):raise ValueError(message)
        def issue(token,value,channel):
            self.assertEqual(channel,'phone');self.assertEqual(value['phone_last'],100)
            value['phone_verified']=False;value['phone_digest']='new'
        c=NS(key=lambda t:t,issue=Mock(side_effect=issue))
        f=NS(throw=fail,cache=NS(lock=lambda *a,**k:nullcontext()))
        send=function('public_signup','send_phone',{'ready':lambda:None,'frappe':f,'challenges':c,'read':lambda t:state})
        return send,state,c

    def test_changed_phone_keeps_email_but_replaces_phone_proof(self):
        send,state,c=self.harness();send('token',phone='+94771234567')
        self.assertEqual(state['details']['phone'],'+94771234567');self.assertTrue(state['email_verified']);self.assertFalse(state['phone_verified']);self.assertEqual(state['phone_digest'],'new');c.issue.assert_called_once()

    def test_invalid_phone_or_unverified_email_cannot_send(self):
        for number in ('0771234567','+94\n1234567','+123',None):
            send,state,c=self.harness()
            if number is None:state['email_verified']=False
            with self.assertRaises(ValueError):send('token',phone=number)
            c.issue.assert_not_called()

    def test_legacy_phone_request_uses_existing_number(self):
        send,state,c=self.harness();send('token');self.assertEqual(state['details']['phone'],'+94761234567');c.issue.assert_called_once()
