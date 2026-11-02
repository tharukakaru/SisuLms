from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import MagicMock,patch
from test_upload_provisioning import function


class Row(dict):
    __getattr__=dict.get


class CommercialFreeAccess(TestCase):
    def setUp(self):
        self.room=Row(name='room',fee_mode='Free',fee=0,active=1)
        self.member=NS(role='Student',name='student')
        self.enrollment=NS(active=1,access_override='Automatic')
        self.f=NS(db=MagicMock(),get_doc=MagicMock(return_value=self.enrollment))
        self.f.db.get_value.return_value=self.enrollment
        self.lock=MagicMock(return_value='')
        self.paid=MagicMock(return_value=False)
        self.retention=MagicMock(return_value=True)
        p=patch.dict('sys.modules',{'institute_lms.commercial':NS(account_for=lambda *a:NS(plan='Gold'),
            locked_reason=self.lock,plan_features=lambda plan:{'lms':True},access_granted=self.paid),
            'institute_lms.retention':NS(access_allowed=self.retention)})
        p.start();self.addCleanup(p.stop)
        self.access=function('api','access',{'frappe':self.f,'money':float})

    def test_free_enrollment_needs_no_paid_access_record(self):
        self.assertTrue(self.access(self.room,self.member)['allowed'])
        self.paid.assert_not_called()

    def test_paid_class_stays_locked_without_paid_period(self):
        self.room.update(fee_mode='Paid',fee=1000)
        self.assertFalse(self.access(self.room,self.member)['allowed'])
        self.paid.assert_called_once()

    def test_inconsistent_free_label_does_not_unlock_nonzero_fee(self):
        self.room['fee']=1000
        self.assertFalse(self.access(self.room,self.member)['allowed'])

    def test_closed_or_inactive_enrollment_stays_locked(self):
        for active,override in [(0,'Automatic'),(1,'Closed')]:
            self.enrollment.active=active;self.enrollment.access_override=override
            self.assertFalse(self.access(self.room,self.member)['allowed'])

    def test_expired_or_archived_free_class_stays_locked(self):
        self.retention.return_value=False
        self.assertFalse(self.access(self.room,self.member)['allowed'])

    def test_provider_subscription_requirement_preserved(self):
        self.lock.return_value='Provider subscription needs payment'
        self.assertFalse(self.access(self.room,self.member)['allowed'])
