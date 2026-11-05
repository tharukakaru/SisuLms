"""Real service checks against labelled fixtures; all test writes roll back."""
import os
import secrets
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


def main():
    if os.name != 'posix' or Path.home() != Path('/home/sisu'):
        raise RuntimeError('Run as sisu')
    os.chdir('/home/sisu/frappe-bench/sites')
    import frappe
    frappe.init(site='sisuacademylk.com'); frappe.connect()
    try:
        from institute_lms import classroom_handover as handover, classroom_quizzes as quizzes, api, teaching, account_billing, saas
        from institute_lms.campus_context import SESSION_KEY
        from institute_lms.membership_write import authorized_insert
        inst = frappe.db.get_value('IL Institute', {'code': 'SISUDEMO'}, 'name')
        email = 'sisu.student.test+institute.teacher@gmail.com'
        room = frappe.get_doc('IL Classroom', 'fp20kd7lgd')
        assert room.institute == inst and room.title == '[TEST] Institute teacher assigned practice'
        assert room.teacher_assignment_active and room.teacher_access == 'Teaching only'
        original = room.teacher
        candidates = frappe.get_all('IL Member', filters={'institute': inst, 'role': 'Admin', 'active': 1}, pluck='user')
        admin = next((user for user in sorted(candidates) if user not in ('Guest', 'Administrator')
            and frappe.db.get_value('User', user, 'enabled')), None)
        temporary_admin = False
        if not admin:
            # This display fixture was deliberately seeded with User.enabled=0.
            # Its activation is visible only inside this uncommitted transaction.
            admin = 'sisu-public-demo-admin@example.invalid'
            assert admin in candidates, 'No eligible institute admin or named demo fixture'
            assert frappe.db.get_value('IL Institute', inst, 'title') == '[DEMO] SISU Practice Institute'
            assert frappe.db.exists('IL Public Profile', {'user': admin, 'kind': 'Institute', 'workspace': inst})
            assert frappe.db.exists('User', admin) and not frappe.db.get_value('User', admin, 'enabled')
            temporary_admin = True
        def login(user):
            frappe.set_user(user); frappe.session.data[SESSION_KEY] = inst
            frappe.session.data.csrf_token = secrets.token_hex(32)
        def call(module, method, **args):
            frappe.local.request = SimpleNamespace(path='/api/method/institute_lms.' + module + '.' + method)
            frappe.local.form_dict = frappe._dict(args)
            account_billing.guard_request(); saas.guard_request()
            return getattr({'classroom_handover': handover, 'classroom_quizzes': quizzes, 'api': api, 'teaching': teaching}[module], method)(**args)
        def denied(fn):
            try: fn()
            except (frappe.ValidationError, frappe.PermissionError): return
            raise AssertionError('Expected denial')
        with ExitStack() as stack:
            stack.enter_context(patch.object(frappe, 'sendmail', side_effect=AssertionError('Unexpected mail')))
            stack.enter_context(patch.object(frappe, 'enqueue', return_value=None))
            stack.enter_context(patch.object(frappe, 'publish_realtime', return_value=None))
            login(email)
            boot = call('api', 'bootstrap')
            assert boot['member']['institute_teacher']
            assert boot['member']['provider_profile']['kind'] == 'Teacher'
            assert not teaching.rights(room, frappe.get_doc('IL Member', original))['edit']
            assert call('classroom_quizzes', 'metadata', classroom=room.name)['can_manage']
            draft = call('classroom_quizzes', 'save', data={'classroom': room.name, 'title': '[TEST] Rollback quiz',
                'questions': [{'prompt': 'Two plus two?', 'options': ['1','2','3','4'], 'answer': 3}]})
            assert draft
            plan = call('classroom_handover', 'institute_plan')
            assert set(plan) == {'institute', 'plan', 'state', 'features'}
            print('PASS: teaching-only quiz creation; own profile projection; read-only institute plan.')
            denied(lambda: call('teaching', 'leave_class', classroom=room.name))
            requested = call('teaching', 'leave_class', classroom=room.name, reason='[TEST] Rollback-only handover')
            assert call('teaching', 'leave_class', classroom=room.name, reason='[TEST] duplicate')['name'] == requested['name']
            assert frappe.db.get_value('IL Classroom', room.name, 'teacher_assignment_active') == 1
            denied(lambda: call('classroom_handover', 'review', name=requested['name'], decision='Rejected'))
            print('PASS: leave request retains assignment; duplicate request protection; teacher cannot approve.')
            if temporary_admin:
                frappe.db.set_value('User', admin, 'enabled', 1, update_modified=False)
                print('TEST FIXTURE: named demo admin enabled only within this rollback transaction; no credentials changed.')
            login(admin)
            assert any(r.name == requested['name'] for r in call('classroom_handover', 'listing'))
            call('classroom_handover', 'review', name=requested['name'], decision='Rejected')
            assert frappe.db.get_value('IL Classroom', room.name, 'teacher') == original
            login(email)
            requested = call('teaching', 'leave_class', classroom=room.name, reason='[TEST] Replacement handover')
            login(admin)
            denied(lambda: call('classroom_handover', 'review', name=requested['name'], decision='Approved'))
            denied(lambda: call('classroom_handover', 'review', name=requested['name'], decision='Approved', replacement=original))
            # Rollback-only local teacher with an already-existing test User; no credentials or messages.
            replacement_user = 'sisu.student.test+teacher@gmail.com'
            import hashlib
            relation = frappe.get_doc(dict(doctype='IL Profile Relationship', profile=room.public_provider,
                user=replacement_user, kind='Teacher membership', status='Active',
                relationship_key=hashlib.sha256(f'{replacement_user}:{room.public_provider}:Teacher membership'.encode()).hexdigest()))
            existing = frappe.db.get_value('IL Profile Relationship', {'relationship_key': relation.relationship_key}, 'name')
            if existing: relation = frappe.get_doc('IL Profile Relationship', existing)
            relation.status = 'Active'; relation.flags.community_service = True; relation.save(ignore_permissions=True)
            replacement = frappe.db.get_value('IL Member', {'institute': inst, 'user': replacement_user}, 'name')
            if not replacement:
                member = frappe.get_doc(dict(doctype='IL Member', institute=inst, user=replacement_user,
                    role='Teacher', active=1, full_name='[TEST] Rollback replacement'))
                with authorized_insert(member): member.insert(ignore_permissions=True)
                replacement = member.name
            else:
                member = frappe.get_doc('IL Member', replacement)
                assert member.role == 'Teacher' and member.active
            call('classroom_handover', 'review', name=requested['name'], decision='Approved', replacement=replacement)
            assert frappe.db.get_value('IL Classroom', room.name, 'teacher') == replacement
            denied(lambda: call('classroom_handover', 'review', name=requested['name'], decision='Approved', replacement=replacement))
            login(email)
            denied(lambda: api.classroom_for(room.name, write=True))
            assert frappe.db.exists('IL Profile Relationship', {'profile': room.public_provider, 'user': email,
                'kind': 'Teacher membership', 'status': 'Active'})
            login(replacement_user)
            assert api.classroom_for(room.name, write=True)[2].teacher == replacement
            print('PASS: request retains access; duplicate protection; admin rejection; replacement required; approval transfers access and preserves institute membership.')
    finally:
        frappe.db.rollback(); frappe.destroy()
        print('ROLLED BACK: no quiz, handover, assignment, membership, user activation or message changes retained. Browser acceptance remains pending.')


if __name__ == '__main__': main()
