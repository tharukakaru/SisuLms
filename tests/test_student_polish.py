from types import SimpleNamespace as NS
from unittest import TestCase
from unittest.mock import Mock, patch
from test_upload_provisioning import function


class StudentPolish(TestCase):
    def test_news_checks_selected_membership_and_filters_providers(self):
        db = Mock()
        context = NS(enabled=lambda: True, SESSION_KEY='selected', current_institute=Mock(return_value=NS(name='I1')))
        fn = function('profiles', 'followed_updates', {'signed_in':Mock(), 'frappe':NS(db=db, session=NS(user='student', data={'selected':'I1'}))})
        with patch.dict('sys.modules', {'institute_lms.campus_context':context, 'frappe.utils':NS(now_datetime=lambda:'now')}):
            fn(2)
            sql, args = db.sql.call_args.args
            self.assertEqual(args, ('now','student','I1','I1',50))
            context.current_institute.assert_called_once()
            for part in ("p.workspace=%s", "m.institute=%s", "m.active=1", "r.user=%s", "r.status='Active'"):
                self.assertIn(part,sql)
            context.current_institute.side_effect = PermissionError('revoked')
            db.sql.reset_mock()
            with self.assertRaises(PermissionError): fn()
            db.sql.assert_not_called()

    def test_general_news_keeps_current_user_follows(self):
        db=Mock()
        fn=function('profiles','followed_updates',{'signed_in':Mock(),'frappe':NS(db=db,session=NS(user='student',data={}))})
        with patch.dict('sys.modules',{'institute_lms.campus_context':NS(enabled=lambda:True,SESSION_KEY='selected',current_institute=Mock()),'frappe.utils':NS(now_datetime=lambda:'now')}):fn()
        self.assertEqual(db.sql.call_args.args[1],('now','student',0))
        self.assertNotIn('m.institute',db.sql.call_args.args[0])

    def test_erasure_request_belongs_to_current_user_and_deduplicates(self):
        db=Mock();db.get_value.return_value=None
        doc=Mock(name='request');doc.name='request-1'
        f=NS(db=db,session=NS(user='self'),get_doc=Mock(return_value=doc))
        def fail(message):raise ValueError(message)
        f.throw=fail
        fn=function('accounts','public_deletion_request',{'frappe':f,'payload':lambda x:NS(**x)})
        data={'kind':'delete_profile','confirmation':'CONFIRM','reason':' Please remove my account ','target':'someone-else'}
        self.assertEqual(fn(data),{'request':'request-1','status':'Pending'})
        self.assertEqual(f.get_doc.call_args.args[0]['requested_by'],'self')
        self.assertNotIn('target',f.get_doc.call_args.args[0])
        db.get_value.return_value='request-1'
        fn(data)
        self.assertEqual(doc.insert.call_count,1)
        data['confirmation']='confirm'
        with self.assertRaises(ValueError):fn(data)
        self.assertEqual(doc.insert.call_count,1)
