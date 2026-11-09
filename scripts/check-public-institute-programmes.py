"""Real Frappe role checks using named test users. All database writes roll back."""
import os
import secrets
from contextlib import ExitStack
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch


def main():
    import hashlib, json, tarfile
    from pathlib import Path
    app=Path('/home/sisu/frappe-bench/apps/institute_lms')
    with tarfile.open('/tmp/sisu-institute-admin-programmes.tgz') as archive:
        manifest=json.load(archive.extractfile('manifest.json'))
    for name, entry in manifest.items():
        assert hashlib.sha256((app/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==entry['after'], 'Source mismatch: '+name
    print('PASS: deployed source matches release package.')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com')
    frappe.connect()
    codes = []
    try:
        from institute_lms import (api, teaching, programme_courses, programme_learning,
            programme_certificates, classroom_quizzes, attendance_register, commercial,
            account_billing, saas, public_student)
        from institute_lms.campus_context import SESSION_KEY
        from institute_lms.membership_write import authorized_insert
        from frappe.utils import now_datetime
        inst = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO'}, 'name')
        assert inst and frappe.db.get_value('IL Institute', inst, 'title') == '[DEMO] SISU Practice Institute'
        admin = 'sisu.student.test+institute.admin@gmail.com'
        teacher = 'sisu.student.test+institute.teacher@gmail.com'
        student = 'sisu.student.test@gmail.com'
        for user in (admin, teacher, student):
            assert frappe.db.get_value('User', user, 'enabled'), 'Named test account unavailable: ' + user
        t = frappe.db.get_value('IL Member', {'user': teacher, 'institute': inst, 'role': 'Teacher', 'active': 1}, 'name')
        assert t
        modules = {m.__name__.split('.')[-1]: m for m in (api, teaching, programme_courses,
            programme_learning, programme_certificates, classroom_quizzes, attendance_register,
            commercial, public_student)}
        def login(user):
            frappe.set_user(user)
            frappe.session.data[SESSION_KEY] = inst
            frappe.session.data.csrf_token = secrets.token_hex(32)
        def call(module, method, **args):
            frappe.local.request = SimpleNamespace(path='/api/method/institute_lms.' + module + '.' + method)
            frappe.local.form_dict = frappe._dict(args)
            account_billing.guard_request(); saas.guard_request()
            return getattr(modules[module], method)(**args)
        def denied(fn):
            try: fn()
            except (frappe.ValidationError, frappe.PermissionError): return
            raise AssertionError('Expected permission/validation denial')
        with ExitStack() as stack:
            stack.enter_context(patch.object(frappe, 'sendmail', side_effect=AssertionError('No test email may be sent')))
            stack.enter_context(patch.object(frappe, 'enqueue', return_value=None))
            stack.enter_context(patch.object(frappe, 'publish_realtime', return_value=None))
            login(admin)
            s = frappe.db.get_value('IL Member', {'user': student, 'institute': inst, 'role': 'Student', 'active': 1}, 'name')
            if not s:
                member = frappe.get_doc({'doctype': 'IL Member', 'user': student, 'institute': inst,
                    'role': 'Student', 'active': 1, 'full_name': '[TEST] Programme student'})
                with authorized_insert(member): member.insert(ignore_permissions=True)
                s = member.name
            codes = [call('programme_courses', 'module_code') for _ in range(2)]
            payload = {'title': '[TEST] Rollback programme', 'description': 'Rollback-only course',
                'fee': 0, 'access_duration_days': 180, 'modules': [
                    {'module_code': code, 'title': '[TEST] Module ' + str(i + 1), 'teacher': t,
                     'duration_weeks': 2, 'assessment_weight': 90} for i, code in enumerate(codes)]}
            course = call('programme_courses', 'create', data=payload)
            denied(lambda: call('programme_courses', 'create', data=payload))
            programme = frappe.get_doc('IL Programme', course)
            rooms = [r.classroom for r in programme.modules]
            assert len(rooms) == 2 and len(set(rooms)) == 2
            assert frappe.db.count('IL Notification Event', {'event_type': 'programme.assigned', 'recipient': t,
                'classroom': ['in', rooms]}) == 2
            login(teacher)
            denied(lambda: call('programme_courses', 'create', data=payload))
            quizzes = []
            for room in rooms:
                quizzes.append(call('classroom_quizzes', 'save', data={'classroom': room,
                    'title': '[TEST] Required quiz', 'questions': [
                        {'prompt': 'Two plus two?', 'options': ['1', '2', '3', '4'], 'answer': 3}]}, publish=True)['name'])
            session = frappe.get_doc({'doctype': 'IL Session', 'institute': inst, 'classroom': rooms[0],
                'title': '[TEST] Completed session', 'starts_at': now_datetime() - timedelta(hours=2),
                'ends_at': now_datetime() - timedelta(hours=1), 'mode': 'Physical', 'status': 'Scheduled'}).insert(ignore_permissions=True)
            print('PASS: admin creates dedicated modules; assigned teacher can publish quizzes; notification events exist.')
            login(student)
            enrolled = call('teaching', 'enroll_programme', programme=course)
            assert call('teaching', 'enroll_programme', programme=course)['enrollment'] == enrolled['enrollment']
            denied(lambda: call('programme_learning', 'complete', classroom=rooms[0]))
            denied(lambda: call('api', 'accessible_room', name=rooms[1]))
            denied(lambda: call('classroom_quizzes', 'detail', name=quizzes[1]))
            denied(lambda: call('programme_certificates', 'download', programme=course))
            call('classroom_quizzes', 'submit', name=quizzes[0], answers=[3])
            state = call('programme_learning', 'complete', classroom=rooms[0])
            assert state['modules'][0]['completed'] and state['modules'][0]['grade']['provisional']
            assert state['modules'][1]['allowed']
            login(teacher)
            call('attendance_register', 'submit', session=session.name, entries=[{'student': s, 'status': 'Absent'}])
            gradebook=call('programme_learning','gradebook',classroom=rooms[0])
            assert next(row for row in gradebook['rows'] if row['student']==s)['grade']['score']==90
            login(student)
            denied(lambda: call('programme_learning','gradebook',classroom=rooms[0]))
            state = call('programme_learning', 'status', programme=course)
            assert state['modules'][0]['grade']['score'] == 90
            assert not state['modules'][0]['grade']['provisional']
            call('classroom_quizzes', 'submit', name=quizzes[1], answers=[0])
            assert call('programme_learning', 'complete', classroom=rooms[1])['completed']
            assert call('programme_learning', 'status', programme=course)['modules'][0]['allowed']
            print('PASS: required submission gate, direct-link locks, no attendance/pass prerequisite, 90/10 grades and completed-module access.')
            login(admin)
            paid_code = call('programme_courses', 'module_code'); codes.append(paid_code)
            paid = call('programme_courses', 'create', data={**payload, 'fee': 100,
                'modules': [{**payload['modules'][0], 'module_code': paid_code}]})
            paid_room = frappe.get_doc('IL Programme', paid).modules[0].classroom
            login(student)
            call('teaching', 'enroll_programme', programme=paid)
            details = call('programme_courses', 'payment_details', programme=paid)
            assert details['invoice'] and details['fee'] == 100 and details['payment_method'] == 'Bank transfer'
            assert frappe.db.count('IL Invoice', {'student': s, 'classroom': paid_room}) == 1
            denied(lambda: call('api', 'accessible_room', name=paid_room))
            login(teacher)
            # Even full classroom control must not permit institute bank-slip review.
            frappe.db.set_value('IL Classroom', paid_room, 'teacher_access', 'Full control')
            denied(lambda: commercial.reviewer(frappe._dict(classroom=paid_room, institute=inst)))
            print('PASS: one course invoice, bank details, unpaid access denied, institute payment review restricted to admin.')
    finally:
        frappe.db.rollback()
        for code in codes: frappe.cache().delete_value('programme-module:' + code)
        print('ROLLED BACK: no programme, module, grade, enrollment, invoice, notification or membership retained. No payment or message sent. Browser/slip-upload acceptance remains separate.')
        frappe.destroy()


if __name__ == '__main__': main()
